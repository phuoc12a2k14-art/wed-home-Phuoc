import streamlit as st
import requests
import time
from datetime import datetime, time as dtime

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
#  BLYNK CONFIG
# ============================================================
BLYNK_AUTH_TOKEN = "o_YezTbra89IcjZShEngnLv047q_gLwt"
BLYNK_SERVER = "https://blynk.cloud/external/api"
HTTP_TIMEOUT = 3

DEVICES = [
    {"id": "den",     "name": "Đèn Nhỏ",       "vpin": "V1", "pin": "GPIO 27", "icon": "💡", "category": "Chiếu sáng",       "watt": 15, "color": "#fbbf24"},
    {"id": "quat",    "name": "Quạt Phòng",   "vpin": "V2", "pin": "GPIO 26", "icon": "💨", "category": "Làm mát",          "watt": 45, "color": "#38bdf8"},
    {"id": "tong",    "name": "Cầu Dao Tổng", "vpin": "V3", "pin": "GPIO 25", "icon": "⚡", "category": "Nguồn chính",       "watt": 0,  "color": "#f472b6"},
    {"id": "den_lon", "name": "Đèn Lớn",      "vpin": "V4", "pin": "GPIO 33", "icon": "🔆", "category": "Chiếu sáng chính", "watt": 60, "color": "#a78bfa"},
]

# ============================================================
#  HÀM BLYNK API
# ============================================================
def blynk_set(pin: str, value) -> bool:
    url = f"{BLYNK_SERVER}/update"
    params = {"token": BLYNK_AUTH_TOKEN, pin: str(value)}
    try:
        r = requests.get(url, params=params, timeout=HTTP_TIMEOUT)
        return r.status_code == 200
    except requests.RequestException:
        return False

def blynk_get(pin: str):
    url = f"{BLYNK_SERVER}/get?token={BLYNK_AUTH_TOKEN}&{pin}"
    try:
        r = requests.get(url, timeout=HTTP_TIMEOUT)
        if r.status_code == 200:
            return r.text.strip()
    except requests.RequestException:
        pass
    return None

def blynk_ping() -> bool:
    try:
        r = requests.get(f"{BLYNK_SERVER}/isHardwareConnected?token={BLYNK_AUTH_TOKEN}", timeout=HTTP_TIMEOUT)
        return r.status_code == 200
    except requests.RequestException:
        return False

# ============================================================
#  SESSION STATE
# ============================================================
for dev in DEVICES:
    st.session_state.setdefault(dev["id"], False)

st.session_state.setdefault("log", [])
st.session_state.setdefault("last_sync", 0.0)
st.session_state.setdefault("entered", False)
st.session_state.setdefault("timer_on", dtime(18, 30))
st.session_state.setdefault("timer_off", dtime(23, 0))
st.session_state.setdefault("timer_enable", True)
st.session_state.setdefault("timer_devs", ["den", "quat"])
st.session_state.setdefault("kwh_total", 0.25)
st.session_state.setdefault("synced_flash", False)

def push_log(msg: str, level: str = "info"):
    icon = {"info": "🔵", "ok": "🟢", "warn": "🟡", "err": "🔴"}.get(level, "•")
    st.session_state.log.insert(0, f"{icon} `{datetime.now().strftime('%H:%M:%S')}` — {msg}")
    st.session_state.log = st.session_state.log[:20]

def sync_flash_config():
    if not st.session_state.synced_flash:
        raw_v5 = blynk_get("V5")
        if raw_v5 and ";" in raw_v5:
            try:
                parts = raw_v5.split(";")
                on_p = parts[0].split(":")
                off_p = parts[1].split(":")
                st.session_state.timer_on = dtime(int(on_p[0]), int(on_p[1]))
                st.session_state.timer_off = dtime(int(off_p[0]), int(off_p[1]))
                st.session_state.timer_devs = parts[2].split(",")
                st.session_state.timer_enable = True
                st.session_state.synced_flash = True
            except Exception:
                pass

sync_flash_config()

