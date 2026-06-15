"""
category_split_pipeline.py — Category Split pipeline module
Tách file buzz data theo Category (dựa trên cột Topic) thành nhiều file Excel,
đóng gói trong 1 file zip. Mỗi file giữ nguyên toàn bộ cột gốc, chỉ lọc theo Topic.
"""

import calendar
import io
import re
import zipfile

import pandas as pd

# ══════════════════════════════════════════════════════════════════════════════
# Category -> danh sách Topic Name
# ══════════════════════════════════════════════════════════════════════════════
CATEGORY_TOPICS = {
    "BBQ": [
        "BBQ Ông Mập", "Galbi House", "Gogi House", "Gyu-kaku", "Gyu-shige",
        "iMeatU", "KingBBQ", "K-pub", "Meat and Meet", "Meat Plus",
        "Moo Beefsteak", "Phổ Đình - Uraetei", "Subin BBQ", "Sumo Yakiniku",
        "Woo Master", "WOW! Yakiniku", "Yakiniku like",
    ],
    "Hotpot": [
        "Ashima", "Chang Kang Kung", "Chao Xian", "Cloud Pot", "Dahú HotPot",
        "Dao Niu Guo", "Dookki", "Haidilao Việt Nam", "Hotpot Story",
        "Kichi Kichi", "Lẩu nấm Gia Khánh", "Long Wang", "Man Tang Guo",
        "Manwah", "Momo Paradise", "Nihaoniu", "ShangChi",
        "Tian Long - Lẩu bò tươi Triều Châu", "Wangheniu", "Wulao",
    ],
    "Japanese": [
        "Daruma", "Genki Sushi Vietnam", "Hadu Sushi", "ikigai sushi", "Isushi",
        "Izakaya Matsuki", "Magnetsu", "Manmaru", "Mikado", "Nama Sushi",
        "Shamoji Robata Yaki", "Shogun Janpanese street BBQ",
        "Sushi Hokkaido Sachi", "Sushi Tei", "SUSHIX", "Tokyo deli",
        "Yen Sushi & Sake Pub",
    ],
    "Western": [
        "Union Pizza", "Pizza 4P's", "Pizza Belga",
    ],
    "Asian": [
        "Bánh Tráng Phú Cường", "Baoz Dimsum", "Bếp Quán", "Big Bowl",
        "Bò tơ Quán Mộc", "Chả cá Hàng Sơn", "Chả Cá Vạn Vạn",
        "Crystal Jade Kitchen", "Ctao", "Dim Tu Tac", "Hàng Cuốn 37",
        "Hoàng Ty", "Lách Ca Lách Cách", "Madame Lam", "Mặn Mòi", "Phở Inn",
        "Phở Lành", "Phở Lý Quốc Sư", "Phở Tâm", "Phở Thìn", "Quán Bụi",
        "San Fu Lou", "Tim Ho Wan", "Vua Chả Cá", "Jin Din Rou",
    ],
    "Drink": [
        "Cheese Coffee", "Gongcha", "Jollibee", "Katinat", "KOI Thé",
        "Phê la", "Texas Chicken", "Universal tea", "Yu Tang",
    ],
    "Beer Club": [
        "Bia Sành điệu", "Hẻm Quán", "Nhậu Tự Do", "Quán Nhỏ", "Vuvuzela",
    ],
    "Fastfood": [
        "Chixmax", "Cecebox", "Jollibee",
    ],
    "SeaFood": [
        "Blue Bay", "Cửu Vân Long", "Poseidon", "D'maris",
    ],
    "Golden Gate Restaurant Group": ["Golden Gate Restaurant Group"],
    "The Golden Spoon": ["The Golden Spoon"],
    "Goldsun Food/Redsun": ["Goldsun Food/Redsun"],
    "The Coffee House": ["The Coffee House"],
}

# Topic Name -> Category (Topic trùng ở nhiều Category sẽ lấy Category khai báo sau cùng)
TOPIC_CATEGORY = {
    topic: category
    for category, topics in CATEGORY_TOPICS.items()
    for topic in topics
}

