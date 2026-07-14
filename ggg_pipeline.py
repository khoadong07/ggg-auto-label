"""
ggg_pipeline.py — GGG pipeline module
Được gọi từ app.py (Streamlit UI)
"""

import re
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd
from typing import Optional

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
MODEL_NAME   = "Khoa/kompa-ggg-032026"
BATCH_SIZE   = 16
MAX_LENGTH   = 128
CURRENT_YEAR = datetime.now().year

OUTPUT_COLS = [
    "Id", "TopicId", "Topic", "Brand Code", "Title", "Content", "Description",
    "UrlComment", "PublishedDate", "Sentiment", "SiteName", "SiteId", "Channel",
    "POE", "Author", "AuthorId", "UrlTopic", "ParentId",
    "Labels1", "Labels2", "Labels3", "Labels4",
    "feed_back", "Type", "Gender", "Birthday", "năm sinh", "X", "TUỔI",
    "HomeTown", "Phone", "Area", "Province",
]

TOPIC_BRAND = {
    "Ashima":                       "AS",
    "Blue Bay":                     "VX",
    "Chixmax":                      "CK",
    "Chả Cá Vạn Vạn":              "CV",
    "Cloud Pot":                    "CD",
    "Crystal Jade Kitchen":         "CJ",
    "Dao Niu Guo":                  "DN",
    "Daruma":                       "DR",
    "Gogi House":                   "GG",
    "Golden Gate Restaurant Group": "GGG",
    "Hàng Cuốn 37":                "HC",
    "Isushi":                       "SS",
    "K-pub":                        "KP",
    "Kichi Kichi":                  "KK",
    "Lách Ca Lách Cách":            "LC",
    "Man Tang Guo":                 "MT",
    "Manwah":                       "MW",
    "Phở Inn":                      "IP",
    "SUSHIX":                       "SX",
    "Shogun Janpanese street BBQ":  "SG",
    "Sumo Yakiniku":                "SM",
    "The Coffee House":             "TCH",
    "The Golden Spoon":             "TSG",
    "Union Pizza":                  "UP",
    "Universal tea":                "UT",
    "Vuvuzela":                     "VV",
    "WOW! Yakiniku":                "WY",
    "Woo Master":                   "WM",
    "Yu Tang":                      "YT",
}

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
_ID_FB_PAT = re.compile(r'^(\d+)_')
_YEAR_PAT  = re.compile(r'\b(19\d{2}|20\d{2})\b')



def _fix_channel(row):
    url = row.get("UrlTopic", "")
    if pd.notna(url) and not str(url).startswith("http"):
        return str(url)
    return row.get("Channel", "")


def _extract_author_id(buzz_id):
    if not buzz_id or pd.isna(buzz_id): return ""
    m = _ID_FB_PAT.match(str(buzz_id))
    return m.group(1) if m else ""


def _preprocess_text(text):
    if not text or pd.isna(text): return ""
    from underthesea import word_tokenize
    text = unicodedata.normalize("NFC", str(text))
    text = re.sub(r"\s+", " ", text).strip()
    return word_tokenize(text, format="text")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
