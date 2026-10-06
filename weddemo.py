import streamlit as st
import requests
import time
from datetime import datetime

# ============================================================
#  CẤU HÌNH TRANG
# ============================================================
st.set_page_config(
    page_title="Nhà Của Phước • Smart Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
#  BLYNK CLOUD
# ============================================================
BLYNK_AUTH_TOKEN = "o_YezTbra89IcjZShEngnLv047q_gLwt"
BLYNK_SERVER = "https://blynk.cloud/external/api"
HTTP_TIMEOUT = 3

DEVICES = [
    {"id": "den",     "name": "Đèn Nhỏ",      "vpin": "V1", "pin": "GPIO 27", "icon": "💡", "category": "Chiếu sáng",       "watt": 15, "color": "#fbbf24"},
    {"id": "quat",    "name": "Quạt Phòng",   "vpin": "V2", "pin": "GPIO 26", "icon": "💨", "category": "Làm mát",          "watt": 45, "color": "#38bdf8"},
    {"id": "tong",    "name": "Cầu Dao Tổng", "vpin": "V3", "pin": "GPIO 25", "icon": "⚡", "category": "Nguồn chính",       "watt": 0,  "color": "#f472b6"},
    {"id": "den_lon", "name": "Đèn Lớn",      "vpin": "V4", "pin": "GPIO 33", "icon": "🔆", "category": "Chiếu sáng chính", "watt": 60, "color": "#a78bfa"},
]

# ============================================================
#  HÀM GỌI BLYNK
# ============================================================
def blynk_set(pin: str, value: int) -> bool:
    """Gửi lệnh điều khiển tới Blynk."""
    url = f"{BLYNK_SERVER}/update?token={BLYNK_AUTH_TOKEN}&{pin}={int(bool(value))}"
    try:
        r = requests.get(url, timeout=HTTP_TIMEOUT)
        return r.status_code == 200 and r.text.strip() in ("", "OK", "0", "1")
    except requests.RequestException:
        return False


def blynk_get(pin: str):
    """Đọc giá trị hiện tại từ Blynk. None nếu lỗi."""
    url = f"{BLYNK_SERVER}/get?token={BLYNK_AUTH_TOKEN}&{pin}"
    try:
        r = requests.get(url, timeout=HTTP_TIMEOUT)
        if r.status_code == 200:
            return int(r.text.strip())
    except (requests.RequestException, ValueError):
        pass
    return None


def blynk_ping() -> bool:
    """Kiểm tra kết nối Blynk Cloud."""
    try:
        r = requests.get(
            f"{BLYNK_SERVER}/isHardwareConnected?token={BLYNK_AUTH_TOKEN}",
            timeout=HTTP_TIMEOUT,
        )
        return r.status_code == 200
    except requests.RequestException:
        return False


# ============================================================
#  SESSION STATE KHỞI TẠO
# ============================================================
for dev in DEVICES:
    st.session_state.setdefault(dev["id"], False)

st.session_state.setdefault("log", [])
st.session_state.setdefault("last_sync", 0.0)
st.session_state.setdefault("last_sync_ok", False)
st.session_state.setdefault("entered", False)


def push_log(msg: str, level: str = "info"):
    """Ghi nhật ký, giữ tối đa 20 dòng."""
    icon = {"info": "🔵", "ok": "🟢", "warn": "🟡", "err": "🔴"}.get(level, "•")
    st.session_state.log.insert(0, f"{icon} `{datetime.now().strftime('%H:%M:%S')}` — {msg}")
    st.session_state.log = st.session_state.log[:20]


# ============================================================
#  ĐÈN CHIẾU SÁNG WEB — overlay theo trạng thái đèn thật
# ============================================================
def render_room_light():
    """Vẽ overlay ánh sáng lên web dựa trên trạng thái 2 đèn."""
    small_on = st.session_state.get("den", False)      # Đèn Nhỏ → nửa trái
    big_on   = st.session_state.get("den_lon", False)  # Đèn Lớn → nửa phải

    overlays = []

    # Nửa trái — ánh vàng ấm (Đèn Nhỏ)
    if small_on:
        overlays.append("""
        <div class="light-overlay" style="
            left: 0; width: 55%;
            background: radial-gradient(ellipse at 0% 50%,
                        rgba(251, 191, 36, 0.28) 0%,
                        rgba(251, 191, 36, 0.10) 45%,
                        transparent 80%);
        "></div>
        """)

    # Nửa phải — ánh trắng tím (Đèn Lớn)
    if big_on:
        overlays.append("""
        <div class="light-overlay" style="
            right: 0; width: 65%;
            background: radial-gradient(ellipse at 100% 50%,
                        rgba(216, 220, 255, 0.30) 0%,
                        rgba(167, 139, 250, 0.12) 45%,
                        transparent 80%);
        "></div>
        """)

    # Khi cả 2 đèn cùng bật → thêm lớp sáng đều toàn trang
    if small_on and big_on:
        overlays.append("""
        <div class="light-overlay" style="
            left: 0; width: 100%;
            background: linear-gradient(90deg,
                        rgba(251, 191, 36, 0.10) 0%,
                        rgba(255, 255, 255, 0.08) 50%,
                        rgba(167, 139, 250, 0.10) 100%);
        "></div>
        """)

    # Badge báo trạng thái phòng
    if small_on and big_on:
        status = '<div class="room-status bright">✨ PHÒNG SÁNG RỰC</div>'
    elif small_on or big_on:
        status = '<div class="room-status half">💡 PHÒNG SÁNG MỘT NỬA</div>'
    else:
        status = '<div class="room-status dim">🌑 PHÒNG ĐANG TỐI</div>'

    st.markdown("".join(overlays) + status, unsafe_allow_html=True)


# ============================================================
#  CSS NÂNG CAO — Glassmorphism + Light Overlay + Welcome Screen
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
}

