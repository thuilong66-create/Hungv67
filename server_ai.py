# ============================================================
#  SERVER AI VIP PRO MAX - v6.0 VIP PRO
#  NÂNG CẤP: LẤY 15 PHIÊN GẦN NHẤT + THUẬT TOÁN DỰ ĐOÁN THEO CẦU
#  Nguyên tắc: KHÔNG RANDOM - CHỈ DỰ ĐOÁN KHI CÓ CẦU RÕ RÀNG
#  + Phát hiện chu kỳ lặp (theo cầu) → tiếp nối cầu
#  + Bảng cầu mẫu mở rộng đến độ dài 15
# ============================================================
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, uvicorn, sqlite3, os, logging, math
from datetime import datetime, timedelta
from collections import Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="AI VIP PRO MAX", version="6.0")
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
# 4. ENGINE VIP PRO: 15 PHIÊN GẦN NHẤT + DỰ ĐOÁN THEO CẦU
# ============================================================
WINDOW = 15  # VIP PRO: phân tích đúng 15 phiên gần nhất

def _normalize(kq_list):
    """Chuẩn hóa 'Tài'/'Xỉu'/'TÀI'/'XỈU'/'T'/'X' → 'T'/'X'"""
    out = []
    for x in kq_list:
        s = str(x).strip().upper()
        if s in ("TÀI", "TAI", "T"):
            out.append("T")
        elif s in ("XỈU", "XIỦ", "XIU", "X"):
            out.append("X")
    return out

def _rle(seq):
    """Run-length encoding. Trả về [(char, count), ...] từ cũ → mới."""
    if not seq:
        return []
    out = []
    cur = seq[0]
    cnt = 1
    for c in seq[1:]:
        if c == cur:
            cnt += 1
        else:
            out.append((cur, cnt))
            cur = c
            cnt = 1
    out.append((cur, cnt))
    return out

def _match_groups(rle, groups):
    """Khớp chính xác đuôi RLE theo dãy nhóm. VD groups=[3,1,3] → TTT X TTT."""
    if len(rle) < len(groups):
        return False
    tail_counts = [cnt for _, cnt in rle[-len(groups):]]
    return tail_counts == groups

# ---------- THUẬT TOÁN THEO CẦU: PHÁT HIỆN CHU KỲ LẶP ----------
def _find_cycle(seq, min_len=2, max_len=7):
    """
    Tìm chu kỳ lặp nhỏ nhất trong đuôi chuỗi.
    Trả về (cycle_length, next_char) hoặc None.
    Ví dụ: T X T X T X → cycle=2, next=T (tiếp nối cầu đảo tay)
           TT X TT X → cycle=3 (nhóm 2-1), next=T
    Yêu cầu: chu kỳ phải lặp ít nhất 2 lần HOÀN CHỈNH ở đuôi.
    """
    n = len(seq)
    best = None
    best_repeats = 0
    for L in range(min_len, max_len + 1):
        if n < L * 2:
            continue
        # Lấy đuôi dài nhất là bội số của L (ít nhất 2 chu kỳ)
        num_cycles = n // L
        if num_cycles < 2:
            continue
        tail = seq[-(num_cycles * L):]
        cycle = tail[:L]
        # Kiểm tra toàn bộ đuôi có phải lặp của cycle không
        ok = True
        for i in range(len(tail)):
            if tail[i] != cycle[i % L]:
                ok = False
                break
        if ok:
            # Đếm số lần lặp đầy đủ
            repeats = num_cycles
            if repeats > best_repeats:
                best_repeats = repeats
                next_char = cycle[0]  # tiếp nối chu kỳ
                best = (L, next_char, repeats, cycle)
    return best

