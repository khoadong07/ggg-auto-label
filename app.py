"""
Kompa Auto Mapping — Golden Gate
Hệ thống tự động xử lý Social Listening cho dự án Golden Gate Group
"""

import os
import sys
import time
import uuid
import threading
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st
from typing import Optional

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GGG Auto Mapping",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent
UPLOAD_DIR  = Path(tempfile.gettempdir()) / "ggg_uploads"
OUTPUT_DIR  = Path(tempfile.gettempdir()) / "ggg_outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(PROJECT_DIR))

# ── Module-level job store ────────────────────────────────────────────────────
if not hasattr(st, "_ggg_jobs"):
    st._ggg_jobs = {}
JOBS: dict = st._ggg_jobs

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background-color: #F5F7FA; }

.k-header {
    background: #FFFFFF; border-radius: 14px; padding: 22px 28px;
    margin-bottom: 24px; display: flex; align-items: center; gap: 16px;
    border: 1px solid #E2E8F0; box-shadow: 0 2px 12px rgba(200,50,0,0.07);
}
.k-header-icon {
    width: 48px; height: 48px;
    background: linear-gradient(135deg, #C83200 0%, #FF6B35 100%);
    border-radius: 12px; display: flex; align-items: center;
    justify-content: center; font-size: 24px; flex-shrink: 0;
}
.k-header-title { font-size: 22px; font-weight: 800; color: #C83200; letter-spacing: -0.5px; }
.k-header-sub   { font-size: 13px; color: #64748B; margin-top: 3px; }
.k-header-badge {
    margin-left: auto; background: #FFF4F0; color: #C83200;
    border: 1px solid #FFCCB8; border-radius: 20px;
    padding: 5px 14px; font-size: 12px; font-weight: 600; white-space: nowrap;
}

.k-section {
    font-size: 13px; font-weight: 700; color: #64748B;
    text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 12px;
}

.k-panel {
    background: #FFFFFF; border: 1px solid #E2E8F0;
    border-radius: 12px; padding: 20px 22px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04);
}

/* Demo badge */
.demo-yes { background:#F0FDF4; color:#16A34A; border:1px solid #86EFAC; border-radius:6px; padding:3px 10px; font-size:12px; font-weight:600; }
.demo-no  { background:#FFF7ED; color:#EA580C; border:1px solid #FED7AA; border-radius:6px; padding:3px 10px; font-size:12px; font-weight:600; }

/* Job rows */
.k-job { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:14px 18px 10px; margin-bottom:10px; }
.k-job:hover { box-shadow: 0 3px 12px rgba(0,0,0,0.07); }
.k-job-running { border-left: 4px solid #C83200; }
.k-job-done    { border-left: 4px solid #16A34A; }
.k-job-error   { border-left: 4px solid #DC2626; }
.k-job-stopped { border-left: 4px solid #F59E0B; }
.k-job-queued  { border-left: 4px solid #CBD5E1; }

.k-prog-wrap { background:#F1F5F9; border-radius:6px; height:8px; margin:8px 0 5px; overflow:hidden; }
.k-prog-bar  { height:100%; border-radius:6px; transition:width 0.5s ease; }

.k-stat { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:14px 16px; text-align:center; }
.k-stat-num { font-size:28px; font-weight:800; color:#C83200; line-height:1; }
.k-stat-lbl { font-size:12px; color:#94A3B8; margin-top:4px; font-weight:500; }

.k-empty { background:#FFFFFF; border:2px dashed #CBD5E1; border-radius:14px; text-align:center; padding:60px 20px; color:#94A3B8; }
.k-empty-icon { font-size:40px; margin-bottom:12px; }
.k-empty-text { font-size:15px; font-weight:500; }
.k-empty-hint { font-size:13px; margin-top:6px; color:#CBD5E1; }

.k-footer { text-align:center; color:#CBD5E1; font-size:12px; margin-top:36px; padding-top:18px; border-top:1px solid #E2E8F0; }

#MainMenu, footer, .stDeployButton { display:none !important; }
div[data-testid="stFileUploaderDropzone"] {
    background: #FFFAF8 !important; border: 2px dashed #FFCCB8 !important; border-radius: 10px !important;
}
div[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #C83200 !important; background: #FFF4F0 !important;
}
.stButton > button { border-radius: 8px !important; font-weight: 600 !important; }
.stDownloadButton > button {
    border-radius: 8px !important; font-weight: 600 !important;
    background: #F0FDF4 !important; border: 1px solid #86EFAC !important; color: #16A34A !important;
}
.stDownloadButton > button:hover { background: #DCFCE7 !important; border-color: #4ADE80 !important; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Background job runner
# ═══════════════════════════════════════════════════════════════════════════════
def _run_job(job_id: str, buzz_path: str, demo_path: Optional[str], output_path: str):
    JOBS[job_id].update(status="running", progress=1, stage="Đang khởi tạo...")

    def cb(pct: int, stage: str = ""):
        if JOBS[job_id].get("stop_requested"):
            raise InterruptedError("Đã dừng bởi người dùng")
        JOBS[job_id]["progress"] = min(pct, 99)
        if stage:
            JOBS[job_id]["stage"] = stage

    try:
        from ggg_pipeline import run_pipeline
        stats = run_pipeline(
            buzz_path=buzz_path,
            output_path=output_path,
            demo_path=demo_path,
            progress_callback=cb,
        )
        JOBS[job_id].update(
            status="done",
            progress=100,
            stage="Hoàn thành!",
            output_path=output_path,
            finished_at=datetime.now().strftime("%H:%M:%S"),
            stats=stats,
        )
    except InterruptedError:
        JOBS[job_id].update(
            status="stopped",
            stage="Đã dừng bởi người dùng",
            finished_at=datetime.now().strftime("%H:%M:%S"),
        )
    except Exception as exc:
        import traceback
        JOBS[job_id].update(
            status="error",
            stage="Lỗi xử lý",
            error=traceback.format_exc(),
            finished_at=datetime.now().strftime("%H:%M:%S"),
        )


def submit_job(buzz_file, demo_file: Optional[object] = None) -> str:
    job_id      = str(uuid.uuid4())[:8].upper()
    buzz_path   = str(UPLOAD_DIR / f"{job_id}_{buzz_file.name}")
    output_path = str(OUTPUT_DIR / f"{job_id}_output_{buzz_file.name}")
    demo_path   = None

    with open(buzz_path, "wb") as f:
        f.write(buzz_file.getbuffer())

    if demo_file is not None:
        demo_path = str(UPLOAD_DIR / f"{job_id}_demo_{demo_file.name}")
        with open(demo_path, "wb") as f:
            f.write(demo_file.getbuffer())

    JOBS[job_id] = {
        "id":             job_id,
        "filename":       buzz_file.name,
        "demo_filename":  demo_file.name if demo_file else None,
        "has_demo":       demo_file is not None,
        "status":         "queued",
        "progress":       0,
        "stage":          "Đang chờ...",
        "stop_requested": False,
        "output_path":    None,
        "error":          None,
        "stats":          None,
        "created_at":     datetime.now().strftime("%H:%M:%S"),
        "finished_at":    None,
    }

    threading.Thread(
        target=_run_job,
        args=(job_id, buzz_path, demo_path, output_path),
        daemon=True,
    ).start()
    return job_id


# ═══════════════════════════════════════════════════════════════════════════════
# Header
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="k-header">
    <div class="k-header-icon">🍽️</div>
    <div>
        <div class="k-header-title">GGG Auto Mapping</div>
        <div class="k-header-sub">Hệ thống tự động xử lý Social Listening — Golden Gate Group</div>
    </div>
    <div class="k-header-badge">⚡ Powered by Kompa AI</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# Upload section
# ═══════════════════════════════════════════════════════════════════════════════
col_buzz, col_demo, col_action = st.columns([3, 3, 2], gap="medium")

with col_buzz:
    st.markdown('<div class="k-section">📁 File Buzz Data <span style="color:#C83200">*</span></div>', unsafe_allow_html=True)
    buzz_file = st.file_uploader(
        label="buzz",
        type=["xlsx"],
        accept_multiple_files=False,
        label_visibility="collapsed",
        key="buzz_uploader",
    )
    if buzz_file:
        st.markdown(
            f'<div style="background:#FFF4F0;border:1px solid #FFCCB8;border-radius:8px;'
            f'padding:8px 14px;font-size:13px;color:#C83200;font-weight:500;margin-top:6px;">'
            f'✓ &nbsp;<b>{buzz_file.name}</b> &nbsp;·&nbsp; {buzz_file.size/1024:.1f} KB</div>',
            unsafe_allow_html=True,
        )
    else:
        st.caption("File raw buzz data (.xlsx) — bắt buộc")

with col_demo:
    st.markdown('<div class="k-section">👥 File Demographic <span style="color:#94A3B8">(tùy chọn)</span></div>', unsafe_allow_html=True)
    demo_file = st.file_uploader(
        label="demo",
        type=["xlsx"],
        accept_multiple_files=False,
        label_visibility="collapsed",
        key="demo_uploader",
    )
    if demo_file:
        st.markdown(
            f'<div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;'
            f'padding:8px 14px;font-size:13px;color:#16A34A;font-weight:500;margin-top:6px;">'
            f'✓ &nbsp;<b>{demo_file.name}</b> &nbsp;·&nbsp; {demo_file.size/1024:.1f} KB</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;'
            'padding:8px 14px;font-size:13px;color:#92400E;margin-top:6px;">'
            '⚠️ Không có demographic — vẫn xử lý, gán tag <b>No Demographic</b></div>',
            unsafe_allow_html=True,
        )

with col_action:
    st.markdown('<div class="k-section">🚀 Thực thi</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if st.button(
        "🚀  Bắt đầu xử lý",
        disabled=(buzz_file is None),
        use_container_width=True,
        type="primary",
    ):
        jid = submit_job(buzz_file, demo_file)
        st.session_state["last_jid"] = jid
        st.rerun()

    if buzz_file is None:
        st.caption("⬆️ Upload file buzz data trước")
    else:
        mode = "với Demographic" if demo_file else "không có Demographic"
        st.caption(f"Sẵn sàng chạy {mode}")

# ═══════════════════════════════════════════════════════════════════════════════
# Job list
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
st.markdown('<div class="k-section">📊 Danh sách tác vụ</div>', unsafe_allow_html=True)

STATUS_CFG = {
    "running": ("⏳", "Đang chạy",  "#C83200", "k-job-running"),
    "done":    ("✅", "Hoàn thành", "#16A34A", "k-job-done"),
    "error":   ("❌", "Lỗi",        "#DC2626", "k-job-error"),
    "stopped": ("⏹",  "Đã dừng",   "#F59E0B", "k-job-stopped"),
    "queued":  ("🕐", "Chờ xử lý", "#94A3B8", "k-job-queued"),
}
PROG_COLOR = {
    "running": "#C83200", "done": "#16A34A",
    "error": "#DC2626", "stopped": "#F59E0B", "queued": "#CBD5E1",
}

if not JOBS:
    st.markdown(
        '<div class="k-empty">'
        '<div class="k-empty-icon">📭</div>'
        '<div class="k-empty-text">Chưa có tác vụ nào</div>'
        '<div class="k-empty-hint">Upload file buzz và bấm <b>Bắt đầu xử lý</b></div>'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    has_running = False

    for job_id, job in reversed(list(JOBS.items())):
        status   = job["status"]
        progress = job["progress"]
        stage    = job["stage"]

        s_icon, s_label, s_color, _ = STATUS_CFG.get(status, ("❓", status, "#94A3B8", ""))
        prog_color = PROG_COLOR.get(status, "#CBD5E1")
        fill_pct   = progress if status != "error" else 100

        col_info, col_status, col_pct, col_action = st.columns([5, 1.5, 1, 1.8], gap="small")

        with col_info:
            demo_badge = (
                '<span class="demo-yes">👥 Có Demographic</span>'
                if job["has_demo"] else
                '<span class="demo-no">🚫 No Demographic</span>'
            )
            stats_html = ""
            if status == "done" and job.get("stats"):
                s = job["stats"]
                stats_html = (
                    f'<span style="font-size:11px;color:#94A3B8;margin-left:8px;">'
                    f'{s["total_rows"]:,} rows &nbsp;·&nbsp; '
                    f'Labels: {s["labels_filled"]:,}'
                    + (f' &nbsp;·&nbsp; Demo matched: {s["demo_matched"]:,}' if s["has_demo"] else "")
                    + '</span>'
                )
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;padding-top:8px;flex-wrap:wrap;">'
                f'<span style="font-weight:600;font-size:14px;color:#1E293B;max-width:220px;'
                f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{job["filename"]}">'
                f'{job["filename"]}</span>'
                f'{demo_badge}'
                f'<span style="color:#CBD5E1;font-size:11px;">#{job_id}</span>'
                f'{stats_html}'
                f'</div>',
                unsafe_allow_html=True,
            )

        with col_status:
            st.markdown(
                f'<div style="text-align:center;padding-top:8px;font-size:13px;'
                f'font-weight:700;color:{s_color};">{s_icon}&nbsp;{s_label}</div>',
                unsafe_allow_html=True,
            )

        with col_pct:
            st.markdown(
                f'<div style="text-align:center;padding-top:4px;font-size:20px;'
                f'font-weight:800;color:{s_color};">{progress}%</div>',
                unsafe_allow_html=True,
            )

        with col_action:
            if status == "done" and job.get("output_path") and os.path.exists(job["output_path"]):
                with open(job["output_path"], "rb") as fout:
                    st.download_button(
                        label="⬇️ Tải về",
                        data=fout.read(),
                        file_name=f"GGG_output_{job['filename']}",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dl_{job_id}",
                        use_container_width=True,
                    )
            elif status in ("running", "queued"):
                if st.button("⏹  Dừng", key=f"stop_{job_id}", use_container_width=True):
                    JOBS[job_id]["stop_requested"] = True
                    JOBS[job_id]["stage"] = "Đang dừng..."
                    st.rerun()

        # Progress bar
        st.markdown(
            f'<div class="k-prog-wrap">'
            f'<div class="k-prog-bar" style="width:{fill_pct}%;background:{prog_color};"></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Stage + timestamp
        t_info = f"Tạo lúc {job['created_at']}"
        if job.get("finished_at"):
            t_info += f"  ·  Xong lúc {job['finished_at']}"
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
            f'<span style="font-size:12px;color:#64748B;">{stage}</span>'
            f'<span style="font-size:11px;color:#CBD5E1;">{t_info}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if status == "error" and job.get("error"):
            with st.expander("Xem chi tiết lỗi", expanded=False):
                st.code(job["error"], language=None)

        st.markdown('<div style="height:1px;background:#F1F5F9;margin:6px 0 10px;"></div>', unsafe_allow_html=True)

        if status == "running":
            has_running = True

    if has_running:
        time.sleep(1)
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# Stats + Clear
# ═══════════════════════════════════════════════════════════════════════════════
if JOBS:
    total_n   = len(JOBS)
    run_n     = sum(1 for j in JOBS.values() if j["status"] == "running")
    done_n    = sum(1 for j in JOBS.values() if j["status"] == "done")
    stopped_n = sum(1 for j in JOBS.values() if j["status"] == "stopped")
    err_n     = sum(1 for j in JOBS.values() if j["status"] == "error")
    demo_n    = sum(1 for j in JOBS.values() if j["has_demo"])

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    for col, num, label, color in [
        (c1, total_n,   "Tổng cộng",     "#C83200"),
        (c2, run_n,     "Đang chạy",     "#C83200"),
        (c3, done_n,    "Hoàn thành",    "#16A34A"),
        (c4, stopped_n, "Đã dừng",       "#F59E0B"),
        (c5, err_n,     "Lỗi",           "#DC2626"),
        (c6, demo_n,    "Có Demographic","#0EA5E9"),
    ]:
        with col:
            st.markdown(
                f'<div class="k-stat">'
                f'<div class="k-stat-num" style="color:{color}">{num}</div>'
                f'<div class="k-stat-lbl">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    clearable = [jid for jid, j in JOBS.items() if j["status"] in ("done", "error", "stopped")]
    if clearable:
        if st.button(f"🗑️  Xoá {len(clearable)} tác vụ đã kết thúc", type="secondary"):
            for jid in clearable:
                del JOBS[jid]
            st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="k-footer">'
    'Phát triển bởi <strong style="color:#C83200">Kompa</strong>'
    ' &nbsp;·&nbsp; GGG Auto Mapping — Golden Gate Group'
    '</div>',
    unsafe_allow_html=True,
)