/* ==== Nền chính ==== */
.stApp {
    background:
        radial-gradient(circle at 15% 10%, #1a1f36 0%, transparent 45%),
        radial-gradient(circle at 85% 90%, #161028 0%, transparent 50%),
        linear-gradient(135deg, #0a0c14 0%, #0d1018 100%);
    background-attachment: fixed;
    color: #e2e8f0;
    transition: filter 0.6s ease;
}

#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

/* ==== Card glass ==== */
.card-glass {
    background: linear-gradient(145deg, rgba(30, 36, 58, 0.75), rgba(20, 24, 40, 0.65));
    backdrop-filter: blur(16px) saturate(160%);
    -webkit-backdrop-filter: blur(16px) saturate(160%);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 16px;
    box-shadow: 0 10px 30px -12px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.05);
    transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease;
    animation: fadeUp .5s ease both;
}
.card-glass:hover {
    transform: translateY(-3px);
    border-color: rgba(56, 189, 248, 0.35);
    box-shadow: 0 18px 40px -15px rgba(56,189,248,0.25), inset 0 1px 0 rgba(255,255,255,0.06);
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ==== Badge trạng thái ==== */
.badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 12px; border-radius: 999px;
    font-size: 11px; font-weight: 700; letter-spacing: .4px;
    text-transform: uppercase;
}
.badge-on {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(52, 211, 153, 0.35);
    box-shadow: 0 0 12px rgba(52, 211, 153, 0.25);
}
.badge-on::before {
    content: ""; width: 7px; height: 7px; border-radius: 50%;
    background: #34d399; box-shadow: 0 0 8px #34d399;
    animation: pulse 1.5s ease-in-out infinite;
}
.badge-off {
    background: rgba(100, 116, 139, 0.12);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.2);
}
.badge-off::before {
    content: ""; width: 7px; height: 7px; border-radius: 50%;
    background: #64748b;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%      { opacity: .55; transform: scale(1.25); }
}

/* ==== Metric ==== */
.metric-label {
    font-size: 12px; font-weight: 600; letter-spacing: .8px;
    color: #94a3b8; text-transform: uppercase;
}
.metric-value {
    font-size: 30px; font-weight: 800; line-height: 1.1; margin: 6px 0 4px;
    background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 60%, #f472b6 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.metric-sub { font-size: 12px; color: #64748b; }

/* ==== Icon thiết bị ==== */
.dev-icon {
    font-size: 34px; line-height: 1;
    filter: drop-shadow(0 4px 12px rgba(0,0,0,0.4));
    transition: transform .3s ease;
}
.dev-icon.on {
    filter: drop-shadow(0 0 12px currentColor);
    animation: floaty 2.8s ease-in-out infinite;
}
@keyframes floaty {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(-4px); }
}

/* ==== Nút bấm chung ==== */
.stButton > button {
    border-radius: 12px !important;
    font-weight: 700 !important;
    letter-spacing: .3px;
    padding: 10px 14px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    transition: all .2s ease !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 8px 20px -6px rgba(99, 102, 241, 0.6) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 24px -8px rgba(99, 102, 241, 0.85) !important;
}
.stButton > button[kind="secondary"] {
    background: rgba(30, 41, 59, 0.7) !important;
    color: #cbd5e1 !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(51, 65, 85, 0.85) !important;
    border-color: rgba(239, 68, 68, 0.45) !important;
    color: #fca5a5 !important;
}

/* ==== Sidebar ==== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0e1120 0%, #0a0c16 100%);
    border-right: 1px solid rgba(255,255,255,0.05);
}
section[data-testid="stSidebar"] * { color: #cbd5e1; }

/* ==== Log panel ==== */
.log-panel {
    background: rgba(10, 13, 24, 0.6);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 14px 16px;
    font-size: 13px; line-height: 1.9;
    max-height: 260px; overflow-y: auto;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
}

/* ==== Scrollbar ==== */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(100,116,139,0.4); border-radius: 8px; }
::-webkit-scrollbar-thumb:hover { background: rgba(100,116,139,0.7); }