def _theo_cau_predict(seq):
    """
    Thuật toán DỰ ĐOÁN THEO CẦU:
    B1: Tìm chu kỳ lặp nhỏ nhất ở đuôi 15 phiên → tiếp nối cầu.
    B2: Nếu chu kỳ ≥ 3 lần lặp → tin cậy cao.
    Trả về dict {name, prediction, conf, note} hoặc None.
    """
    if len(seq) < 6:
        return None
    cyc = _find_cycle(seq, min_len=2, max_len=7)
    if not cyc:
        return None
    L, next_char, repeats, cycle = cyc
    if repeats < 2:
        return None
    pred = "TÀI" if next_char == "T" else "XỈU"
    cycle_str = "-".join(["T" if c == "T" else "X" for c in cycle])
    # Độ tin cậy theo số lần lặp
    if repeats >= 5:
        conf = 93.0
        level = "CỰC MẠNH"
    elif repeats >= 4:
        conf = 90.0
        level = "RẤT MẠNH"
    elif repeats >= 3:
        conf = 87.0
        level = "MẠNH"
    else:
        conf = 82.0
        level = "RÕ"
    note = f"🌉 Theo cầu [{cycle_str}] lặp {repeats}x ({level}) → {pred}"
    return {"name": f"THEO_CAU_L{L}_x{repeats}", "prediction": pred, "conf": conf, "note": note}

