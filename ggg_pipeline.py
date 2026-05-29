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


def _format_date(val):
    if not val or pd.isna(val): return val
    s = str(val)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:19], fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return val


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
    df["Brand Code"]    = df["Topic"].map(TOPIC_BRAND).fillna("")
    df["PublishedDate"] = df["PublishedDate"].apply(_format_date)
    df["POE"]           = df["SharedMedia"].fillna("Earned") if "SharedMedia" in df.columns else "Earned"
    df["Channel"]       = df.apply(_fix_channel, axis=1)
    df["AuthorId"]      = df["Id"].apply(_extract_author_id)

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

    cb(20, "Tiền xử lý văn bản...")
    df["_text"] = df.apply(_merge, axis=1).apply(_preprocess_text)

    texts     = df["_text"].tolist()
    all_preds = []
    n_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE

    cb(25, f"Dự đoán nhãn ({total_rows:,} records)...")
    for i, start in enumerate(range(0, len(texts), BATCH_SIZE)):
        batch  = texts[start : start + BATCH_SIZE]
        inputs = tokenizer(batch, return_tensors="pt", truncation=True,
                           padding=True, max_length=MAX_LENGTH).to(device)
        with torch.no_grad():
            probs = torch.softmax(model(**inputs).logits, dim=-1)
        for pid in torch.argmax(probs, dim=-1):
            all_preds.append(model.config.id2label[int(pid)])

        pct = 25 + int(60 * (i + 1) / n_batches)
        cb(pct, f"Dự đoán nhãn... ({min(start+BATCH_SIZE, len(texts)):,}/{len(texts):,})")

    hierarchies = [[l.strip() for l in p.split("->")] for p in all_preds]
    for i in range(4):
        df[f"Labels{i+1}"] = [h[i] if i < len(h) else "" for h in hierarchies]
    df.drop(columns=["_text"], inplace=True, errors="ignore")

    # ── Step 3: Join demographic ──────────────────────────────────────────────
    has_demo = demo_path is not None and Path(demo_path).exists()

    if has_demo:
        cb(87, "Join demographic...")
        demo = pd.read_excel(demo_path, sheet_name=0)
        demo["UserId"] = demo["UserId"].astype(str).str.strip()
        if "Gender_norm" in demo.columns:
            demo["Gender"] = demo["Gender_norm"]

        demo_cols = ["Name", "Gender", "Birthday", "năm sinh", "TUỔI", "X",
                     "HomeTown", "Phone", "Province", "Area"]
        LOOKUP = (
            demo.set_index("UserId")[demo_cols]
                .fillna("")
                .to_dict(orient="index")
        )

        for field in demo_cols:
            col = "Author" if field == "Name" else field
            df[col] = df["AuthorId"].apply(lambda x: LOOKUP.get(str(x), {}).get(field, ""))
    else:
        cb(87, "Bỏ qua demographic (không có file)...")
        for col in ["Author", "Gender", "Birthday", "năm sinh", "TUỔI", "X",
                    "HomeTown", "Phone", "Province", "Area"]:
            df[col] = ""

    # ── Step 4: Export ────────────────────────────────────────────────────────
    cb(94, "Xuất file kết quả...")
    for col in OUTPUT_COLS:
        if col not in df.columns:
            df[col] = ""

    df[OUTPUT_COLS].to_excel(output_path, index=False, sheet_name="Data")
    cb(100, "Hoàn thành!")

    return {
        "total_rows":  total_rows,
        "has_demo":    has_demo,
        "demo_matched": int(df["Author"].ne("").sum()) if has_demo else 0,
        "labels_filled": int(df["Labels1"].ne("").sum()),
    }
