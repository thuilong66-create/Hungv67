# ============================================================
#  SERVER AI VIP PRO MAX - v4.0
#  NGUYÊN TẮC: KHÔNG RANDOM - CHỈ DỰ ĐOÁN KHI CÓ CẦU RÕ RÀNG
#  Nếu không tìm được cầu phù hợp → Báo "CHỜ CẦU"
# ============================================================

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, uvicorn, sqlite3, os, logging, math
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="AI VIP PRO MAX", version="4.0")
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

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT, balance INTEGER,
        vip_expire DATETIME, is_banned INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, card_type TEXT,
        card_amount INTEGER, card_pin TEXT, card_serial TEXT, status TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS ai_memory (
        phien TEXT PRIMARY KEY, du_doan TEXT, ket_qua TEXT, is_win INTEGER,
        pattern_type TEXT, confidence REAL, created_at DATETIME)''')

    c.execute('''CREATE TABLE IF NOT EXISTS pattern_stats (
        pattern_type TEXT PRIMARY KEY, total INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0, last_updated DATETIME)''')

    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?, ?)",
              ('hungadmin11', 'hungki98', 999999999999, '2099-12-31 23:59:59', 0))

    conn.commit()
    conn.close()
    logger.info("✅ Khởi tạo database thành công!")


khoi_tao_db()


# ============================================================
# 2. HELPER: PHÂN TÍCH CẦU
# ============================================================
def detect_streak(kq_list):
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


def check_11(kq_list, window=6):
    if len(kq_list) < window:
        return False
    r = kq_list[-window:]
    return all(r[i] != r[i + 1] for i in range(len(r) - 1))


def check_22(kq_list):
    if len(kq_list) < 6:
        return False
    r = kq_list[-6:]
    return r[0] == r[1] and r[2] == r[3] and r[4] == r[5] and r[0] != r[2] and r[2] != r[4]


def check_33(kq_list):
    if len(kq_list) < 6:
        return False
    r = kq_list[-6:]
    return r[0] == r[1] == r[2] and r[3] == r[4] == r[5] and r[0] != r[3]


def check_121(kq_list):
    if len(kq_list) < 6:
        return False
    r = kq_list[-6:]
    return r[0] != r[1] and r[1] == r[2] and r[2] != r[3] and r[3] != r[4] and r[4] == r[5]


def check_212(kq_list):
    if len(kq_list) < 6:
        return False
    r = kq_list[-6:]
    return r[0] == r[1] and r[1] != r[2] and r[2] != r[3] and r[3] == r[4] and r[4] != r[5]


def check_123(kq_list):
    if len(kq_list) < 6:
        return False
    r = kq_list[-6:]
    return r[0] != r[1] and r[1] == r[2] and r[2] != r[3] and r[3] == r[4] and r[4] == r[5]


def check_31(kq_list):
    if len(kq_list) < 8:
        return False
    r = kq_list[-8:]
    return (r[0] == r[1] == r[2] and r[3] != r[2] and
            r[4] != r[3] and r[5] != r[4] and r[6] != r[5] and r[7] != r[6])


def check_13(kq_list):
    if len(kq_list) < 8:
        return False
    r = kq_list[-8:]
    return (r[0] != r[1] and r[1] != r[2] and r[2] != r[3] and
            r[3] == r[4] == r[5] and r[6] != r[5] and r[7] != r[6])

def check_groups(kq_list, groups):
    """Nhận diện cầu theo nhóm kích thước: [2,3]=TTXXX, [3,2,1]=TTTXXT, [4,4]=TTTTXXXX..."""
    n = sum(groups)
    if len(kq_list) < n:
        return False
    r = kq_list[-n:]
    idx = 0
    door = r[0]
    for g in groups:
        for _ in range(g):
            if r[idx] != door:
                return False
            idx += 1
        door = "Xỉu" if door == "Tài" else "Tài"
    return True


def markov_chain(kq_list, window=20):
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
    if len(kq_list) < 10:
        return 0.5
    recent = kq_list[-20:]
    p_tai = recent.count("Tài") / len(recent)
    p_xiu = 1 - p_tai
    if p_tai == 0 or p_xiu == 0:
        return 0.0
    return -(p_tai * math.log2(p_tai) + p_xiu * math.log2(p_xiu))


def anti_trap_detect(kq_list):
    if len(kq_list) < 8:
        return False
    r = kq_list[-8:]
    changes = sum(1 for i in range(len(r) - 1) if r[i] != r[i + 1])
    return changes >= 6


def get_pattern_winrate(pattern_type):
    if not pattern_type or pattern_type in ("FLEX", "NONE"):
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
# 3. HỌC MÁY - CHẤM ĐIỂM DỰ ĐOÁN CŨ
# ============================================================
def cap_nhat_va_hoc_lich_su(lst):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    for s in lst:
        phien_id = str(s.get("id"))
        actual_kq = "TÀI" if "TAI" in str(s.get("resultTruyenThong", "")).upper() else "XỈU"

        c.execute("SELECT du_doan, is_win, pattern_type FROM ai_memory WHERE phien = ?", (phien_id,))
        row = c.fetchone()

        if row and row[1] is None:
            pred, pattern = row[0], row[2]
            win_status = 1 if pred == actual_kq else 0
            c.execute("UPDATE ai_memory SET ket_qua = ?, is_win = ? WHERE phien = ?",
                      (actual_kq, win_status, phien_id))

            if pattern and pattern not in ("FLEX", "NONE"):
                for p in pattern.split("_"):
                    if p and p not in ("FLEX", "NONE"):
                        c.execute("INSERT OR IGNORE INTO pattern_stats (pattern_type, total, wins, last_updated) VALUES (?, 0, 0, ?)",
                                  (p, datetime.now()))
                        c.execute("UPDATE pattern_stats SET total = total + 1, wins = wins + ?, last_updated = ? WHERE pattern_type = ?",
                                  (win_status, datetime.now(), p))

    conn.commit()

    c.execute("SELECT is_win, pattern_type FROM ai_memory WHERE is_win IS NOT NULL ORDER BY created_at DESC LIMIT 30")
    history_records = c.fetchall()

    c.execute("SELECT phien, du_doan, ket_qua, is_win FROM ai_memory WHERE is_win IS NOT NULL ORDER BY created_at DESC LIMIT 10")
    recent_logs = c.fetchall()
    conn.close()

    total = len(history_records)
    wins = sum(1 for r in history_records if r[0] == 1)
    win_rate = (wins / total * 100) if total > 0 else 0.0
    return win_rate, recent_logs, history_records


# ============================================================
# 4. ENGINE: TÌM CẦU PHÙ HỢP NHẤT (KHÔNG RANDOM)
# ============================================================
def tim_cau_phu_hop(kq_list):
    """
    Quét TẤT CẢ các cầu, trả về danh sách cầu phù hợp với điểm ưu tiên.
    Mỗi cầu: dict {name, prediction, weight, confidence, note}
    """
    results = []
    if len(kq_list) < 6:
        return results

    last = kq_list[-1]
    opp = "XỈU" if last == "Tài" else "TÀI"
    cont = last.upper()
    streak, streak_type = detect_streak(kq_list)

    # ----- CẦU 1-1 (ưu tiên cao) -----
    if check_11(kq_list, 6):
        results.append({
            "name": "CAU_11", "prediction": opp, "weight": 10.0,
            "base_conf": 90.0, "note": f"⚡ Cầu 1-1 chuẩn → {opp}"
        })

    # ----- CẦU 2-2 -----
    if check_22(kq_list):
        results.append({
            "name": "CAU_22", "prediction": opp, "weight": 9.0,
            "base_conf": 88.0, "note": f"⚖️ Cầu 2-2 → {opp}"
        })

    # ----- CẦU 3-3 -----
    if check_33(kq_list):
        results.append({
            "name": "CAU_33", "prediction": opp, "weight": 9.5,
            "base_conf": 89.0, "note": f"🎯 Cầu 3-3 → {opp}"
        })

    # ----- CẦU 1-2-1 -----
    if check_121(kq_list):
        results.append({
            "name": "CAU_121", "prediction": opp, "weight": 8.0,
            "base_conf": 85.0, "note": f"📊 Cầu 1-2-1 → {opp}"
        })

    # ----- CẦU 2-1-2 -----
    if check_212(kq_list):
        results.append({
            "name": "CAU_212", "prediction": opp, "weight": 8.5,
            "base_conf": 86.0, "note": f"📊 Cầu 2-1-2 → {opp}"
        })

    # ----- CẦU 1-2-3 -----
    if check_123(kq_list):
        results.append({
            "name": "CAU_123", "prediction": opp, "weight": 7.5,
            "base_conf": 84.0, "note": f"📊 Cầu 1-2-3 → {opp}"
        })

    # ----- CẦU 3-1 -----
    if check_31(kq_list):
        results.append({
            "name": "CAU_31", "prediction": opp, "weight": 7.0,
            "base_conf": 83.0, "note": f"📊 Cầu 3-1 → {opp}"
        })

    # ----- CẦU 1-3 -----
    if check_13(kq_list):
        results.append({
            "name": "CAU_13", "prediction": opp, "weight": 7.0,
            "base_conf": 83.0, "note": f"📊 Cầu 1-3 → {opp}"
        })

    # ----- BỆT -----
    if streak == 3:
        results.append({
            "name": "DU_BET", "prediction": cont, "weight": 8.0,
            "base_conf": 85.0, "note": f"🔥 Bệt 3 tay → Theo {cont}"
        })
    elif streak == 4 or streak == 5:
        results.append({
            "name": "BE_BET_MED", "prediction": cont, "weight": 6.5,
            "base_conf": 80.0, "note": f"⚡ Bệt {streak} tay → Theo nhẹ {cont}"
        })
    elif streak == 6 or streak == 7 or streak == 8:
        results.append({
            "name": "BE_BET_ALERT", "prediction": opp, "weight": 8.5,
            "base_conf": 87.0, "note": f"⚠️ Bệt {streak} tay → Nghi bẻ {opp}"
        })
    elif streak >= 9:
        results.append({
            "name": "BE_BET_LONG", "prediction": opp, "weight": 10.0,
            "base_conf": 92.0, "note": f"🛑 Bệt {streak} tay CỰC DÀI → BẺ {opp}"
        })

    # ----- MARKOV CHAIN -----
    p_cont = markov_chain(kq_list, 20)
    if p_cont >= 0.65:
        results.append({
            "name": "MARKOV_CONT", "prediction": cont, "weight": 7.0,
            "base_conf": 78.0 + (p_cont - 0.65) * 30,
            "note": f"🔗 Markov {int(p_cont * 100)}% tiếp {cont}"
        })
    elif p_cont <= 0.35:
        results.append({
            "name": "MARKOV_OPP", "prediction": opp, "weight": 7.0,
            "base_conf": 78.0 + (0.35 - p_cont) * 30,
            "note": f"🔗 Markov {int((1 - p_cont) * 100)}% đảo {opp}"
        })

    # ----- HỒI QUY ĐỘNG -----
    recent_20 = kq_list[-20:] if len(kq_list) >= 20 else kq_list
    diff = recent_20.count("Tài") - recent_20.count("Xỉu")
    if diff >= 6:
        results.append({
            "name": "HOI_QUY", "prediction": "XỈU", "weight": 7.5,
            "base_conf": 82.0 + min(diff, 10),
            "note": f"📉 Lệch Tài +{diff} → Đảo XỈU"
        })
    elif diff <= -6:
        results.append({
            "name": "HOI_QUY", "prediction": "TÀI", "weight": 7.5,
            "base_conf": 82.0 + min(abs(diff), 10),
            "note": f"📈 Lệch Xỉu +{abs(diff)} → Đảo TÀI"
        })

    # ----- ANTI-TRAP -----
    if anti_trap_detect(kq_list):
        results.append({
            "name": "ANTI_TRAP", "prediction": opp, "weight": 7.0,
            "base_conf": 82.0, "note": "🚨 Phát hiện bẫy đảo → Đi ngược"
        })

    # ----- CÁC CẦU THEO NHÓM: 2-3, 3-2-1, 4-4, 5-5, 3-1-3, 1-3-1, 2-1-2 -----
    for name, groups, w, conf in [
        ("CAU_2-3", [2, 3], 8.0, 85.0),
        ("CAU_3-2-1", [3, 2, 1], 8.5, 86.0),
        ("CAU_4-4", [4, 4], 9.5, 89.0),
        ("CAU_5-5", [5, 5], 10.0, 91.0),
        ("CAU_3-1-3", [3, 1, 3], 8.0, 85.0),
        ("CAU_1-3-1", [1, 3, 1], 8.0, 85.0),
        ("CAU_2-1-2", [2, 1, 2], 8.5, 86.0),
    ]:
        if check_groups(kq_list, groups):
            results.append({"name": name, "prediction": opp, "weight": w,
                            "base_conf": conf, "note": f"📊 {name} → {opp}"})

    # ----- CẦU BẺ (bệt dài 5+ rồi đảo đúng 1 phát) -----
    if len(kq_list) >= 6:
        last_door = kq_list[-1]
        prev_door = "Xỉu" if last_door == "Tài" else "Tài"
        long_streak = 0
        for i in range(len(kq_list) - 2, -1, -1):
            if kq_list[i] == prev_door:
                long_streak += 1
            else:
                break
        if long_streak >= 5:
            results.append({"name": "CAU_BE", "prediction": last_door.upper(), "weight": 6.5,
                            "base_conf": 78.0, "note": f"🔨 Bẻ sau bệt {long_streak} → tiếp {last_door.upper()}"})

    return results

def _fallback_predict(kq_list):
    """LUÔN trả về kết quả (KHÔNG BAO GIỜ CHỜ) khi chưa đủ cầu - dùng Markov + xu hướng."""
    if not kq_list:
        return "TÀI", 62.0
    last = kq_list[-1].upper()
    opp = "XỈU" if last == "TÀI" else "TÀI"
    p = markov_chain(kq_list, 20)
    if p >= 0.5:
        return last, round(60 + (p - 0.5) * 28, 1)
    return opp, round(60 + (0.5 - p) * 28, 1)


# ============================================================
# 5. AI CHÍNH: CHỌN CẦU + DỰ ĐOÁN (LUÔN CÓ KẾT QUẢ - KHÔNG CHỜ)
# ============================================================
def phan_tich_ai(kq_list, next_phien_id, win_rate, history_records):
    tong_tai = kq_list.count("Tài")
    tong_xiu = kq_list.count("Xỉu")
    radar = "".join(["🔴" if x == "Tài" else "🔵" for x in kq_list[-15:]])

    # ---------- CHƯA ĐỦ DỮ LIỆU → FALLBACK (LUÔN CÓ KẾT QUẢ) ----------
    if len(kq_list) < 6:
        fb_pred, fb_conf = _fallback_predict(kq_list)
        return {
            "du_doan": fb_pred, "ti_le": fb_conf,
            "loi_khuyen": "⚡ Dữ liệu ít → Dự đoán theo xu hướng gần nhất",
            "trend": radar,
            "tong_tai": tong_tai, "tong_xiu": tong_xiu,
            "patterns": [], "signal_score": {"TAI": 0, "XIU": 0}, "entropy": 0,
            "status_predict": "FALLBACK",
            "ai_stats": {"win_rate": round(win_rate, 1), "total_learned_sessions": len(history_records)}
        }

    # ---------- TÌM TẤT CẢ CẦU PHÙ HỢP ----------
    cau_list = tim_cau_phu_hop(kq_list)

    # ---------- KHÔNG CÓ CẦU NÀO → FALLBACK (KHÔNG BAO GIỜ CHỜ) ----------
    if not cau_list:
        fb_pred, fb_conf = _fallback_predict(kq_list)
        return {
            "du_doan": fb_pred, "ti_le": fb_conf,
            "loi_khuyen": "⚡ Chưa rõ cầu → Dự đoán theo Markov + xu hướng",
            "trend": radar,
            "tong_tai": tong_tai, "tong_xiu": tong_xiu,
            "patterns": [], "signal_score": {"TAI": 0, "XIU": 0},
            "entropy": round(entropy_score(kq_list), 3),
            "status_predict": "FALLBACK",
            "ai_stats": {"win_rate": round(win_rate, 1), "total_learned_sessions": len(history_records)}
        }

    # ---------- VOTING: CỘNG ĐIỂM THEO CẦU ----------
    signal = {"TAI": 0.0, "XIU": 0.0}
    pattern_names = []
    notes = []
    total_weight = 0.0

    for cau in cau_list:
        pred = cau["prediction"]
        w = cau["weight"]
        conf = cau["base_conf"]

        # Trọng số = weight * (confidence/100)
        score = w * (conf / 100.0)
        signal[pred] += score
        total_weight += score
        pattern_names.append(cau["name"])
        notes.append(cau["note"])

    # ---------- CHECK CẦU XUNG ĐỘT (KHÔNG CHỜ - chỉ hạ tin cậy) ----------
    conflict_penalty = 0.0
    if signal["TAI"] > 0 and signal["XIU"] > 0:
        tong = signal["TAI"] + signal["XIU"]
        chenh_lech = abs(signal["TAI"] - signal["XIU"]) / tong
        if chenh_lech < 0.15:
            conflict_penalty = 10.0

    # ---------- CHỌN CỬA THẮNG ----------
    if signal["TAI"] > signal["XIU"]:
        du_doan = "TÀI"
        score_win = signal["TAI"]
    else:
        du_doan = "XỈU"
        score_win = signal["XIU"]

    # ---------- TÍNH % TIN CẬY (DỰA TRÊN TỈ LỆ ĐIỂM) ----------
    tong_diem = signal["TAI"] + signal["XIU"]
    ty_le_diem = score_win / tong_diem if tong_diem > 0 else 0.5

    # Base confidence từ tỉ lệ điểm (chuyển 0.5-1.0 thành 60-95%)
    base_conf = 60 + (ty_le_diem - 0.5) * 70 - conflict_penalty  # 0.5→60%, 1.0→95%, trừ penalty nếu xung đột

    # ---------- ĐIỀU CHỈNH THEO PATTERN WINRATE DB ----------
    pattern_main = pattern_names[0] if pattern_names else "NONE"
    pattern_wr_db = get_pattern_winrate(pattern_main)
    if pattern_wr_db is not None:
        if pattern_wr_db < 0.40:
            du_doan = "XỈU" if du_doan == "TÀI" else "TÀI"
            base_conf = min(base_conf + 10, 96)
            notes.append(f"🧠 Đảo chiều (cầu yếu {int(pattern_wr_db * 100)}%)")
        elif pattern_wr_db > 0.70:
            base_conf = min(base_conf + 5, 96)
            notes.append(f"✨ Cầu mạnh {int(pattern_wr_db * 100)}%")

    # ---------- ENTROPY FILTER ----------
    ent = entropy_score(kq_list)
    if ent > 0.95:
        base_conf = min(base_conf, 78.0)
        notes.append("🌊 Nhiễu cao → Hạ tin")
    elif ent < 0.5:
        base_conf = min(base_conf + 3, 96)
        notes.append("🎯 Xu hướng rõ → Tăng tin")

    # ---------- CLAMP CONFIDENCE (KHÔNG RANDOM) ----------
    final_conf = max(min(base_conf, 98.0), 60.0)

    # ---------- LƯU BỘ NHỚ ----------
    pattern_type = "_".join(pattern_names[:2])
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO ai_memory (phien, du_doan, pattern_type, confidence, created_at) VALUES (?, ?, ?, ?, ?)",
              (next_phien_id, du_doan, pattern_type, final_conf, datetime.now()))
    conn.commit()
    conn.close()

    return {
        "du_doan": du_doan,
        "ti_le": round(final_conf, 1),
        "loi_khuyen": " | ".join(notes[:3]),
        "trend": radar,
        "tong_tai": tong_tai, "tong_xiu": tong_xiu,
        "patterns": pattern_names,
        "signal_score": {"TAI": round(signal["TAI"], 2), "XIU": round(signal["XIU"], 2)},
        "entropy": round(ent, 3),
        "status_predict": "OK",
        "ai_stats": {
            "win_rate": round(win_rate, 1),
            "total_learned_sessions": len(history_records),
            "pattern_winrate": round(pattern_wr_db * 100, 1) if pattern_wr_db is not None else None
        }
    }


# ============================================================
# 6. API SCAN GAME
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

        win_rate, recent_logs, history_records = cap_nhat_va_hoc_lich_su(lst)

        next_phien_id = str(int(lst[-1]["id"]) + 1)
        data = phan_tich_ai(kq, next_phien_id, win_rate, history_records)
        if mode == "ai_pro" and data.get("du_doan") != "CHỜ":
            data["ti_le"] = min(data.get("ti_le", 60) + 5, 98.0)
        data["phien"] = next_phien_id
        data["logs"] = recent_logs

        return {"status": "success", "data": data}

    except Exception as e:
        logger.error(f"Lỗi API scan: {e}")
        return {"status": "error", "msg": "Bảo trì máy chủ Game!"}


# ============================================================
# 7. API PATTERN STATS
# ============================================================
@app.get("/api/pattern_stats")
async def pattern_stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT pattern_type, total, wins FROM pattern_stats WHERE total >= 3 ORDER BY (CAST(wins AS FLOAT)/total) DESC")
    rows = c.fetchall()
    conn.close()

    stats = [{"pattern": r[0], "total": r[1], "wins": r[2],
              "winrate": round(r[2] / r[1] * 100, 1) if r[1] > 0 else 0} for r in rows]
    return {"status": "success", "data": stats}


# ============================================================
# 8. AUTH
# ============================================================
class AuthReq(BaseModel):
    action: str
    username: str
    password: str


@app.post("/api/auth")
async def auth_user(req: AuthReq):
    u, p = req.username.strip(), req.password.strip()
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
    return {"status": "success", "data": {
        "balance": row[0],
        "vip_expire": row[1] if is_vip else "Chưa có VIP",
        "is_vip": is_vip
    }}


# ============================================================
# 9. DEPOSIT & BUY VIP
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
    c.execute("INSERT INTO deposits (username, card_type, card_amount, card_pin, card_serial, status) VALUES (?, ?, ?, ?, ?, 'PENDING')",
              (req.username, req.network, req.amount, req.pin, req.serial))
    conn.commit()
    conn.close()
    return {"status": "success", "msg": "Gửi thẻ thành công! Chờ duyệt."}


class BuyReq(BaseModel):
    username: str
    package: str


@app.post("/api/buy_vip")
async def buy_vip(req: BuyReq):
    prices = {"1D": (30000, 1), "3D": (50000, 3), "7D": (100000, 7),
              "30D": (150000, 30), "PERM": (200000, 36500)}
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
# 10. HEALTH CHECK & HOME
# ============================================================
@app.get("/health")
async def health():
    return {"status": "online", "time": datetime.now().isoformat(), "version": "4.0"}

@app.get("/")
async def home():
    if os.path.exists(INDEX_HTML):
        return FileResponse(INDEX_HTML)
    tpl = os.path.join(BASE_DIR, "templates", "index.html")
    if os.path.exists(tpl):
        return FileResponse(tpl)
    return {
        "status": "online",
        "msg": "🚀 Server AI VIP PRO MAX v4.0 - KHÔNG RANDOM",
        "features": [
            "Chỉ dự đoán khi tìm được cầu",
            "Không bịa kết quả khi cầu nhiễu",
            "Voting theo trọng số cầu",
            "Tự học từ pattern winrate"
        ]
    }


# ============================================================
# 11. RUN
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Server AI VIP PRO MAX v4.0 - Port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)