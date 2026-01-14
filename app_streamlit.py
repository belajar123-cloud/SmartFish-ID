import streamlit as st
import requests
from PIL import Image, ImageStat
from io import BytesIO
from datetime import datetime
import json
import os

# PDF
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ----------------------------- DEFAULT CONFIG -----------------------------
DEFAULT_API_BASE = "http://127.0.0.1:8000"

# ----------------------------- FEEDBACK STORAGE (PERMANEN) -----------------------------
FEEDBACK_FILE = "data/feedback_pengguna_smartfishid.json"

st.set_page_config(page_title="SmartFish-ID", page_icon="🐟", layout="wide")

# ----------------------------- PREMIUM UI CSS -----------------------------
st.markdown("""
<style>
/* Hide streamlit defaults */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.stApp{
  background:
    radial-gradient(900px 560px at 10% 12%, rgba(56,189,248,0.25), transparent 55%),
    radial-gradient(850px 520px at 90% 8%, rgba(34,197,94,0.18), transparent 55%),
    radial-gradient(900px 520px at 55% 95%, rgba(168,85,247,0.18), transparent 58%),
    linear-gradient(180deg, rgba(2,6,23,1) 0%, rgba(3,7,18,1) 62%, rgba(2,6,23,1) 100%);
}
.block-container{ max-width: 1300px; padding-top: .8rem; padding-bottom: 2.2rem; }

/* Navbar */
.navbar{
  display:flex; justify-content:space-between; align-items:center;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(15,23,42,0.55);
  border: 1px solid rgba(148,163,184,0.16);
  box-shadow: 0 14px 44px rgba(0,0,0,0.28);
  backdrop-filter: blur(12px);
}
.brand{
  display:flex; align-items:center; gap:10px;
}
.logo{
  width: 34px; height: 34px; border-radius: 12px;
  background: linear-gradient(135deg, rgba(56,189,248,0.9), rgba(34,197,94,0.8));
  box-shadow: 0 10px 30px rgba(0,0,0,0.25);
}
.brand-title{ color:#e5e7eb; font-weight: 900; font-size: 15px; margin:0; }
.brand-sub{ color: rgba(226,232,240,0.7); font-size: 12px; margin:0; }
.nav-pill{
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid rgba(148,163,184,0.18);
  background: rgba(2,6,23,0.25);
  color: rgba(226,232,240,0.85);
  font-weight: 800;
  font-size: 13px;
}

/* Hero */
.hero{
  padding: 22px 22px;
  border-radius: 26px;
  background: linear-gradient(135deg, rgba(56,189,248,0.22), rgba(34,197,94,0.12));
  border: 1px solid rgba(148,163,184,0.18);
  box-shadow: 0 22px 70px rgba(0,0,0,0.36);
  backdrop-filter: blur(12px);
}
.kicker{
  display:inline-block; padding: 6px 10px; border-radius: 999px;
  border: 1px solid rgba(148,163,184,0.24);
  background: rgba(2,6,23,0.35);
  color: #e5e7eb; font-size: 12px; font-weight: 900;
}
.h1{ color:#e5e7eb; font-size: 44px; font-weight: 950; margin: 10px 0 6px 0; line-height:1.05;}
.p{ color: rgba(226,232,240,0.86); font-size: 14px; margin: 0; max-width: 920px; }
.hero-row{ margin-top: 14px; display:flex; gap:10px; flex-wrap:wrap; align-items:center; }

.badge{
  display:inline-block; padding: 7px 11px; border-radius: 999px;
  font-weight: 900; font-size: 12px;
  border: 1px solid rgba(148,163,184,0.25);
  background: rgba(2,6,23,0.35);
  color:#e5e7eb;
}
.ok{ background: rgba(34,197,94,0.18); border-color: rgba(34,197,94,0.35); }
.warn{ background: rgba(245,158,11,0.18); border-color: rgba(245,158,11,0.35); }
.bad{ background: rgba(239,68,68,0.18); border-color: rgba(239,68,68,0.35); }

/* Cards */
.card{
  padding: 16px;
  border-radius: 22px;
  background: rgba(15, 23, 42, 0.58);
  border: 1px solid rgba(148,163,184,0.18);
  box-shadow: 0 16px 50px rgba(0,0,0,0.30);
  backdrop-filter: blur(12px);
}
.title{ color:#e5e7eb; font-size: 16px; font-weight: 950; margin: 0 0 6px 0; }
.muted{ color: rgba(226,232,240,0.74); font-size: 13px; }
.feature{
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(148,163,184,0.16);
  background: rgba(2,6,23,0.22);
}
.feature h4{ margin:0; color:#e5e7eb; font-size: 14px; font-weight: 900;}
.feature p{ margin:6px 0 0 0; color: rgba(226,232,240,0.74); font-size: 12px; }

/* Footer */
.footer{
  margin-top: 16px; padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(148,163,184,0.16);
  background: rgba(15,23,42,0.45);
  color: rgba(226,232,240,0.72);
  font-size: 12px; text-align:center;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------- Helpers -----------------------------
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def api_health(api_base: str):
    try:
        r = requests.get(f"{api_base}/health", timeout=2.0)
        return r.status_code == 200, (r.json() if r.status_code == 200 else None)
    except Exception:
        return False, None

def badge_for(pred: str):
    if pred == "segar":
        return ("✅ SEGER", "ok", "Aman dikonsumsi. Simpan dingin dan olah segera untuk kualitas terbaik.")
    if pred == "kurang_segar":
        return ("⚠️ KURANG SEGAR", "warn", "Sebaiknya segera diolah. Hindari penyimpanan lama.")
    return ("❌ TIDAK LAYAK", "bad", "Jangan dikonsumsi. Risiko keamanan pangan.")

def validate_image_quality(img: Image.Image):
    """Validasi sederhana: resolusi & brightness."""
    w, h = img.size
    if w < 200 or h < 200:
        return False, "Resolusi terlalu kecil. Gunakan foto lebih jelas (min 200x200)."

    gray = img.convert("L")
    mean_brightness = ImageStat.Stat(gray).mean[0]  # 0-255
    if mean_brightness < 40:
        return True, "⚠️ Foto terlihat gelap. Coba tambah cahaya agar hasil lebih akurat."
    return True, ""

def crop_roi(img: Image.Image):
    w, h = img.size
    st.caption(f"Ukuran gambar: {w}×{h} — fokuskan crop pada mata/insang.")
    c1, c2 = st.columns(2)
    with c1:
        left = st.slider("Left", 0, max(0, w-2), 0)
        top = st.slider("Top", 0, max(0, h-2), 0)
    with c2:
        right = st.slider("Right", 1, w, w)
        bottom = st.slider("Bottom", 1, h, h)

    if right <= left + 1:
        right = min(w, left + 2)
    if bottom <= top + 1:
        bottom = min(h, top + 2)

    return img.crop((left, top, right, bottom)), (left, top, right, bottom)

def split_text(text, max_len=78):
    words = text.split()
    lines, line = [], ""
    for w in words:
        if len(line) + len(w) + 1 <= max_len:
            line = (line + " " + w).strip()
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines

def make_pdf(original_img: Image.Image, cropped_img: Image.Image, result: dict):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    pred = result.get("prediction", "-")
    conf = float(result.get("confidence", 0.0))
    headline, _, advice = badge_for(pred)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, H - 50, "SmartFish-ID Report (PKM Demo)")
    c.setFont("Helvetica", 10)
    c.drawString(40, H - 70, f"Timestamp: {result.get('time','-')}")
    c.drawString(40, H - 84, f"Prediction: {pred} | Confidence: {conf:.3f}")
    c.drawString(40, H - 98, f"Source: {result.get('source','-')} | Image: {result.get('image_name','-')}")
    c.drawString(40, H - 112, f"ROI box: {result.get('roi_box','-')}")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, H - 136, "Recommendation")
    c.setFont("Helvetica", 10)
    c.drawString(40, H - 152, headline)

    y = H - 168
    for line in split_text(advice):
        c.drawString(40, y, line)
        y -= 14

    probs = result.get("probabilities", {})
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y - 8, "Probabilities")
    y2 = y - 24
    c.setFont("Helvetica", 10)
    for k, v in probs.items():
        c.drawString(40, y2, f"- {k}: {float(v):.3f}")
        y2 -= 14

    def to_jpeg_bytes(im: Image.Image):
        b = BytesIO()
        im.convert("RGB").save(b, format="JPEG", quality=90)
        b.seek(0)
        return b

    def fit(im: Image.Image, max_w, max_h):
        iw, ih = im.size
        s = min(max_w/iw, max_h/ih)
        return int(iw*s), int(ih*s)

    orig_b = to_jpeg_bytes(original_img)
    crop_b = to_jpeg_bytes(cropped_img)

    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, 320, "Images (Original vs ROI)")
    oy = 110
    ow, oh = fit(original_img, 240, 180)
    cw, ch = fit(cropped_img, 240, 180)

    c.setFont("Helvetica", 10)
    c.drawString(40, 300, "Original")
    c.drawImage(ImageReader(orig_b), 40, oy, width=ow, height=oh, mask='auto')

    c.drawString(320, 300, "ROI (Crop)")
    c.drawImage(ImageReader(crop_b), 320, oy, width=cw, height=ch, mask='auto')

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(40, 30, "SmartFish-ID • Generated for PKM attachment • Proof of Concept")
    c.showPage()
    c.save()

    buf.seek(0)
    return buf

def history_to_csv(history):
    header = ["time","prediction","confidence","source","image_name","roi_box"]
    rows = [",".join(header)]
    for h in history:
        row = [
            str(h.get("time","")),
            str(h.get("prediction","")),
            str(h.get("confidence","")),
            str(h.get("source","")),
            str(h.get("image_name","")),
            str(h.get("roi_box","")),
        ]
        rows.append(",".join(row))
    out = BytesIO()
    out.write("\n".join(rows).encode("utf-8"))
    out.seek(0)
    return out

# ----------------------------- FEEDBACK PERMANEN: LOAD/SAVE JSON -----------------------------
def load_feedbacks():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(FEEDBACK_FILE):
        return []
    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_feedbacks(feedbacks):
    os.makedirs("data", exist_ok=True)
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(feedbacks, f, indent=2, ensure_ascii=False)

# ----------------------------- Sidebar Settings -----------------------------
st.sidebar.markdown("## ⚙️ Settings")
api_base = st.sidebar.text_input("API Base URL", DEFAULT_API_BASE)

mode_system = st.sidebar.selectbox(
    "Mode Sistem",
    ["Real API (Prediksi dari FastAPI)", "Demo Stabil (Tanpa API)"]
)

st.sidebar.caption("Tip: Jika API sering error saat demo, pakai **Demo Stabil**.")

# ----------------------------- Session -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "history" not in st.session_state:
    st.session_state.history = []
if "last" not in st.session_state:
    st.session_state.last = None
if "last_original" not in st.session_state:
    st.session_state.last_original = None
if "last_crop_img" not in st.session_state:
    st.session_state.last_crop_img = None

# ✅ load feedback dari file
if "feedbacks" not in st.session_state:
    st.session_state.feedbacks = load_feedbacks()

# ----------------------------- Navbar -----------------------------
ok, health = api_health(api_base)
status_text = "🟢 API Online" if ok else "🔴 API Offline"
status_cls = "ok" if ok else "bad"

st.markdown(f"""
<div class="navbar">
  <div class="brand">
    <div class="logo"></div>
    <div>
      <p class="brand-title">SmartFish-ID</p>
      <p class="brand-sub">Scan Kesegaran Ikan • ROI • PDF Report</p>
    </div>
  </div>
  <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
    <span class="badge {status_cls}">{status_text}</span>
    <span class="nav-pill">v1 Demo</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.write("")

# ----------------------------- Hero + CTA -----------------------------
st.markdown(f"""
<div class="hero">
  <span class="kicker">PKM READY • AI FOOD SAFETY • INDONESIA</span>
  <div class="h1">Deteksi Kesegaran Ikan<br/>dalam 10 Detik</div>
  <p class="p">
    Upload foto atau gunakan webcam, crop area mata/insang (ROI), lalu dapatkan prediksi + confidence.
    Unduh laporan PDF sebagai lampiran PKM.
  </p>
  <div class="hero-row">
    <span class="badge {status_cls}">{status_text}</span>
    <span class="badge">API: {api_base}</span>
    <span class="badge">Scan • ROI • Report</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.write("")

# ----------------------------- Quick actions -----------------------------
qa1, qa2, qa3 = st.columns(3)

if qa1.button("🔌 Cek API Sekarang", use_container_width=True):
    ok2, data2 = api_health(api_base)
    st.toast("API Online ✅" if ok2 else "API Offline ❌")
    if data2:
        st.sidebar.json(data2)

if qa2.button("🗑️ Clear History", use_container_width=True):
    st.session_state.history = []
    st.session_state.last = None
    st.success("History dibersihkan ✅")
    st.rerun()

if qa3.button("🗑️ Clear Feedback (Hapus File)", use_container_width=True):
    st.session_state.feedbacks = []
    save_feedbacks(st.session_state.feedbacks)
    st.success("Feedback dibersihkan ✅ (file di-reset)")
    st.rerun()

st.write("")

# ----------------------------- Navigation Buttons -----------------------------
c1, c2, c3, c4 = st.columns(4)
if c1.button("🏠 Home", use_container_width=True):
    st.session_state.page = "Home"
if c2.button("📷 Scan Now", use_container_width=True):
    st.session_state.page = "Scan"
if c3.button("📊 Dashboard", use_container_width=True):
    st.session_state.page = "Dashboard"
if c4.button("🗣️ Feedback", use_container_width=True):
    st.session_state.page = "Feedback"

st.write("")

# ----------------------------- Pages -----------------------------
page = st.session_state.page

if page == "Home":
    st.markdown('<div class="card"><div class="title">✨ Kenapa SmartFish-ID Menarik?</div>'
                '<div class="muted">Fokus pada manfaat pengguna + tampilan profesional untuk presentasi PKM.</div></div>',
                unsafe_allow_html=True)
    st.write("")

    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("""
        <div class="feature">
          <h4>⚡ Super Cepat</h4>
          <p>Scan dari foto/webcam, hasil keluar dengan confidence & rekomendasi.</p>
        </div>
        """, unsafe_allow_html=True)
    with f2:
        st.markdown("""
        <div class="feature">
          <h4>🎯 ROI Lebih Ilmiah</h4>
          <p>Crop area mata/insang untuk mengurangi noise dan meningkatkan validitas.</p>
        </div>
        """, unsafe_allow_html=True)
    with f3:
        st.markdown("""
        <div class="feature">
          <h4>📄 PDF + History</h4>
          <p>Unduh laporan & export CSV/JSON untuk bukti PKM.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.info("💡 Tips scan: cahaya terang • fokus mata/insang • foto tidak blur • latar sederhana")

elif page == "Scan":
    left, right = st.columns([1.05, 0.95])

    with left:
        st.markdown('<div class="card"><div class="title">📷 Scan</div>'
                    '<div class="muted">Pilih sumber gambar: Upload atau Webcam. Lalu crop ROI.</div></div>',
                    unsafe_allow_html=True)
        st.write("")

        mode = st.radio("Sumber gambar", ["Upload", "Webcam"], horizontal=True)
        img, name = None, None

        if mode == "Upload":
            up = st.file_uploader("Upload gambar ikan (JPG/PNG)", type=["jpg", "jpeg", "png"])
            if up:
                img = Image.open(BytesIO(up.getvalue())).convert("RGB")
                name = up.name
        else:
            cam = st.camera_input("Ambil foto ikan via webcam")
            if cam:
                img = Image.open(BytesIO(cam.getvalue())).convert("RGB")
                name = f"webcam_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

        if not img:
            st.info("Upload foto atau ambil dari webcam untuk mulai.")
        else:
            ok_img, warn_msg = validate_image_quality(img)
            if not ok_img:
                st.error(warn_msg)
                st.stop()
            if warn_msg:
                st.warning(warn_msg)

            st.markdown('<div class="card"><div class="title">Preview</div>'
                        '<div class="muted">Pastikan foto tidak blur dan cukup cahaya.</div></div>',
                        unsafe_allow_html=True)
            st.image(img, use_container_width=True)

            st.write("")
            st.markdown('<div class="card"><div class="title">🎯 Crop ROI (Mata/Insang)</div>'
                        '<div class="muted">Gunakan slider untuk fokus area penting.</div></div>',
                        unsafe_allow_html=True)

            cropped, box = crop_roi(img)
            st.image(cropped, caption=f"ROI box: {box}", use_container_width=True)

            st.session_state.last_original = img
            st.session_state.last_crop_img = cropped

            st.write("")
            b1, b2, b3 = st.columns(3)
            do_predict = b1.button("🔍 Prediksi", use_container_width=True)
            make_report = b2.button("📄 Buat PDF", use_container_width=True)
            reset = b3.button("🧹 Reset", use_container_width=True)

            if reset:
                st.session_state.last = None
                st.success("Reset selesai.")
                st.rerun()

            if do_predict:
                if mode_system == "Demo Stabil (Tanpa API)":
                    demo = {
                        "prediction": "segar",
                        "confidence": 0.93,
                        "probabilities": {"segar": 0.93, "kurang_segar": 0.05, "tidak_layak": 0.02},
                        "time": now_str(),
                        "source": mode,
                        "image_name": name,
                        "roi_box": box,
                        "mode": "demo"
                    }
                    st.session_state.last = demo
                    st.session_state.history.insert(0, demo)
                    st.success("Prediksi demo berhasil ✅")
                    st.rerun()
                else:
                    if not ok:
                        st.error("API Offline. Jalankan API dulu:\n"
                                 "`uvicorn api.app_api:app --reload --host 127.0.0.1 --port 8000`")
                    else:
                        try:
                            with st.spinner("Mengirim ROI ke API..."):
                                b = BytesIO()
                                cropped.save(b, format="JPEG", quality=95)
                                b.seek(0)
                                files = {"file": (name or "fish.jpg", b.getvalue(), "image/jpeg")}
                                r = requests.post(f"{api_base}/predict", files=files, timeout=30)

                            if r.status_code != 200:
                                st.error(f"Gagal prediksi: {r.status_code} - {r.text}")
                            else:
                                data = r.json()
                                data["time"] = now_str()
                                data["source"] = mode
                                data["image_name"] = name
                                data["roi_box"] = box
                                data["mode"] = "api"
                                st.session_state.last = data
                                st.session_state.history.insert(0, data)
                                st.success("Prediksi berhasil ✅")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error koneksi ke API: {e}")

            if make_report:
                if st.session_state.last is None:
                    st.warning("Lakukan prediksi dulu sebelum membuat PDF.")
                else:
                    try:
                        pdf_buf = make_pdf(st.session_state.last_original, st.session_state.last_crop_img, st.session_state.last)
                        st.download_button(
                            "⬇️ Download PDF Report",
                            data=pdf_buf.getvalue(),
                            file_name=f"SmartFishID_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        st.info("PDF siap diunduh.")
                    except Exception as e:
                        st.error(f"Gagal membuat PDF: {e}")

    with right:
        st.markdown('<div class="card"><div class="title">📊 Result</div>'
                    '<div class="muted">Hasil prediksi + confidence + probabilitas.</div></div>',
                    unsafe_allow_html=True)
        st.write("")

        if st.session_state.last is None:
            st.info("Belum ada hasil. Klik Prediksi setelah crop ROI.")
        else:
            data = st.session_state.last
            pred = data.get("prediction", "-")
            conf = float(data.get("confidence", 0.0))
            probs = data.get("probabilities", {})

            headline, cls, advice = badge_for(pred)

            st.markdown(f"""
            <div class="card">
              <div class="title">Ringkasan</div>
              <span class="badge {cls}">{headline}</span>
              <span class="badge">confidence: {conf:.3f}</span>
              <span class="badge">mode: {data.get('mode','-')}</span>
              <div class="muted" style="margin-top:10px;">{advice}</div>
              <div class="muted" style="margin-top:8px;"><b>Waktu:</b> {data.get('time','-')}</div>
              <div class="muted"><b>ROI:</b> {data.get('roi_box','-')}</div>
            </div>
            """, unsafe_allow_html=True)

            st.write("")
            st.markdown('<div class="card"><div class="title">Probabilitas</div>'
                        '<div class="muted">Grafik bar + progress tiap kelas.</div></div>',
                        unsafe_allow_html=True)

            chart_data = {k: float(v) for k, v in probs.items()}
            st.bar_chart(chart_data)
            for k, v in chart_data.items():
                st.progress(min(max(v, 0.0), 1.0), text=f"{k}: {v:.3f}")

elif page == "Dashboard":
    st.markdown('<div class="card"><div class="title">📊 Dashboard</div>'
                '<div class="muted">Statistik ringkas untuk terlihat “serius” saat demo PKM.</div></div>',
                unsafe_allow_html=True)
    st.write("")

    if not st.session_state.history:
        st.info("Belum ada data. Lakukan Scan dulu.")
    else:
        counts = {"segar": 0, "kurang_segar": 0, "tidak_layak": 0}
        avg_conf = 0.0
        for item in st.session_state.history:
            p = item.get("prediction")
            if p in counts:
                counts[p] += 1
            avg_conf += float(item.get("confidence", 0.0))
        avg_conf = avg_conf / max(1, len(st.session_state.history))

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total scan", len(st.session_state.history))
        k2.metric("Avg confidence", f"{avg_conf:.3f}")
        k3.metric("Segar", counts["segar"])
        k4.metric("Tidak layak", counts["tidak_layak"])

        st.write("")
        st.markdown('<div class="card"><div class="title">Distribusi Prediksi</div></div>', unsafe_allow_html=True)
        st.bar_chart(counts)

        st.write("")
        colx, coly = st.columns(2)
        with colx:
            st.download_button(
                "⬇️ Export History (JSON)",
                data=json.dumps(st.session_state.history, indent=2).encode("utf-8"),
                file_name=f"SmartFishID_History_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        with coly:
            csv_buf = history_to_csv(st.session_state.history)
            st.download_button(
                "⬇️ Export History (CSV)",
                data=csv_buf.getvalue(),
                file_name=f"SmartFishID_History_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

elif page == "Feedback":
    st.markdown('<div class="card"><div class="title">🗣️ Feedback Pengguna</div>'
                '<div class="muted">Fitur ini penting untuk PKM: bukti uji coba dan evaluasi dari pengguna.</div></div>',
                unsafe_allow_html=True)
    st.caption(f"📁 File tersimpan di: {FEEDBACK_FILE}")
    st.write("")

    with st.form("feedback_form", clear_on_submit=True):
        nama = st.text_input("Nama (opsional)")
        peran = st.selectbox("Peran pengguna", ["Konsumen", "Pedagang", "Mahasiswa/Tim", "Lainnya"])
        rating = st.slider("Seberapa membantu aplikasi ini?", 1, 5, 4)
        komentar = st.text_area("Komentar / Saran")
        submit = st.form_submit_button("Kirim Feedback")

    if submit:
        fb = {
            "time": now_str(),
            "nama": nama,
            "peran": peran,
            "rating": rating,
            "komentar": komentar,
            "last_prediction": (st.session_state.last.get("prediction") if st.session_state.last else None),
            "last_confidence": (st.session_state.last.get("confidence") if st.session_state.last else None),
        }
        st.session_state.feedbacks.insert(0, fb)

        # ✅ simpan permanen ke file
        save_feedbacks(st.session_state.feedbacks)

        st.success("Feedback tersimpan ✅ (permanen)")

    st.write("")
    if not st.session_state.feedbacks:
        st.info("Belum ada feedback.")
    else:
        for i, fb in enumerate(st.session_state.feedbacks[:10], start=1):
            st.write(f"{i}. **{fb['time']}** • {fb['peran']} • rating **{fb['rating']}**")
            if fb.get("komentar"):
                st.caption(fb["komentar"])

        st.download_button(
            "⬇️ Download Feedback (JSON)",
            data=json.dumps(st.session_state.feedbacks, indent=2, ensure_ascii=False).encode("utf-8"),
            file_name=f"SmartFishID_Feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

# Footer
st.markdown("""
<div class="footer">
  SmartFish-ID • Premium UI Demo (Streamlit) • Scan • ROI • PDF Report • Dashboard • Feedback (Permanent JSON) • PKM Ready
</div>
""", unsafe_allow_html=True)