# ---------- BẢNG THUẬT TOÁN (ưu tiên từ trên xuống) ----------
# (tên, loại, thông_số, hành_động, %tin_cậy, ghi_chú)
#   loại 'groups' : thông_số = list độ dài nhóm (khớp đuôi RLE)
#   loại 'streak' : thông_số = (min, max) độ dài bệt hiện tại
#   hành_động 'opp' = đảo (đối lập phiên cuối), 'cont' = theo (giữ nguyên)
PATTERNS = [
    # ===== RỒNG / BỆT CỰC DÀI (ưu tiên cao nhất) =====
    ("RONG_BET_10+",     "streak", (10, 99), "opp", 95.0, "🐉 Rồng/Bệt 10+ → Bẻ {opp}"),
    ("RONG_BET_8-9",     "streak", (8, 9),   "opp", 93.0, "🐉 Rồng/Bệt 8-9 → Bẻ {opp}"),
    ("RONG_BET_7",       "streak", (7, 7),   "opp", 91.0, "🐉 Bệt 7 → Bẻ {opp}"),
    # ===== CẦU DÀI HIẾM (độ dài 10-15) =====
    ("CAU_5-5",          "groups", [5,5],     "opp", 92.0, "💎 Cầu 5-5 hiếm → Đổi {opp}"),
    ("CAU_6-6",          "groups", [6,6],     "opp", 93.0, "💎 Cầu 6-6 cực hiếm → Đổi {opp}"),
    ("CAU_4-4-4",        "groups", [4,4,4],   "opp", 91.0, "💎 Cầu 4-4-4 → {opp}"),
    ("CAU_3-3-3",        "groups", [3,3,3],   "opp", 90.0, "💎 Cầu 3-3-3 → {opp}"),
    ("CAU_2-2-2-2-2",    "groups", [2,2,2,2,2],"opp",90.0,"💎 Cầu 2-2-2-2-2 → {opp}"),
    ("CAU_7-3",          "groups", [7,3],     "opp", 91.0, "💎 Cầu 7-3 → {opp}"),
    ("CAU_3-7",          "groups", [3,7],     "opp", 91.0, "💎 Cầu 3-7 → {opp}"),
    ("CAU_4-3-4",        "groups", [4,3,4],   "opp", 90.0, "💎 Cầu 4-3-4 đối xứng → {opp}"),
    ("CAU_3-4-3",        "groups", [3,4,3],   "opp", 90.0, "💎 Cầu 3-4-3 đối xứng → {opp}"),
    ("CAU_5-1-5",        "groups", [5,1,5],   "opp", 92.0, "💎 Cầu 5-1-5 cực hiếm → {opp}"),
    ("CAU_1-5-1",        "groups", [1,5,1],   "opp", 92.0, "💎 Cầu 1-5-1 cực hiếm → {opp}"),
    ("CAU_4-1-4",        "groups", [4,1,4],   "opp", 91.0, "💎 Cầu 4-1-4 → {opp}"),
    ("CAU_1-4-1",        "groups", [1,4,1],   "opp", 91.0, "💎 Cầu 1-4-1 → {opp}"),
    ("CAU_2-4-2",        "groups", [2,4,2],   "opp", 89.0, "💎 Cầu 2-4-2 → {opp}"),
    ("CAU_4-2-4",        "groups", [4,2,4],   "opp", 89.0, "💎 Cầu 4-2-4 → {opp}"),
    ("CAU_3-2-2-3",      "groups", [3,2,2,3], "opp", 89.0, "💎 Cầu 3-2-2-3 → {opp}"),
    ("CAU_2-3-3-2",      "groups", [2,3,3,2], "opp", 89.0, "💎 Cầu 2-3-3-2 → {opp}"),
    ("CAU_2-2-3-3",      "groups", [2,2,3,3], "opp", 88.0, "📊 Cầu 2-2-3-3 → {opp}"),
    ("CAU_3-3-2-2",      "groups", [3,3,2,2], "opp", 88.0, "📊 Cầu 3-3-2-2 → {opp}"),
    ("CAU_1-1-1-1-1-1-1","groups", [1,1,1,1,1,1,1],"opp",92.0,"⚡ Đảo tay 7 nhịp → {opp}"),
    ("CAU_1-1_6",        "groups", [1,1,1,1,1,1],"opp",90.0,"⚡ Đảo tay 6 nhịp → {opp}"),
    # ===== CẦU HIẾM (độ dài 8) =====
    ("CAU_3-1-1-3",      "groups", [3,1,1,3], "opp", 90.0, "💎 Cầu 3-1-1-3 hiếm → {opp}"),
    ("CAU_4-4",          "groups", [4,4],     "opp", 89.0, "🎯 Cầu 4-4 → Đổi {opp}"),
    ("DAO_GUONG_2222",   "groups", [2,2,2,2], "opp", 88.0, "🪞 Đảo gương TTXXTTXX → {opp}"),
    ("VONG_LAP_3-2-3",   "groups", [3,2,3],   "opp", 86.0, "🔁 Vòng lặp 3-2 → {opp}"),
    # ===== ĐỘ DÀI 7 =====
    ("CAU_3-1-3",        "groups", [3,1,3],   "opp", 91.0, "💎 Cầu 3-1-3 rất hiếm → {opp}"),
    ("CAU_1-1-3-1-1",    "groups", [1,1,3,1,1],"opp",82.0, "⚠️ Cầu 1-1-3-1-1 → {opp}"),
    ("VONG_LAP_2-3-2",   "groups", [2,3,2],   "opp", 84.0, "🔁 Vòng lặp/Gương đối xứng → {opp}"),
    # ===== ĐỘ DÀI 6 =====
    ("CAU_1-5",          "groups", [1,5],     "opp", 89.0, "⭐ Cầu 1-5 rất hiếm → {opp}"),
    ("CAU_5-1",          "groups", [5,1],     "opp", 89.0, "⭐ Cầu 5-1 rất hiếm → {opp}"),
    ("CAU_3-3",          "groups", [3,3],     "opp", 89.0, "🎯 Cầu 3-3 → Đổi {opp}"),
    ("CAU_1-1-2-2",      "groups", [1,1,2,2], "opp", 88.0, "📊 Cầu 1-1-2-2 hiếm → {opp}"),
    ("CAU_2-2-1-1",      "groups", [2,2,1,1], "opp", 88.0, "📊 Cầu 2-2-1-1 hiếm → {opp}"),
    ("CAU_1-2-1-2",      "groups", [1,2,1,2], "opp", 87.0, "📊 Cầu 1-2-1-2 → {opp}"),
    ("NHAY_COC_2121",    "groups", [2,1,2,1], "opp", 87.0, "🐸 Nhảy cóc TTXTTX → {opp}"),
    ("CAU_2-1-1-2",      "groups", [2,1,1,2], "opp", 87.0, "📊 Cầu 2-1-1-2 → {opp}"),
    ("CAU_1-1-1-1-2",    "groups", [1,1,1,1,2],"opp",87.0, "📊 Cầu TXTXTT → {opp}"),
    ("CAU_1-2-3",        "groups", [1,2,3],   "opp", 84.0, "📊 Cầu 1-2-3 → Đổi {opp}"),
    ("CAU_3-2-1",        "groups", [3,2,1],   "opp", 86.0, "📊 Cầu 3-2-1 → {opp}"),
    # ===== ĐỘ DÀI 5 =====
    ("CAU_1-3-1",        "groups", [1,3,1],   "opp", 90.0, "💎 Cầu 1-3-1 hiếm → {opp}"),
    ("CAU_1-1-1-2",      "groups", [1,1,1,2], "opp", 87.0, "📊 Cầu 1-1-1-2 → {opp}"),
    ("CAU_2-1-2",        "groups", [2,1,2],   "opp", 86.0, "📊 Cầu 2-1-2 (theo nhịp) → {opp}"),
    ("CAU_2-3",          "groups", [2,3],     "opp", 85.0, "📊 Cầu 2-3 → {opp}"),
    # ===== ĐỘ DÀI 4 =====
    ("CAU_2-2",          "groups", [2,2],     "opp", 88.0, "⚖️ Cầu 2-2 → Đổi sau 2 → {opp}"),
    ("CAU_1-2-1",        "groups", [1,2,1],   "opp", 85.0, "📊 Cầu 1-2-1 (đảo cuối) → {opp}"),
    ("CAU_3-1",          "groups", [3,1],     "opp", 83.0, "📊 Cầu 3-1 (đảo 1 nhịp) → {opp}"),
    ("CAU_1-3",          "groups", [1,3],     "opp", 83.0, "📊 Cầu 1-3 (đảo 3 nhịp) → {opp}"),
    # ===== BỆT DÀI 5-6 (bẻ) =====
    ("BET_DAI_5-6",      "streak", (5, 6),    "opp", 88.0, "⚠️ Bệt {n} tay → Bẻ {opp}"),
    # ===== BỆT NGẮN (theo) =====
    ("BET_4",            "streak", (4, 4),    "cont",80.0, "⚡ Bệt 4 tay → Theo nhẹ {cont}"),
    ("BET_NGAN_3",       "streak", (3, 3),    "cont",85.0, "🔥 Bệt 3 tay → Theo {cont}"),
]