def run_pipeline(
    buzz_path: str,
    output_path: str,
    demo_path: Optional[str] = None,
    progress_callback=None,
):
    """
    buzz_path  : đường dẫn file raw buzz (.xlsx)
    output_path: đường dẫn file output (.xlsx)
    demo_path  : đường dẫn file demographic đã xử lý (.xlsx), None = skip
    progress_callback(pct, stage): callback cập nhật tiến trình
    """

    def cb(pct: int, stage: str = ""):
        if progress_callback:
            progress_callback(pct, stage)

    # ── Step 1: Transform buzz ────────────────────────────────────────────────
    cb(5, "Đọc file buzz data...")
    df = pd.read_excel(buzz_path)
    total_rows = len(df)

    cb(10, f"Transform {total_rows:,} rows...")
    df["Brand Code"] = df["Topic"].map(TOPIC_BRAND).fillna("")
    df["PublishedDate"] = pd.to_datetime(df["PublishedDate"], format="mixed", dayfirst=True, errors="coerce")
    df["POE"]           = df["SharedMedia"].fillna("Earned") if "SharedMedia" in df.columns else "Earned"
    df["Channel"]       = df.apply(_fix_channel, axis=1)
    # Chỉ tạo AuthorId nếu raw file chưa có — tránh ghi đè User ID gốc
    if "AuthorId" not in df.columns:
        df["AuthorId"] = df["Id"].apply(_extract_author_id)

    # ── Pre-filter: Keyword-based labels (before AI model) ───────────────────
    cb(14, "Pre-filter: kiểm tra từ khoá...")
    _filter_cols = [c for c in ["Title", "Content", "Description"] if c in df.columns]
    _text_lower = df[_filter_cols].fillna("").agg(" ".join, axis=1).str.lower()

    _GIA_KEYWORDS = [
        "tăng giá", "lên giá", "ngáo giá", "ảo giá", "bảng giá",
        "giá buffet", "giá niêm yết", "giá cao", "giá đắt", "giá rẻ",
        "giá vé", "giá tăng", "giá vậy", "giá này", "mức giá",
        "phân khúc giá", "túi tiền", "chi phí", "niêm yết",
        "vat", "đắt", "mắc",
    ]
    _gia_mask = _text_lower.str.contains("|".join(re.escape(k) for k in _GIA_KEYWORDS), regex=True)

    _WIFI_KEYWORDS = [
        "wifi", "wi-fi",
        "mạng chậm", "mạng yếu", "mạng kém", "mạng tệ",
        "không vào được mạng", "không vào nổi mạng",
        "kết nối không ổn định", "kết nối wifi", "bắt wifi",
        "chập chờn", "internet chậm", "internet yếu",
    ]
    _wifi_mask = _text_lower.str.contains("|".join(re.escape(k) for k in _WIFI_KEYWORDS), regex=True)
    _wifi_mask = _wifi_mask & ~_gia_mask

    _MAYLANH_KEYWORDS = [
        "máy lạnh", "điều hòa", "điều hoà", "máy điều hòa", "máy điều hoà",
    ]
    _maylanh_mask = _text_lower.str.contains("|".join(re.escape(k) for k in _MAYLANH_KEYWORDS), regex=True)
    _maylanh_mask = _maylanh_mask & ~_gia_mask & ~_wifi_mask

    for i in range(1, 5):
        df[f"Labels{i}"] = ""
    df.loc[_gia_mask, "Labels1"] = "6. Giá & Chính sách"
    df.loc[_gia_mask, "Labels2"] = "6.1 Giá"
    df.loc[_wifi_mask, "Labels1"] = "4. Vận hành chung"
    df.loc[_wifi_mask, "Labels2"] = "4.12 Wifi"
    df.loc[_wifi_mask, "Labels3"] = "Khả năng truy cập"
    df.loc[_maylanh_mask, "Labels1"] = "3. Cơ sở vật chất"
    df.loc[_maylanh_mask, "Labels2"] = "3.2 Hình ảnh không gian (bài trí, trang trí, nhiệt độ, ánh sáng, nhà vệ sinh...)"
    df.loc[_maylanh_mask, "Labels3"] = "Máy lạnh"

    _prefilter_mask = _gia_mask | _wifi_mask | _maylanh_mask

    # ── Step 2: Predict labels ────────────────────────────────────────────────
    cb(15, "Tải model AI...")
    import torch
    from tqdm import tqdm
    from transformers import AutoTokenizer, AutoModelForSequenceClassification

    device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model     = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.to(device)
    model.eval()

    text_cols = [c for c in ["Title", "Content", "Description"] if c in df.columns]

    def _merge(row):
        seen, out = set(), []
        for col in text_cols:
            t = str(row[col]).strip() if pd.notna(row[col]) else ""
            if t and t not in seen:
                seen.add(t); out.append(t)
        return " ".join(out)

    ai_df = df[~_prefilter_mask].copy()
    ai_count = len(ai_df)

    cb(20, f"Tiền xử lý văn bản ({ai_count:,} records cần AI)...")
    ai_df["_text"] = ai_df.apply(_merge, axis=1).apply(_preprocess_text)

    texts     = ai_df["_text"].tolist()
    all_preds = []
    n_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE

    cb(25, f"Dự đoán nhãn ({ai_count:,} records)...")
    for i, start in enumerate(range(0, len(texts), BATCH_SIZE)):
        batch  = texts[start : start + BATCH_SIZE]
        inputs = tokenizer(batch, return_tensors="pt", truncation=True,
                           padding=True, max_length=MAX_LENGTH).to(device)
        with torch.no_grad():
            probs = torch.softmax(model(**inputs).logits, dim=-1)
        for pid in torch.argmax(probs, dim=-1):
            all_preds.append(model.config.id2label[int(pid)])

        pct = 25 + int(60 * (i + 1) / max(n_batches, 1))
        cb(pct, f"Dự đoán nhãn... ({min(start+BATCH_SIZE, len(texts)):,}/{len(texts):,})")

    hierarchies = [[l.strip() for l in p.split("->")] for p in all_preds]
    for i in range(4):
        ai_df[f"Labels{i+1}"] = [h[i] if i < len(h) else "" for h in hierarchies]
    ai_df.drop(columns=["_text"], inplace=True, errors="ignore")

    for col in [f"Labels{i+1}" for i in range(4)]:
        df.loc[~_prefilter_mask, col] = ai_df[col].values

    # ── Step 3: Join demographic ──────────────────────────────────────────────
    has_demo = demo_path is not None and Path(demo_path).exists()

    if has_demo:
        cb(87, "Join demographic...")
        demo = pd.read_excel(demo_path, sheet_name=0)
        demo["UserId"] = demo["UserId"].astype(str).str.strip()
        if "Gender_norm" in demo.columns:
            demo["Gender"] = demo["Gender_norm"]

        # Derive năm sinh / TUỔI từ Birthday nếu chưa có
        if "năm sinh" not in demo.columns and "Birthday" in demo.columns:
            demo["năm sinh"] = demo["Birthday"].apply(
                lambda v: (m.group(1) if (m := _YEAR_PAT.search(str(v))) else "")
                          if pd.notna(v) else ""
            )
        if "TUỔI" not in demo.columns and "năm sinh" in demo.columns:
            demo["TUỔI"] = demo["năm sinh"].apply(
                lambda y: str(CURRENT_YEAR - int(y)) if pd.notna(y) and str(y).isdigit() else ""
            )

        # Derive Province / Area từ Location nếu chưa có
        if ("Province" not in demo.columns or "Area" not in demo.columns) and "Location" in demo.columns:
            _loc_split = demo["Location"].apply(
                lambda v: [p.strip() for p in str(v).split(",")] if pd.notna(v) else []
            )
            if "Province" not in demo.columns:
                demo["Province"] = _loc_split.apply(lambda p: p[0] if p else "")
            if "Area" not in demo.columns:
                demo["Area"] = _loc_split.apply(lambda p: p[1] if len(p) > 1 else "")

        wanted_cols = ["Name", "Gender", "Birthday", "năm sinh", "TUỔI", "X",
                       "HomeTown", "Phone", "Province", "Area"]
        demo_cols = [c for c in wanted_cols if c in demo.columns]
        LOOKUP = (
            demo.set_index("UserId")[demo_cols]
                .fillna("")
                .to_dict(orient="index")
        )

        orig_author = df["Author"].copy() if "Author" in df.columns else None

        for field in demo_cols:
            col = "Author" if field == "Name" else field
            df[col] = df["AuthorId"].apply(lambda x: LOOKUP.get(str(x), {}).get(field, ""))

        # Nếu demo không match được, giữ lại Author gốc từ raw file
        if orig_author is not None:
            df["Author"] = df["Author"].where(df["Author"].ne(""), orig_author)

        # Đảm bảo các cột thiếu vẫn tồn tại trong output
        for field in wanted_cols:
            col = "Author" if field == "Name" else field
            if col not in df.columns:
                df[col] = ""
    else:
        cb(87, "Bỏ qua demographic (không có file)...")
        for col in ["Gender", "Birthday", "năm sinh", "TUỔI", "X",
                    "HomeTown", "Phone", "Province", "Area"]:
            if col not in df.columns:
                df[col] = ""
        if "Author" not in df.columns:
            df["Author"] = ""

    # ── Step 4: Export ────────────────────────────────────────────────────────
    cb(94, "Xuất file kết quả...")
    for col in OUTPUT_COLS:
        if col not in df.columns:
            df[col] = ""

    df[OUTPUT_COLS].to_excel(output_path, index=False, sheet_name="Data")
    import openpyxl as _xl
    _wb = _xl.load_workbook(output_path)
    _ws = _wb["Data"]
    _headers = [c.value for c in _ws[1]]
    if "PublishedDate" in _headers:
        _cidx = _headers.index("PublishedDate") + 1
        for _row in _ws.iter_rows(min_row=2, min_col=_cidx, max_col=_cidx):
            for _cell in _row:
                if _cell.value is not None:
                    _cell.number_format = "DD/MM/YYYY"
    _wb.save(output_path)
    cb(100, "Hoàn thành!")

    return {
        "total_rows":     total_rows,
        "has_demo":       has_demo,
        "demo_matched":   int(df["Author"].ne("").sum()) if has_demo else 0,
        "labels_filled":  int(df["Labels1"].ne("").sum()),
        "gia_prefiltered":  int(_gia_mask.sum()),
        "wifi_prefiltered":    int(_wifi_mask.sum()),
        "maylanh_prefiltered": int(_maylanh_mask.sum()),
    }
