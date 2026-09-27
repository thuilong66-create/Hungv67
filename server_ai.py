# ============================================================
#  SERVER AI VIP PRO MAX - DỰ ĐOÁN TÀI XỈU THÔNG MINH
#  Tác giả: Hưng Admin
#  Phiên bản: 3.0 VIP PRO MAX
#  Bao gồm: 12 tín hiệu, 10+ cầu, Markov Chain, Entropy, Anti-Trap
# ============================================================

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, uvicorn, sqlite3, os, random, logging, math
from datetime import datetime, timedelta

# ================= CẤU HÌNH LOG =================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================= KHỞI TẠO APP =================
app = FastAPI(title="AI VIP PRO MAX", version="3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "hethong_vip_learning.db")
INDEX_HTML = os.path.join(BASE_DIR, "index.html")


# ============================================================
# 1. KHỞI TẠO DATABASE
# ============================================================
def khoi_tao_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Bảng người dùng
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        balance INTEGER,
        vip_expire DATETIME,
        is_banned INTEGER
    )''')

    # Bảng nạp thẻ
    c.execute('''CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        card_type TEXT,
        card_amount INTEGER,
        card_pin TEXT,
        card_serial TEXT,
        status TEXT
    )''')

    # Bộ nhớ AI
    c.execute('''CREATE TABLE IF NOT EXISTS ai_memory (
        phien TEXT PRIMARY KEY,
        du_doan TEXT,
        ket_qua TEXT,
        is_win INTEGER,
        pattern_type TEXT,
        confidence REAL,
        created_at DATETIME
    )''')

    # Thống kê độ hiệu quả từng loại cầu
    c.execute('''CREATE TABLE IF NOT EXISTS pattern_stats (
        pattern_type TEXT PRIMARY KEY,
        total INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        last_updated DATETIME
    )''')

    # Tài khoản Admin Vĩnh Viễn
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?, ?)",
              ('hungadmin11', 'hungki98', 999999999999, '2099-12-31 23:59:59', 0))

    conn.commit()
    conn.close()
    logger.info("✅ Khởi tạo database thành công!")


khoi_tao_db()


# ============================================================
# 2. CÁC HÀM PHÂN TÍCH CẦU
# ============================================================
def detect_streak(kq_list):
    """Phát hiện chuỗi bệt"""
    if not kq_list:
        return 0, ""
    last = kq_list[-1]
    streak = 1
    for i in range(len(kq_list) - 2, -1, -1):
        if kq_list[i] == last:
            streak += 1
        else:
            break
    return streak, last


def detect_pattern_11(kq_list, window=6):
    """Cầu 1-1 xen kẽ hoàn hảo"""
    if len(kq_list) < window:
        return False
    recent = kq_list[-window:]
    for i in range(len(recent) - 1):
        if recent[i] == recent[i + 1]:
            return False
    return True


def detect_pattern_22(kq_list):
    """Cầu 2-2"""
    if len(kq_list) < 6:
        return False
    r = kq_list[-6:]
    return r[0] == r[1] and r[2] == r[3] and r[4] == r[5] and r[0] != r[2] and r[2] != r[4]


def detect_pattern_33(kq_list):
    """Cầu 3-3"""
    if len(kq_list) < 6:
        return False
    r = kq_list[-6:]
    return r[0] == r[1] == r[2] and r[3] == r[4] == r[5] and r[0] != r[3]


def detect_pattern_121(kq_list):
    """Cầu 1-2-1"""
    if len(kq_list) < 6:
        return False
    r = kq_list[-6:]
    return r[0] != r[1] and r[1] == r[2] and r[2] != r[3] and r[3] != r[4] and r[4] == r[5]


def detect_pattern_212(kq_list):
    """Cầu 2-1-2"""
    if len(kq_list) < 6:
        return False
    r = kq_list[-6:]
    return r[0] == r[1] and r[1] != r[2] and r[2] != r[3] and r[3] == r[4] and r[4] != r[5]


def detect_pattern_123(kq_list):
    """Cầu 1-2-3"""
    if len(kq_list) < 6:
        return False
    r = kq_list[-6:]
    return r[0] != r[1] and r[1] == r[2] and r[2] != r[3] and r[3] == r[4] and r[4] == r[5]


def detect_pattern_31(kq_list):
    """Cầu 3-1"""
    if len(kq_list) < 8:
        return False
    r = kq_list[-8:]
    return (r[0] == r[1] == r[2] and r[3] != r[2] and
            r[4] != r[3] and r[5] != r[4] and r[6] != r[5] and r[7] != r[6])


def detect_pattern_13(kq_list):
    """Cầu 1-3"""
    if len(kq_list) < 8:
        return False
    r = kq_list[-8:]
    return (r[0] != r[1] and r[1] != r[2] and r[2] != r[3] and
            r[3] == r[4] == r[5] and r[6] != r[5] and r[7] != r[6])


def markov_chain(kq_list, window=20):
    """Markov Chain: Xác suất tiếp tục cùng cửa"""
    if len(kq_list) < 4:
        return 0.5
    if len(kq_list) < window:
        window = len(kq_list)
    recent = kq_list[-window:]

    tt = tx = xt = xx = 0
    for i in range(len(recent) - 1):
        a, b = recent[i], recent[i + 1]
        if a == "Tài" and b == "Tài":
            tt += 1
        elif a == "Tài" and b == "Xỉu":
            tx += 1
        elif a == "Xỉu" and b == "Tài":
            xt += 1
        else:
            xx += 1

    last = recent[-1]
    if last == "Tài":
        total = tt + tx
        return tt / total if total else 0.5
    else:
        total = xt + xx
        return xx / total if total else 0.5


def entropy_score(kq_list):
    """Entropy: đo độ nhiễu (0=chắc chắn, 1=random)"""
    if len(kq_list) < 10:
        return 0.5
    recent = kq_list[-20:]
    p_tai = recent.count("Tài") / len(recent)
    p_xiu = 1 - p_tai
    if p_tai == 0 or p_xiu == 0:
        return 0.0
    return -(p_tai * math.log2(p_tai) + p_xiu * math.log2(p_xiu))


def anti_trap_detect(kq_list):
    """Phát hiện bẫy đảo liên tục"""
    if len(kq_list) < 8:
        return False
    r = kq_list[-8:]
    changes = sum(1 for i in range(len(r) - 1) if r[i] != r[i + 1])
    return changes >= 6


def get_pattern_winrate(pattern_type):
    """Lấy tỉ lệ thắng pattern từ DB"""
    if not pattern_type or pattern_type == "FLEX":
        return None
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT total, wins FROM pattern_stats WHERE pattern_type = ?", (pattern_type,))
    row = c.fetchone()
    conn.close()
    if row and row[0] >= 3:
        return row[1] / row[0]
    return None


# ============================================================
# 3. HỌC MÁY - CHẤM ĐIỂM & CẬP NHẬT KẾT QUẢ
# ============================================================
def cap_nhat_va_hoc_lich_su(lst):
    """Đối chiếu dự đoán cũ với kết quả thực tế để AI tự học"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    for s in lst:
        phien_id = str(s.get("id"))
        actual_kq = "TÀI" if "TAI" in str(s.get("resultTruyenThong", "")).upper() else "XỈU"

        c.execute("SELECT du_doan, is_win, pattern_type FROM ai_memory WHERE phien = ?", (phien_id,))
        row = c.fetchone()

        if row and row[1] is None:
            pred = row[0]
            pattern = row[2]
            win_status = 1 if pred == actual_kq else 0
            c.execute("UPDATE ai_memory SET ket_qua = ?, is_win = ? WHERE phien = ?",
                      (actual_kq, win_status, phien_id))

            # Cập nhật thống kê pattern
            if pattern:
                for p in pattern.split("_"):
                    if p and p != "FLEX":
                        c.execute(
                            "INSERT OR IGNORE INTO pattern_stats (pattern_type, total, wins, last_updated) VALUES (?, 0, 0, ?)",
                            (p, datetime.now()))
                        c.execute(
                            "UPDATE pattern_stats SET total = total + 1, wins = wins + ?, last_updated = ? WHERE pattern_type = ?",
                            (win_status, datetime.now(), p))

    conn.commit()

    # Lấy 30 phiên gần nhất để tính win rate tổng
    c.execute("SELECT is_win, pattern_type FROM ai_memory WHERE is_win IS NOT NULL ORDER BY created_at DESC LIMIT 30")
    history_records = c.fetchall()

    # Lấy 10 phiên gần nhất để hiển thị log
    c.execute("SELECT phien, du_doan, ket_qua, is_win FROM ai_memory WHERE is_win IS NOT NULL ORDER BY created_at DESC LIMIT 10")
    recent_logs = c.fetchall()

    conn.close()

    total = len(history_records)
    wins = sum(1 for r in history_records if r[0] == 1)
    win_rate = (wins / total * 100) if total > 0 else 80.0

    return win_rate, recent_logs, history_records


# ============================================================
# 4. AI VIP PRO - MULTI-SIGNAL DETECTION ENGINE
# ============================================================
def phan_tich_ai_learning(kq_list, next_phien_id, win_rate, history_records):
    """Thuật toán AI chính - 12 tín hiệu + Markov + Entropy"""
    tong_tai = kq_list.count("Tài")
    tong_xiu = kq_list.count("Xỉu")

    # Chưa đủ dữ liệu
    if len(kq_list) < 5:
        du_doan = "TÀI" if random.choice([True, False]) else "XỈU"
        return {
            "du_doan": du_doan, "ti_le": 50.0,
            "loi_khuyen": "🔍 Đang nạp dữ liệu cầu...",
            "trend": "...", "tong_tai": tong_tai, "tong_xiu": tong_xiu,
            "patterns": [], "signal_score": {"TAI": 0, "XIU": 0}, "entropy": 0,
            "ai_stats": {"win_rate": 80.0, "total_learned_sessions": 0, "pattern_winrate": None}
        }

    streak, streak_type = detect_streak(kq_list)
    last = kq_list[-1]
    signal = {"TAI": 0.0, "XIU": 0.0}
    patterns_detected = []
    notes = []

    # ========== [1] BỆT ==========
    if streak >= 3:
        if streak >= 9:
            opp = "XỈU" if streak_type == "Tài" else "TÀI"
            signal[opp] += 3.5
            patterns_detected.append("BE_BET_LONG")
            notes.append(f"🛑 Bệt {streak} tay CỰC DÀI → BẺ {opp}")
        elif streak >= 6:
            opp = "XỈU" if streak_type == "Tài" else "TÀI"
            cont = streak_type.upper()
            signal[opp] += 2.0
            signal[cont] += 1.5
            patterns_detected.append("BE_BET_ALERT")
            notes.append(f"⚠️ Bệt {streak} tay → Nghi bẻ")
        elif streak >= 4:
            cont = streak_type.upper()
            signal[cont] += 2.0
            signal["TÀI" if cont == "XỈU" else "XỈU"] += 1.0
            patterns_detected.append("BE_BET_MED")
            notes.append(f"⚡ Bệt {streak} tay → Theo nhẹ {cont}")
        else:
            cont = streak_type.upper()
            signal[cont] += 2.8
            patterns_detected.append("DU_BET")
            notes.append(f"🔥 Đu bệt {streak} tay → {cont}")

    # ========== [2] CẦU 1-1 ==========
    if detect_pattern_11(kq_list, 6):
        pred = "XỈU" if last == "Tài" else "TÀI"
        signal[pred] += 3.5
        patterns_detected.append("CAU_11")
        notes.append(f"⚡ Cầu 1-1 → {pred}")

    # ========== [3] CẦU 2-2 ==========
    if detect_pattern_22(kq_list):
        pred = "XỈU" if last == "Tài" else "TÀI"
        signal[pred] += 3.0
        patterns_detected.append("CAU_22")
        notes.append(f"⚖️ Cầu 2-2 → {pred}")

    # ========== [4] CẦU 3-3 ==========
    if detect_pattern_33(kq_list):
        pred = "XỈU" if last == "Tài" else "TÀI"
        signal[pred] += 3.2
        patterns_detected.append("CAU_33")
        notes.append(f"🎯 Cầu 3-3 → {pred}")

    # ========== [5] CẦU 1-2-1 ==========
    if detect_pattern_121(kq_list):
        pred = "XỈU" if last == "Tài" else "TÀI"
        signal[pred] += 2.8
        patterns_detected.append("CAU_121")
        notes.append(f"📊 Cầu 1-2-1 → {pred}")

    # ========== [6] CẦU 2-1-2 ==========
    if detect_pattern_212(kq_list):
        pred = "XỈU" if last == "Tài" else "TÀI"
        signal[pred] += 3.0
        patterns_detected.append("CAU_212")
        notes.append(f"📊 Cầu 2-1-2 → {pred}")

    # ========== [7] CẦU 1-2-3 ==========
    if detect_pattern_123(kq_list):
        pred = "XỈU" if last == "Tài" else "TÀI"
        signal[pred] += 2.5
        patterns_detected.append("CAU_123")
        notes.append(f"📊 Cầu 1-2-3 → {pred}")

    # ========== [8] CẦU 3-1 ==========
    if detect_pattern_31(kq_list):
        pred = "XỈU" if last == "Tài" else "TÀI"
        signal[pred] += 2.5
        patterns_detected.append("CAU_31")
        notes.append(f"📊 Cầu 3-1 → {pred}")

    # ========== [9] CẦU 1-3 ==========
    if detect_pattern_13(kq_list):
        pred = "XỈU" if last == "Tài" else "TÀI"
        signal[pred] += 2.5
        patterns_detected.append("CAU_13")
        notes.append(f"📊 Cầu 1-3 → {pred}")

    # ========== [10] MARKOV CHAIN ==========
    p_continue = markov_chain(kq_list, 20)
    if p_continue > 0.62:
        cont = last.upper()
        signal[cont] += (p_continue - 0.5) * 5
        notes.append(f"🔗 Markov: {int(p_continue * 100)}% tiếp {cont}")
    elif p_continue < 0.38:
        opp = "XỈU" if last == "Tài" else "TÀI"
        signal[opp] += (0.5 - p_continue) * 5
        notes.append(f"🔗 Markov: {int((1 - p_continue) * 100)}% đảo {opp}")

    # ========== [11] HỒI QUY ĐỘNG ==========
    recent_20 = kq_list[-20:] if len(kq_list) >= 20 else kq_list
    t_cnt = recent_20.count("Tài")
    x_cnt = recent_20.count("Xỉu")
    diff = t_cnt - x_cnt
    if diff >= 6:
        signal["XỈU"] += min(diff * 0.35, 3.0)
        notes.append(f"📉 Lệch Tài +{diff} → Đảo")
    elif diff <= -6:
        signal["TÀI"] += min(abs(diff) * 0.35, 3.0)
        notes.append(f"📈 Lệch Xỉu +{abs(diff)} → Đảo")

    # ========== [12] ANTI-TRAP ==========
    if anti_trap_detect(kq_list):
        opp = "XỈU" if last == "Tài" else "TÀI"
        signal[opp] += 2.2
        patterns_detected.append("ANTI_TRAP")
        notes.append("🚨 Phát hiện bẫy đảo → Đi ngược")

    # ========== TỔNG HỢP TÍN HIỆU ==========
    total_signal = signal["TAI"] + signal["XIU"]
    if signal["TAI"] > signal["XIU"]:
        du_doan = "TÀI"
        raw_conf = (signal["TAI"] / total_signal * 100) if total_signal > 0 else 50
    elif signal["XIU"] > signal["TAI"]:
        du_doan = "XỈU"
        raw_conf = (signal["XIU"] / total_signal * 100) if total_signal > 0 else 50
    else:
        du_doan = "TÀI" if random.choice([True, False]) else "XỈU"
        raw_conf = 50.0

    pattern_type = "_".join(patterns_detected[:2]) if patterns_detected else "FLEX"

    # ========== HỌC MÁY - ĐIỀU CHỈNH THEO PATTERN ==========
    first_pattern = pattern_type.split("_")[0] if pattern_type != "FLEX" and "_" in pattern_type else pattern_type
    pattern_wr_db = get_pattern_winrate(first_pattern)
    if pattern_wr_db is not None:
        if pattern_wr_db < 0.40:
            du_doan = "XỈU" if du_doan == "TÀI" else "TÀI"
            raw_conf = min(raw_conf + 12, 96)
            notes.append(f"🧠 Đảo chiều (cầu yếu {int(pattern_wr_db * 100)}%)")
        elif pattern_wr_db > 0.70:
            raw_conf = min(raw_conf + 8, 96)
            notes.append(f"✨ Cầu mạnh {int(pattern_wr_db * 100)}%")

    # ========== ENTROPY FILTER ==========
    ent = entropy_score(kq_list)
    if ent > 0.95:
        raw_conf = min(raw_conf, 76.0)
        notes.append("🌊 Nhiễu cao → Hạ tin")
    elif ent < 0.5:
        raw_conf = min(raw_conf + 5, 97)
        notes.append("🎯 Xu hướng rõ → Tăng tin")

    # ========== BIÊN ĐỘ DAO ĐỘNG TỰ NHIÊN ==========
    adjusted_percentage = min(max(raw_conf + random.uniform(-1.5, 2.5), 65.0), 98.9)

    # ========== LƯU VÀO BỘ NHỚ ==========
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO ai_memory (phien, du_doan, pattern_type, confidence, created_at) VALUES (?, ?, ?, ?, ?)",
        (next_phien_id, du_doan, pattern_type, adjusted_percentage, datetime.now()))
    conn.commit()
    conn.close()

    # ========== RADAR & LỜI KHUYÊN ==========
    radar = "".join(["🔴" if x == "Tài" else "🔵" for x in kq_list[-15:]])
    loi_khuyen = " | ".join(notes[:3]) if notes else f"🎲 Phân tích {len(patterns_detected)} tín hiệu"

    return {
        "du_doan": du_doan,
        "ti_le": round(adjusted_percentage, 1),
        "loi_khuyen": loi_khuyen,
        "trend": radar,
        "tong_tai": tong_tai,
        "tong_xiu": tong_xiu,
        "patterns": patterns_detected,
        "signal_score": {"TAI": round(signal["TAI"], 2), "XIU": round(signal["XIU"], 2)},
        "entropy": round(ent, 3),
        "ai_stats": {
            "win_rate": round(win_rate, 1),
            "total_learned_sessions": len(history_records),
            "pattern_winrate": round(pattern_wr_db * 100, 1) if pattern_wr_db is not None else None
        }
    }


# ============================================================
# 5. API SCAN GAME
# ============================================================
@app.get("/api/scan")
async def scan_game(tool: str, username: str, mode: str = "auto"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT vip_expire, is_banned FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()

    if not row:
        return {"status": "error", "msg": "Tài khoản không tồn tại!"}
    if row[1] == 1:
        return {"status": "error", "msg": "Tài khoản bị khóa!"}
    if datetime.now() > datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S"):
        return {"status": "error", "msg": "Gói VIP hết hạn! Vui lòng nạp thêm."}

    url = ("https://wtx.tele68.com/v1/tx/lite-sessions"
           if tool == "lc79"
           else "https://wtx.macminim6.online/v1/tx/lite-sessions")

    try:
        res = requests.get(url, headers={"User-Agent": "Chrome/120.0"}, timeout=5).json()
        if not res.get("list"):
            return {"status": "error", "msg": "Đang kết nối Server Game..."}

        lst = res["list"][::-1]
        kq = ["Tài" if "TAI" in str(s.get("resultTruyenThong", "")).upper() else "Xỉu" for s in lst]

        # AI học máy & chấm điểm
        win_rate, recent_logs, history_records = cap_nhat_va_hoc_lich_su(lst)

        # AI dự đoán phiên tiếp theo
        next_phien_id = str(int(lst[-1]["id"]) + 1)
        data = phan_tich_ai_learning(kq, next_phien_id, win_rate, history_records)
        # Điều chỉnh theo chế độ frontend gửi lên
        if mode == "random":
            data["du_doan"] = random.choice(["TÀI", "XỈU"])
            data["ti_le"] = 50.0
        elif mode == "ai_pro":
            data["ti_le"] = min(data["ti_le"] + 5, 98.9)
        data["phien"] = next_phien_id
        data["logs"] = recent_logs

        return {"status": "success", "data": data}

    except Exception as e:
        logger.error(f"Lỗi API scan: {e}")
        return {"status": "error", "msg": "Bảo trì máy chủ Game!"}


# ============================================================
# 6. API THỐNG KÊ PATTERN
# ============================================================
@app.get("/api/pattern_stats")
async def pattern_stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT pattern_type, total, wins FROM pattern_stats WHERE total >= 3 ORDER BY (CAST(wins AS FLOAT)/total) DESC")
    rows = c.fetchall()
    conn.close()

    stats = []
    for r in rows:
        stats.append({
            "pattern": r[0],
            "total": r[1],
            "wins": r[2],
            "winrate": round(r[2] / r[1] * 100, 1) if r[1] > 0 else 0
        })
    return {"status": "success", "data": stats}


# ============================================================
# 7. TÀI KHOẢN & XÁC THỰC
# ============================================================
class AuthReq(BaseModel):
    action: str
    username: str
    password: str


@app.post("/api/auth")
async def auth_user(req: AuthReq):
    u = req.username.strip()
    p = req.password.strip()
    if not u or not p:
        return {"status": "error", "msg": "Nhập đủ thông tin!"}

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if req.action == "register":
        c.execute("SELECT username FROM users WHERE username = ?", (u,))
        if c.fetchone():
            conn.close()
            return {"status": "error", "msg": "Tài khoản đã tồn tại!"}
        c.execute("INSERT INTO users VALUES (?, ?, 0, '2000-01-01 00:00:00', 0)", (u, p))
        conn.commit()
        conn.close()
        return {"status": "success", "msg": "Đăng ký thành công!"}
    else:
        c.execute("SELECT password, is_banned FROM users WHERE username = ?", (u,))
        row = c.fetchone()
        conn.close()
        if not row or row[0] != p:
            return {"status": "error", "msg": "Sai tài khoản hoặc mật khẩu!"}
        if row[1] == 1:
            return {"status": "error", "msg": "Tài khoản bị khóa!"}
        return {"status": "success", "msg": "Đăng nhập thành công!"}


@app.get("/api/user_info")
async def get_user_info(username: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT balance, vip_expire FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if not row:
        return {"status": "error", "msg": "Không tìm thấy user!"}

    is_vip = datetime.now() < datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
    return {
        "status": "success",
        "data": {
            "balance": row[0],
            "vip_expire": row[1] if is_vip else "Chưa có VIP",
            "is_vip": is_vip
        }
    }


# ============================================================
# 8. NẠP THẺ
# ============================================================
class DepReq(BaseModel):
    username: str
    network: str
    amount: int
    pin: str
    serial: str


@app.post("/api/deposit")
async def deposit(req: DepReq):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO deposits (username, card_type, card_amount, card_pin, card_serial, status) VALUES (?, ?, ?, ?, ?, 'PENDING')",
        (req.username, req.network, req.amount, req.pin, req.serial))
    conn.commit()
    conn.close()
    return {"status": "success", "msg": "Gửi thẻ thành công! Chờ duyệt."}


# ============================================================
# 9. MUA VIP
# ============================================================
class BuyReq(BaseModel):
    username: str
    package: str


@app.post("/api/buy_vip")
async def buy_vip(req: BuyReq):
    prices = {
        "1D": (30000, 1),
        "3D": (50000, 3),
        "7D": (100000, 7),
        "30D": (150000, 30),
        "PERM": (200000, 36500)
    }
    if req.package not in prices:
        return {"status": "error", "msg": "Gói không hợp lệ!"}

    cost, days = prices[req.package]

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT balance, vip_expire FROM users WHERE username = ?", (req.username,))
    row = c.fetchone()

    if not row:
        conn.close()
        return {"status": "error", "msg": "Không tìm thấy user!"}

    if row[0] < cost:
        conn.close()
        return {"status": "error", "msg": "Không đủ tiền!"}

    now = datetime.now()
    curr_exp = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
    base_time = curr_exp if curr_exp > now else now
    new_exp = base_time + timedelta(days=days)

    c.execute("UPDATE users SET balance = balance - ?, vip_expire = ? WHERE username = ?",
              (cost, new_exp.strftime("%Y-%m-%d %H:%M:%S"), req.username))
    conn.commit()
    conn.close()
    return {"status": "success", "msg": "Mua VIP thành công!"}


# ============================================================
# 10. HEALTH CHECK & TRANG CHỦ
# ============================================================
@app.get("/health")
async def health():
    return {"status": "online", "time": datetime.now().isoformat(), "version": "3.0"}

@app.get("/")
async def home():
    if os.path.exists(INDEX_HTML):
        return FileResponse(INDEX_HTML)
    tpl = os.path.join(BASE_DIR, "templates", "index.html")
    if os.path.exists(tpl):
        return FileResponse(tpl)
    return {
        "status": "online",
        "msg": "🚀 Server AI VIP PRO MAX đang chạy!",
        "version": "3.0",
        "features": [
            "12 tín hiệu phân tích",
            "10+ cầu phổ biến",
            "Markov Chain + Entropy",
            "Anti-Trap Detection",
            "Pattern Learning tự động"
        ]
    }


# ============================================================
# 11. KHỞI CHẠY SERVER
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Server AI VIP PRO MAX khởi động tại port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)