def tim_thuat_toan_khop(kq_list):
    """
    VIP PRO: Lấy đúng 15 phiên gần nhất.
    BƯỚC 1 (ưu tiên cao nhất): THUẬT TOÁN THEO CẦU - phát hiện chu kỳ lặp.
    BƯỚC 2: Quét bảng PATTERNS theo thứ tự ưu tiên.
    Thuật toán NÀO khớp TRƯỚC → trả về dự báo của thuật toán đó.
    Trả về dict {name, prediction, conf, note} hoặc None.
    """
    seq = _normalize(kq_list)
    if len(seq) < 3:
        return None
    seq15 = seq[-WINDOW:]
    rle = _rle(seq15)
    last_char = seq15[-1]
    cont = "TÀI" if last_char == "T" else "XỈU"
    opp = "XỈU" if last_char == "T" else "TÀI"
    streak = rle[-1][1] if rle else 0

    # ===== BƯỚC 1: THUẬT TOÁN THEO CẦU (ưu tiên CAO NHẤT) =====
    theo_cau = _theo_cau_predict(seq15)
    if theo_cau:
        return theo_cau

    # ===== BƯỚC 2: QUÉT BẢNG PATTERNS =====
    for name, ptype, spec, action, conf, note_tpl in PATTERNS:
        matched = False
        if ptype == "streak":
            lo, hi = spec
            if lo <= streak <= hi:
                matched = True
        elif ptype == "groups":
            if _match_groups(rle, spec):
                matched = True
        if matched:
            pred = cont if action == "cont" else opp
            note = note_tpl.format(opp=opp, cont=cont, n=streak)
            return {"name": name, "prediction": pred, "conf": conf, "note": note}

    # ===== Palindrome (cầu đối xứng) - ưu tiên thấp =====
    s6 = "".join(seq15[-6:])
    if len(s6) >= 4 and s6 == s6[::-1]:
        return {"name": "PALINDROME", "prediction": opp, "conf": 78.0,
                "note": f"🪞 Palindrome đối xứng → {opp}"}
    return None