# ============================================================
#  HIỆU ỨNG ÁNH SÁNG PHÒNG THÔNG MINH
# ============================================================
def render_room_light():
    small_on = st.session_state.get("den", False)
    big_on   = st.session_state.get("den_lon", False)

    overlays = []
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

    if small_on and big_on:
        status = '<div class="room-status bright">✨ PHÒNG SÁNG RỰC</div>'
    elif small_on or big_on:
        status = '<div class="room-status half">💡 PHÒNG SÁNG MỘT NỬA</div>'
    else:
        status = '<div class="room-status dim">🌑 PHÒNG ĐANG TỐI</div>'

    st.markdown("".join(overlays) + status, unsafe_allow_html=True)

# ============================================================
#  CSS NÂNG CAO
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', -apple-system, sans-serif; }
.stApp {
    background: radial-gradient(circle at 15% 10%, #1a1f36 0%, transparent 45%),
                radial-gradient(circle at 85% 90%, #161028 0%, transparent 50%),
                linear-gradient(135deg, #0a0c14 0%, #0d1018 100%);
    background-attachment: fixed; color: #e2e8f0;
}
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

.card-glass {
    background: linear-gradient(145deg, rgba(30, 36, 58, 0.75), rgba(20, 24, 40, 0.65));
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 10px 30px -12px rgba(0,0,0,0.6);
}
.badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.badge-on { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.35); }
.badge-off { background: rgba(100, 116, 139, 0.12); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.2); }
.hr-gradient { height: 1px; border: 0; margin: 20px 0; background: linear-gradient(90deg, transparent, rgba(99,102,241,0.5), transparent); }
.log-panel { background: rgba(10, 13, 24, 0.6); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 14px; font-size: 13px; max-height: 250px; overflow-y: auto; font-family: monospace; }

.light-overlay {
    position: fixed;
    top: 0;
    height: 100vh;
    pointer-events: none;
    z-index: 9999;
    mix-blend-mode: screen;
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
    pointer-events: none;
}
.room-status.dim    { background: rgba(30,41,59,0.75); color: #64748b; }
.room-status.half   { background: rgba(251,191,36,0.15); color: #fbbf24; border-color: rgba(251,191,36,0.35); }
.room-status.bright { background: rgba(255,255,255,0.15); color: #fff; border-color: rgba(255,255,255,0.35); box-shadow: 0 0 25px rgba(255,255,255,0.25); }

.st-key-enter_house button {
    font-size: 120px !important; height: 220px !important; width: 220px !important;
    margin: 0 auto !important; display: block !important; border-radius: 50% !important;
    background: radial-gradient(circle, rgba(99,102,241,0.3) 0%, rgba(30,41,59,0.7) 100%) !important;
    border: 2px solid rgba(139,92,246,0.6) !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
#  MÀN HÌNH CHÀO
# ============================================================
if not st.session_state.get("entered", False):
    st.markdown("<h1 style='text-align:center; margin-top:60px;'>🏡 NHÀ CỦA PHƯỚC</h1><p style='text-align:center; color:#64748b;'>HỆ THỐNG ĐIỀU KHIỂN THÔNG MINH</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("🏠", key="enter_house", use_container_width=True):
            st.session_state.entered = True
            st.rerun()
    st.stop()

# Hiển thị quầng sáng khi vào nhà
render_room_light()

# ============================================================
#  AUTO SYNC TRẠNG THÁI TỪ CLOUD
# ============================================================
@st.fragment(run_every=5)
def auto_sync():
    changed = False
    for dev in DEVICES:
        val = blynk_get(dev["vpin"])
        if val is not None:
            try:
                stt = bool(int(val))
                if st.session_state[dev["id"]] != stt:
                    st.session_state[dev["id"]] = stt
                    changed = True
            except ValueError:
                pass
    st.session_state.last_sync = time.time()
    if changed:
        st.rerun()

# ============================================================
#  SIDEBAR: NGỮ CẢNH THÔNG MINH
# ============================================================
with st.sidebar:
    st.markdown("### ⚡ NHÀ CỦA PHƯỚC")
    online = blynk_ping()
    
    if online:
        st.success("● ESP32 ONLINE")
    else:
        st.error("● ESP32 OFFLINE")

    st.markdown('<hr class="hr-gradient">', unsafe_allow_html=True)

    st.markdown("#### 🎭 Ngữ Cảnh Nhanh (Smart Scenes)")
    if st.button("🌙 Chế độ Đi Ngủ", use_container_width=True):
        blynk_set("V1", 0)
        blynk_set("V4", 0)
        blynk_set("V2", 1)
        st.session_state["den"] = False
        st.session_state["den_lon"] = False
        st.session_state["quat"] = True
        push_log("Kích hoạt cảnh 'Đi Ngủ' (Tắt hết đèn, bật quạt)", "ok")
        st.rerun()

    if st.button("🚪 Chế độ Ra Khỏi Nhà", use_container_width=True):
        for d in DEVICES:
            blynk_set(d["vpin"], 0)
            st.session_state[d["id"]] = False
        push_log("Kích hoạt cảnh 'Ra Khỏi Nhà' (Đã ngắt toàn bộ)", "warn")
        st.rerun()

    if st.button("🛋️ Chế độ Về Nhà", use_container_width=True):
        blynk_set("V1", 1)
        blynk_set("V2", 1)
        blynk_set("V3", 1)
        st.session_state["den"] = True
        st.session_state["quat"] = True
        st.session_state["tong"] = True
        push_log("Kích hoạt cảnh 'Về Nhà' (Bật đèn & quạt)", "ok")
        st.rerun()

    st.markdown('<hr class="hr-gradient">', unsafe_allow_html=True)
    if st.button("🏠 Thoát ra ngoài", use_container_width=True):
        st.session_state.entered = False
        st.rerun()

# ============================================================
#  HEADER & THEO DÕI ĐIỆN NĂNG
# ============================================================
active_count = sum(1 for d in DEVICES if st.session_state[d["id"]])
total_watt = sum(d["watt"] for d in DEVICES if st.session_state[d["id"]])
kwh_cost = int(st.session_state.kwh_total * 2167)

col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("## 🏡 Dashboard Điều Khiển Nhà")
with col_h2:
    st.markdown(f"<h3 style='text-align:right; color:#38bdf8;'>{active_count}/4 Thiết Bị Đang Bật</h3>", unsafe_allow_html=True)

st.markdown('<hr class="hr-gradient">', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"<div class='card-glass'><div>CÔNG SUẤT TỨC THỜI</div><h2>{total_watt} W</h2><small>Đang tải thực tế</small></div>", unsafe_allow_html=True)
with m2:
    st.markdown(f"<div class='card-glass'><div>ĐIỆN NĂNG TIÊU THỤ</div><h2>{st.session_state.kwh_total:.2f} kWh</h2><small>Ước tính tiêu thụ</small></div>", unsafe_allow_html=True)
with m3:
    st.markdown(f"<div class='card-glass'><div>TIỀN ĐIỆN TẠM TÍNH</div><h2>{kwh_cost:,} đ</h2><small>Biểu giá EVN bậc 2</small></div>", unsafe_allow_html=True)
with m4:
    st.markdown(f"<div class='card-glass'><div>KẾT NỐI ESP32</div><h2 style='color:#34d399;'>{'ONLINE' if online else 'OFFLINE'}</h2><small>Blynk Cloud Status</small></div>", unsafe_allow_html=True)

# ============================================================
#  BẢNG ĐIỀU KHIỂN 4 THIẾT BỊ (ĐIỀU KHIỂN TRỰC TIẾP 1 CHẠM)
# ============================================================
st.markdown("### 🎛️ Bảng Công Tắc Thiết Bị")
cols = st.columns(4)

for idx, dev in enumerate(DEVICES):
    with cols[idx]:
        is_on = st.session_state[dev["id"]]
        badge = '<span class="badge badge-on">BẬT</span>' if is_on else '<span class="badge badge-off">TẮT</span>'
        
        st.markdown(f"""
        <div class="card-glass">
            <div style="display:flex; justify-content:space-between;">
                <span style="font-size:32px;">{dev['icon']}</span>
                {badge}
            </div>
            <div style="font-size:18px; font-weight:700; margin-top:8px;">{dev['name']}</div>
            <div style="font-size:12px; color:#64748b;">{dev['pin']} • ~{dev['watt']}W</div>
        </div>
        """, unsafe_allow_html=True)

        label = "⏻ TẮT" if is_on else "⏻ BẬT"
        btn_type = "secondary" if is_on else "primary"
        
        # Bấm trực tiếp 1 chạm cho cả 4 thiết bị (bao gồm Cầu Dao Tổng)
        if st.button(label, key=f"btn_{dev['id']}", use_container_width=True, type=btn_type):
            target = not is_on
            blynk_set(dev["vpin"], int(target))
            st.session_state[dev["id"]] = target
            push_log(f"{dev['name']} → {'BẬT' if target else 'TẮT'}", "ok")
            st.rerun()

# ============================================================
#  HẸN GIỜ BẬT / TẮT & ĐẾM NGƯỢC AUTO-OFF
# ============================================================
st.markdown('<hr class="hr-gradient">', unsafe_allow_html=True)
col_sch, col_down = st.columns([1, 1], gap="medium")

with col_sch:
    st.markdown("### ⏰ Lịch Hẹn Giờ Thông Minh (Lưu Flash NVS)")
    r1, r2, r3 = st.columns([1, 1, 1])
    with r1:
        p_on = st.time_input("🟢 Giờ BẬT:", value=st.session_state.timer_on)
    with r2:
        p_off = st.time_input("🔴 Giờ TẮT:", value=st.session_state.timer_off)
    with r3:
        st.write("")
        st.write("")
        is_en = st.toggle("Bật lịch", value=st.session_state.timer_enable)

    c1, c2, c3, c4 = st.columns(4)
    with c1: c_den = st.checkbox("💡 Đèn Nhỏ", value=("den" in st.session_state.timer_devs))
    with c2: c_quat = st.checkbox("💨 Quạt", value=("quat" in st.session_state.timer_devs))
    with c3: c_tong = st.checkbox("⚡ Tổng", value=("tong" in st.session_state.timer_devs))
    with c4: c_denlon = st.checkbox("🔆 Đèn Lớn", value=("den_lon" in st.session_state.timer_devs))

    if st.button("💾 LƯU LỊCH VÀO ESP32", use_container_width=True, type="primary"):
        st.session_state.timer_on = p_on
        st.session_state.timer_off = p_off
        st.session_state.timer_enable = is_en
        
        sel = []
        if c_den: sel.append("den")
        if c_quat: sel.append("quat")
        if c_tong: sel.append("tong")
        if c_denlon: sel.append("den_lon")
        st.session_state.timer_devs = sel

        val = f"{p_on.strftime('%H:%M')};{p_off.strftime('%H:%M')};{','.join(sel)}" if is_en else "OFF"
        if blynk_set("V5", val):
            push_log(f"Lưu lịch: Bật {p_on.strftime('%H:%M')} ➔ Tắt {p_off.strftime('%H:%M')}", "ok")
            st.toast("✅ Đã lưu cấu hình lịch vào ESP32 Flash", icon="⏰")
        st.rerun()

with col_down:
    st.markdown("### ⏳ Đếm Ngược Tự Tắt (Auto-Off)")
    st.markdown("<small style='color:#94a3b8;'>Tự động ngắt Đèn và Quạt sau số phút đã chọn.</small>", unsafe_allow_html=True)
    mins = st.slider("Chọn số phút tự ngắt:", min_value=5, max_value=120, value=30, step=5)
    
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("▶️ BẮT ĐẦU ĐẾM", use_container_width=True, type="primary"):
            blynk_set("V6", mins)
            push_log(f"Đang đếm ngược tự tắt sau {mins} phút", "ok")
            st.toast(f"⏳ Đã hẹn tự tắt sau {mins} phút", icon="⏱️")
    with c_btn2:
        if st.button("⏹️ HỦY ĐẾM NGƯỢC", use_container_width=True):
            blynk_set("V6", 0)
            push_log("Đã hủy chế độ đếm ngược", "warn")
            st.toast("Đã hủy đếm ngược", icon="⏹️")

# ============================================================
#  NHẬT KÝ HOẠT ĐỘNG
# ============================================================
st.markdown('<hr class="hr-gradient">', unsafe_allow_html=True)
st.markdown("### 📜 Nhật Ký Hoạt Động Hệ Thống")
if st.session_state.log:
    st.markdown(f"<div class='log-panel'>{'<br>'.join(st.session_state.log)}</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='log-panel' style='color:#64748b;'>Chưa có hoạt động nào được ghi nhận...</div>", unsafe_allow_html=True)

auto_sync()