_INVALID_FS_CHARS = re.compile(r'[\\/:*?"<>|]')


def _safe_filename_part(name: str) -> str:
    return _INVALID_FS_CHARS.sub("-", name).strip()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
def split_by_category(input_path: str, output_zip_path: str, progress_callback=None) -> dict:
    """
    input_path     : đường dẫn file Excel đầu vào (.xlsx), cần có cột "Topic"
    output_zip_path: đường dẫn file zip kết quả
    progress_callback(pct, stage): callback cập nhật tiến trình
    """

    def cb(pct: int, stage: str = ""):
        if progress_callback:
            progress_callback(pct, stage)

    cb(5, "Đọc file dữ liệu...")
    df = pd.read_excel(input_path)
    total_rows = len(df)

    if "Topic" not in df.columns:
        raise ValueError("File không có cột 'Topic'")

    # ── Rename + convert PublishedDate → Date (datetime) ─────────────────────
    if "PublishedDate" in df.columns:
        df = df.rename(columns={"PublishedDate": "Date"})
        df["Date"] = pd.to_datetime(df["Date"], format="mixed", dayfirst=True, errors="coerce")

    # ── Xác định kỳ báo cáo (Month.Year) từ cột Date ─────────────────────────
    cb(15, "Xác định kỳ báo cáo (Month.Year)...")
    periods = pd.Series([], dtype="period[M]")
    date_source = "current_date"
    if "Date" in df.columns:
        periods = df["Date"].dt.to_period("M").dropna()

    if len(periods) > 0:
        target_period = periods.mode().iloc[0]
        date_source = "data"
    else:
        target_period = pd.Timestamp.now().to_period("M")

    month_year_dot     = f"{target_period.month:02d}.{target_period.year}"
    month_year_compact = f"{target_period.month:02d}{target_period.year}"
    month_year_label   = f"{calendar.month_abbr[target_period.month]}.{target_period.year}"

    # ── Map Topic -> Category ─────────────────────────────────────────────────
    cb(25, "Map Topic -> Category...")
    topic_clean      = df["Topic"].astype(str).str.strip()
    category_series  = topic_clean.map(TOPIC_CATEGORY)
    mapped_mask      = category_series.notna()
    unmapped_topics  = sorted(topic_clean[~mapped_mask].unique().tolist())

    # ── Tách theo Category, xuất Excel vào zip ────────────────────────────────
    cb(40, "Tách dữ liệu theo Category...")
    files_generated = []
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        categories = sorted(category_series[mapped_mask].unique())
        n = len(categories)
        for i, category in enumerate(categories):
            sub_df    = df[category_series == category]
            xlsx_name = f"{_safe_filename_part(category)}_Monthly data_{month_year_label} - Data.xlsx"

            xlsx_buf = io.BytesIO()
            with pd.ExcelWriter(xlsx_buf, engine="openpyxl", datetime_format="MM/DD/YYYY") as writer:
                sub_df.to_excel(writer, index=False)
            zf.writestr(xlsx_name, xlsx_buf.getvalue())

            files_generated.append({"name": xlsx_name, "rows": len(sub_df)})
            cb(40 + int(50 * (i + 1) / max(n, 1)), f"Đã tạo {xlsx_name}")

    cb(95, "Đóng gói file zip...")
    with open(output_zip_path, "wb") as f:
        f.write(buf.getvalue())

    cb(100, "Hoàn thành!")

    return {
        "total_rows":          total_rows,
        "mapped_rows":         int(mapped_mask.sum()),
        "unmapped_rows":       int((~mapped_mask).sum()),
        "unmapped_topics":     unmapped_topics,
        "categories_count":    len(files_generated),
        "files":               files_generated,
        "month_year_dot":      month_year_dot,
        "month_year_compact":  month_year_compact,
        "date_source":         date_source,
    }