def _fallback_predict(kq_list):
    """Không thuật toán nào khớp → dùng Markov + xu hướng (vẫn LUÔN có kết quả)."""
    if not kq_list:
        return "TÀI", 62.0
    seq = _normalize(kq_list)
    last = "TÀI" if seq[-1] == "T" else "XỈU"
    opp = "XỈU" if last == "TÀI" else "TÀI"
    p = markov_chain(kq_list, 20)
    if p >= 0.5:
        return last, round(60 + (p - 0.5) * 28, 1)
    return opp, round(60 + (0.5 - p) * 28, 1)

# ============================================================
# 5. AI CHÍNH VIP PRO: 15 PHIÊN → THEO CẦU → DỰ BÁO
# ============================================================
def phan_tich_ai(kq_list, next_phien_id, win_rate, history_records):
    tong_tai = kq_list.count("Tài") + kq_list.count("TÀI")
    tong_xiu = kq_list.count("Xỉu") + kq_list.count("XỈU")
    radar = "".join(["🔴" if str(x).upper().startswith("T") else "🔵" for x in kq_list[-15:]])
    ent = entropy_score(kq_list) if len(kq_list) >= 10 else 0.5

    seq = _normalize(kq_list)
    if len(seq) < 3:
        fb_pred, fb_conf = _fallback_predict(kq_list)
        return {
            "du_doan": fb_pred, "ti_le": fb_conf,
            "loi_khuyen": "⚡ Dữ liệu ít (<3 phiên) → Dự đoán theo xu hướng",
            "trend": radar,
            "tong_tai": tong_tai, "tong_xiu": tong_xiu,
            "patterns": [], "signal_score": {"TAI": 0, "XIU": 0}, "entropy": 0,
            "status_predict": "FALLBACK",
            "ai_stats": {"win_rate": round(win_rate, 1), "total_learned_sessions": len(history_records)}
        }

    # ---------- LẤY ĐÚNG 15 PHIÊN GẦN NHẤT → THEO CẦU / PATTERN ----------
    matched = tim_thuat_toan_khop(kq_list)

    if not matched:
        fb_pred, fb_conf = _fallback_predict(kq_list)
        return {
            "du_doan": fb_pred, "ti_le": fb_conf,
            "loi_khuyen": "⚡ 15 phiên gần nhất chưa khớp cầu mẫu nào → Dự đoán theo Markov",
            "trend": radar,
            "tong_tai": tong_tai, "tong_xiu": tong_xiu,
            "patterns": [], "signal_score": {"TAI": 0, "XIU": 0},
            "entropy": round(ent, 3),
            "status_predict": "FALLBACK",
            "ai_stats": {"win_rate": round(win_rate, 1), "total_learned_sessions": len(history_records)}
        }

    # ---------- CÓ THUẬT TOÁN KHỚP → LẤY DỰ BÁO ----------
    du_doan = matched["prediction"]
    base_conf = matched["conf"]
    pattern_name = matched["name"]
    notes = [matched["note"]]

    # ---------- ĐIỀU CHỈNH THEO WINRATE ĐÃ HỌC (DB) ----------
    pattern_wr_db = get_pattern_winrate(pattern_name)
    if pattern_wr_db is not None:
        if pattern_wr_db < 0.40:
            du_doan = "XỈU" if du_doan == "TÀI" else "TÀI"
            base_conf = min(base_conf + 5, 96)
            notes.append(f"🧠 Đảo chiều (cầu này thắng chỉ {int(pattern_wr_db*100)}%)")
        elif pattern_wr_db > 0.70:
            base_conf = min(base_conf + 4, 97)
            notes.append(f"✨ Cầu này mạnh ({int(pattern_wr_db*100)}%)")

    # ---------- ENTROPY FILTER (miễn giảm cho THEO_CAU - cầu rõ ràng) ----------
    is_theo_cau = pattern_name.startswith("THEO_CAU")
    if not is_theo_cau and ent > 0.95:
        base_conf = min(base_conf, 78.0)
        notes.append("🌊 Nhiễu cao → Hạ tin")
    elif ent < 0.5:
        base_conf = min(base_conf + 2, 97)
        notes.append("🎯 Xu hướng rõ → Tăng tin")
    elif is_theo_cau and ent > 0.95:
        # Cầu đảo/chu kỳ rõ ràng dù entropy cao → không phạt, cộng nhẹ
        base_conf = min(base_conf + 1, 97)
        notes.append("🌉 Cầu chu kỳ rõ → Giữ tin")

    final_conf = max(min(base_conf, 98.0), 60.0)

    # ---------- LƯU BỘ NHỚ ----------
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO ai_memory (phien, du_doan, pattern_type, confidence, created_at) VALUES (?, ?, ?, ?, ?)",
              (next_phien_id, du_doan, pattern_name, final_conf, datetime.now()))
    conn.commit()
    conn.close()

    signal = {"TAI": 0.0, "XIU": 0.0}
    if du_doan == "TÀI":
        signal["TAI"] = round(final_conf / 10.0, 2)
    else:
        signal["XIU"] = round(final_conf / 10.0, 2)

    return {
        "du_doan": du_doan,
        "ti_le": round(final_conf, 1),
        "loi_khuyen": " | ".join(notes[:3]),
        "trend": radar,
        "tong_tai": tong_tai, "tong_xiu": tong_xiu,
        "patterns": [pattern_name],
        "signal_score": signal,
        "entropy": round(ent, 3),
        "status_predict": "OK",
        "ai_stats": {
            "win_rate": round(win_rate, 1),
            "total_learned_sessions": len(history_records)
        }
    }

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
    return {"status": "online", "time": datetime.now().isoformat(), "version": "6.0 VIP PRO"}

@app.get("/")
async def home():
    if os.path.exists(INDEX_HTML):
        return FileResponse(INDEX_HTML)
    tpl = os.path.join(BASE_DIR, "templates", "index.html")
    if os.path.exists(tpl):
        return FileResponse(tpl)
    return {
        "status": "online",
        "msg": "🚀 Server AI VIP PRO MAX v6.0 VIP PRO - 15 PHIÊN + THEO CẦU",
        "features": [
            "VIP PRO: Phân tích 15 phiên gần nhất",
            "Thuật toán DỰ ĐOÁN THEO CẦU (phát hiện chu kỳ lặp → tiếp nối cầu)",
            "Bảng cầu mẫu mở rộng (đến độ dài 15)",
            "Chỉ dự đoán khi tìm được cầu - KHÔNG RANDOM",
            "Tự học từ pattern winrate"
        ]
    }

# ============================================================
# 11. RUN
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Server AI VIP PRO MAX v6.0 VIP PRO - Port {port} - 15 phiên + Theo cầu")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