/* ==== Divider ==== */
.hr-gradient {
    height: 1px; border: 0; margin: 24px 0;
    background: linear-gradient(90deg, transparent, rgba(99,102,241,0.5), transparent);
}

/* ==== LIGHT OVERLAY ==== */
.light-overlay {
    position: fixed;
    top: 0;
    height: 100vh;
    pointer-events: none;
    z-index: 9999;
    mix-blend-mode: screen;
    transition: opacity 0.8s ease, transform 0.8s ease;
    animation: lightFadeIn 0.8s ease both;
}
@keyframes lightFadeIn {
    from { opacity: 0; transform: scale(0.95); }
    to   { opacity: 1; transform: scale(1); }
}
.light-overlay::after {
    content: "";
    position: absolute;
    inset: 0;
    background: inherit;
    filter: blur(40px);
    opacity: 0.6;
}

.room-status {
    position: fixed;
    top: 14px;
    left: 50%;
    transform: translateX(-50%);
    padding: 6px 16px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: .5px;
    z-index: 10000;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.12);
    animation: fadeUp .4s ease both;
    pointer-events: none;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.room-status.dim    { background: rgba(30,41,59,0.75); color: #64748b; }
.room-status.half   { background: rgba(251,191,36,0.15); color: #fbbf24; border-color: rgba(251,191,36,0.35); }
.room-status.bright { background: rgba(255,255,255,0.15); color: #fff; border-color: rgba(255,255,255,0.35); box-shadow: 0 0 25px rgba(255,255,255,0.25); }

/* ==== WELCOME SCREEN ==== */
.welcome-wrap {
    text-align: center;
    padding-top: 20px;
    animation: fadeUp 0.8s ease both;
}
.welcome-title {
    font-size: 42px;
    font-weight: 800;
    letter-spacing: 2px;
    background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 8px;
    animation: fadeUp 0.9s ease both;
}
.welcome-sub {
    font-size: 13px;
    color: #64748b;
    letter-spacing: 6px;
    margin-bottom: 30px;
    animation: fadeUp 1s ease both;
}
.welcome-hint {
    text-align: center;
    font-size: 14px;
    color: #94a3b8;
    letter-spacing: 1px;
    margin-top: 24px;
    animation: hintBlink 2s ease-in-out infinite;
}
@keyframes hintBlink {
    0%, 100% { opacity: 1; }
    50%      { opacity: .35; }
}

/* Nút ngôi nhà — phát sáng, nhịp thở */
.st-key-enter_house button {
    font-size: 140px !important;
    line-height: 1 !important;
    height: 260px !important;
    width: 260px !important;
    margin: 0 auto !important;
    display: block !important;
    border-radius: 50% !important;
    background:
        radial-gradient(circle at 50% 40%,
            rgba(99, 102, 241, 0.35) 0%,
            rgba(139, 92, 246, 0.20) 40%,
            rgba(30, 41, 59, 0.60) 100%) !important;
    border: 2px solid rgba(139, 92, 246, 0.55) !important;
    box-shadow:
        0 0 60px rgba(99, 102, 241, 0.55),
        0 0 120px rgba(139, 92, 246, 0.35),
        inset 0 0 60px rgba(99, 102, 241, 0.25) !important;
    animation: housePulse 2.4s ease-in-out infinite !important;
    transition: transform 0.3s ease, box-shadow 0.3s ease !important;
    padding: 0 !important;
    color: #fff !important;
}
.st-key-enter_house button:hover {
    transform: scale(1.08) !important;
    box-shadow:
        0 0 90px rgba(99, 102, 241, 0.85),
        0 0 180px rgba(139, 92, 246, 0.55),
        inset 0 0 80px rgba(99, 102, 241, 0.4) !important;
    border-color: rgba(167, 139, 250, 0.9) !important;
}
@keyframes housePulse {
    0%, 100% {
        box-shadow:
            0 0 60px rgba(99, 102, 241, 0.55),
            0 0 120px rgba(139, 92, 246, 0.35),
            inset 0 0 60px rgba(99, 102, 241, 0.25);
        transform: translateY(0);
    }
    50% {
        box-shadow:
            0 0 90px rgba(99, 102, 241, 0.9),
            0 0 180px rgba(139, 92, 246, 0.6),
            inset 0 0 80px rgba(99, 102, 241, 0.4);
        transform: translateY(-8px);
    }
}

/* Vòng hào quang xoay quanh nhà */
.house-halo {
    position: fixed;
    top: 45%; left: 50%;
    width: 420px; height: 420px;
    margin: -210px 0 0 -210px;
    border-radius: 50%;
    background: conic-gradient(from 0deg,
        transparent 0deg,
        rgba(99, 102, 241, 0.35) 90deg,
        transparent 180deg,
        rgba(167, 139, 250, 0.35) 270deg,
        transparent 360deg);
    filter: blur(50px);
    pointer-events: none;
    z-index: 0;
    animation: haloSpin 8s linear infinite;
}
@keyframes haloSpin {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
}
</style>
""", unsafe_allow_html=True)


# ============================================================
#  MÀN HÌNH CHÀO — Ngôi nhà chờ click
# ============================================================
if not st.session_state.get("entered", False):
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .block-container { padding-top: 3rem !important; max-width: 800px !important; }
    </style>
    """, unsafe_allow_html=True)

    # Hào quang xoay quanh ngôi nhà
    st.markdown('<div class="house-halo"></div>', unsafe_allow_html=True)

    # Tiêu đề
    st.markdown("""
    <div class="welcome-wrap">
        <div class="welcome-title">🏡 NHÀ CỦA PHƯỚC</div>
        <div class="welcome-sub">SMART IoT CONTROL</div>
    </div>
    """, unsafe_allow_html=True)

    # Nút ngôi nhà — đặt giữa màn hình
    colA, colB, colC = st.columns([1, 1, 1])
    with colB:
        if st.button("🏠", key="enter_house", use_container_width=True):
            st.session_state.entered = True
            st.rerun()

    # Gợi ý
    st.markdown(
        '<div class="welcome-hint">👆 NHẤN VÀO NGÔI NHÀ ĐỂ BẮT ĐẦU</div>',
        unsafe_allow_html=True
    )

    st.stop()  # Dừng — không render dashboard khi chưa vào nhà


# ============================================================
#  HELPER RENDER
# ============================================================
def render_metric(label: str, value: str, sub: str, sub_color: str = "#64748b"):
    return f"""
    <div class="card-glass">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub" style="color:{sub_color};">{sub}</div>
    </div>
    """


# ============================================================
#  ĐỒNG BỘ TRẠNG THÁI TỪ BLYNK (mỗi 5 giây)
# ============================================================
@st.fragment(run_every=5)
def auto_sync():
    """Đọc trạng thái thật từ Blynk và đồng bộ session_state."""
    changed = False
    for dev in DEVICES:
        val = blynk_get(dev["vpin"])
        if val is not None:
            new_state = bool(val)
            if st.session_state[dev["id"]] != new_state:
                st.session_state[dev["id"]] = new_state
                changed = True
    st.session_state.last_sync = time.time()
    if changed:
        st.rerun()


# ============================================================
#  VẼ HIỆU ỨNG ĐÈN — Overlay ánh sáng lên web
# ============================================================
render_room_light()


# ============================================================
#  SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 6px 0 14px;">
        <div style="font-size: 42px;">⚡</div>
        <div style="font-weight: 800; font-size: 18px; background: linear-gradient(135deg,#60a5fa,#a78bfa); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            NHÀ CỦA PHƯỚC
        </div>
        <div style="font-size: 11px; color: #64748b; letter-spacing: 1.5px; margin-top: 2px;">SMART IoT CONTROL</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 📡 Trạng Thái Gateway")
    online = blynk_ping()
    if online:
        st.success("● ESP32 ONLINE — Blynk Cloud OK")
    else:
        st.error("● OFFLINE — Không kết nối được Blynk")

    if st.session_state.last_sync:
        st.caption(f"Đồng bộ lần cuối: {datetime.fromtimestamp(st.session_state.last_sync).strftime('%H:%M:%S')}")
    else:
        st.caption("Chưa đồng bộ")

    st.markdown('<hr class="hr-gradient">', unsafe_allow_html=True)

    with st.expander("🔐 Cấu hình kết nối", expanded=False):
        st.text_input("Blynk Host", value="blynk.cloud", disabled=True)
        st.text_input("Template", value="TMPL6Aoua1Fjz", disabled=True)
        st.text_input("Auth Token", value=BLYNK_AUTH_TOKEN, type="password", disabled=True)

    st.markdown("#### 🎛️ Điều Khiển Nhanh")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("BẬT TẤT CẢ", use_container_width=True, type="primary"):
            ok = 0
            for dev in DEVICES:
                if blynk_set(dev["vpin"], 1):
                    st.session_state[dev["id"]] = True
                    ok += 1
            push_log(f"Bật tất cả — {ok}/{len(DEVICES)} thành công", "ok" if ok == len(DEVICES) else "warn")
            st.rerun()
    with c2:
        if st.button("TẮT TẤT CẢ", use_container_width=True):
            ok = 0
            for dev in DEVICES:
                if blynk_set(dev["vpin"], 0):
                    st.session_state[dev["id"]] = False
                    ok += 1
            push_log(f"Tắt tất cả — {ok}/{len(DEVICES)} thành công", "ok" if ok == len(DEVICES) else "warn")
            st.rerun()

    st.markdown('<hr class="hr-gradient">', unsafe_allow_html=True)

    if st.button("🏠 Thoát về màn hình chính", use_container_width=True):
        st.session_state.entered = False
        st.rerun()

    st.caption("💡 Relay Active HIGH\n\n🔄 Tự đồng bộ mỗi 5 giây")


# ============================================================
#  HEADER
# ============================================================
active_count = sum(1 for d in DEVICES if st.session_state[d["id"]])
total_watt = sum(d["watt"] for d in DEVICES if st.session_state[d["id"]])

col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("## 🏡 Nhà Của Phước — Control Dashboard")
    st.caption("Bảng điều khiển realtime • Kết nối trực tiếp ESP32 qua Blynk REST API")
with col_h2:
    st.markdown(f"""
    <div style="text-align:right; padding-top:6px;">
        <div style="font-size: 11px; color:#94a3b8; letter-spacing:.8px;">ĐANG HOẠT ĐỘNG</div>
        <div style="font-size: 30px; font-weight: 800; background: linear-gradient(135deg,#38bdf8,#a78bfa); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            {active_count}<span style="font-size:18px; color:#475569;">/{len(DEVICES)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr class="hr-gradient">', unsafe_allow_html=True)


# ============================================================
#  METRIC CARDS
# ============================================================
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(render_metric("⚡ Điện Áp Kích", "3.3 V", "● Active HIGH ổn định", "#34d399"), unsafe_allow_html=True)
with m2:
    st.markdown(render_metric("🔌 Tiếp Điểm Relay", "COM/NO", "● Thường mở — an toàn", "#38bdf8"), unsafe_allow_html=True)
with m3:
    st.markdown(render_metric("📊 Công Suất Ước Tính", f"{total_watt} W", f"● {active_count} thiết bị đang tải", "#a78bfa"), unsafe_allow_html=True)
with m4:
    st.markdown(render_metric("🌐 Kết Nối Blynk", "REST", "● Online" if online else "● Offline", "#34d399" if online else "#f87171"), unsafe_allow_html=True)


# ============================================================
#  BẢNG CÔNG TẮC
# ============================================================
st.markdown("### 🎛️ Bảng Công Tắc Thiết Bị")
cols = st.columns(4, gap="medium")

for idx, dev in enumerate(DEVICES):
    with cols[idx]:
        is_on = st.session_state[dev["id"]]

        badge = '<span class="badge badge-on">BẬT</span>' if is_on else '<span class="badge badge-off">TẮT</span>'

        glow = (
            f"border:1px solid {dev['color']}66;"
            f"box-shadow: 0 0 30px -5px {dev['color']}55, inset 0 1px 0 rgba(255,255,255,0.06);"
        ) if is_on else ""

        st.markdown(f"""
        <div class="card-glass" style="{glow}">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:14px;">
                <span class="dev-icon {'on' if is_on else ''}" style="color:{dev['color']};">{dev['icon']}</span>
                {badge}
            </div>
            <div style="font-size:17px; font-weight:700; color:#f1f5f9;">{dev['name']}</div>
            <div style="font-size:12px; color:#64748b; margin-top:4px;">
                Blynk <b style="color:{dev['color']};">{dev['vpin']}</b> · {dev['pin']}
            </div>
            <div style="font-size:11px; color:#475569; margin-top:2px;">
                {dev['category']} · ~{dev['watt']}W
            </div>
        </div>
        """, unsafe_allow_html=True)

        label = f"⏻  TẮT" if is_on else f"⏻  BẬT"
        btn_type = "secondary" if is_on else "primary"

        if st.button(label, key=f"btn_{dev['id']}", use_container_width=True, type=btn_type):
            target = not is_on
            ok = blynk_set(dev["vpin"], target)
            st.session_state[dev["id"]] = target
            state_txt = "BẬT" if target else "TẮT"

            if ok:
                push_log(f"{dev['name']} → {state_txt}", "ok")
                st.toast(f"✅ {dev['name']}: {state_txt}", icon="⚡")
            else:
                push_log(f"{dev['name']} → {state_txt} (lỗi mạng)", "err")
                st.toast(f"⚠️ Không gửi được lệnh tới {dev['name']}", icon="🚨")

            st.rerun()


# ============================================================
#  NHẬT KÝ + TỔNG QUAN
# ============================================================
st.markdown('<hr class="hr-gradient">', unsafe_allow_html=True)

col_log, col_info = st.columns([2, 1])

with col_log:
    st.markdown("### 📜 Nhật Ký Hoạt Động")
    if st.session_state.log:
        log_html = "<br>".join(st.session_state.log)
        st.markdown(f'<div class="log-panel">{log_html}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="log-panel" style="color:#475569;">Chưa có hoạt động nào...</div>', unsafe_allow_html=True)

with col_info:
    st.markdown("### 📊 Tổng Quan Hệ Thống")
    st.markdown(f"""
    <div class="card-glass">
        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
            <span style="color:#94a3b8; font-size:13px;">Thiết bị hoạt động</span>
            <b style="color:#38bdf8;">{active_count}/{len(DEVICES)}</b>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
            <span style="color:#94a3b8; font-size:13px;">Tổng công suất</span>
            <b style="color:#a78bfa;">{total_watt} W</b>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
            <span style="color:#94a3b8; font-size:13px;">Kết nối Blynk</span>
            <b style="color:{'#34d399' if online else '#f87171'};">{'Online' if online else 'Offline'}</b>
        </div>
        <div style="display:flex; justify-content:space-between;">
            <span style="color:#94a3b8; font-size:13px;">Cập nhật cuối</span>
            <b style="color:#e2e8f0;">{datetime.fromtimestamp(st.session_state.last_sync).strftime('%H:%M:%S') if st.session_state.last_sync else '—'}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr class="hr-gradient">', unsafe_allow_html=True)
st.caption("⚡ Smart Dashboard v4.0 — Streamlit × Blynk Cloud × ESP32 · Made with ❤️ for Nhà Của Phước")


# ============================================================
#  AUTO-SYNC CHẠY CUỐI
# ============================================================
auto_sync()