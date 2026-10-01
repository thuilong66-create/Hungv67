# ============================================================
#  SERVER AI VIP PRO MAX - v8.0 VIP PRO
#  15 PHIÊN GẦN NHẤT + 8 LỚP PHÁT HIỆN + 70+ CẦU MẪU + ENSEMBLE
#  Lớp 0: Theo cầu (phát hiện chu kỳ lặp → tiếp nối)   [MỚI]
#  Lớp 1: Đếm liên tiếp        → BỆT + Đảo bệt vừa phá [MỚI]
#  Lớp 2: Chu kỳ đổi cửa       → 1-1 ... 9-9, 5-5-5
#  Lớp 3: Nhịp phức            → 1-2-1, Fibonacci, 3-Phase, Zigzag [MỚI]
#  Lớp 4: Đối xứng             → Palindrome 5/7, Gương 9/11/13/15 [MỚI]
#  Lớp 5: Hồi quy              → 20 tay lệch ≥6
#  Lớp 6: Anti-trap            → 8 đảo liên tiếp = bẫy
#  Lớp 7: Ensemble voting      → Đa thuật toán đồng thuận [MỚI]
#  Nguyên tắc: KHÔNG RANDOM
# ============================================================
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, uvicorn, sqlite3, os, logging, math
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="AI VIP PRO MAX", version="8.0")
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
# 2. HELPER
# ============================================================
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
# 3. HỌC MÁY
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
# 4. ENGINE VIP PRO v8: 15 PHIÊN + 8 LỚP + ENSEMBLE
# ============================================================
WINDOW = 15  # VIP PRO v8: phân tích 15 phiên gần nhất

def _normalize(kq_list):
    out = []
    for x in kq_list:
        s = str(x).strip().upper()
        if s in ("TÀI", "TAI", "T"):
            out.append("T")
        elif s in ("XỈU", "XIỦ", "XIU", "X"):
            out.append("X")
    return out

def _rle(seq):
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
    if len(rle) < len(groups):
        return False
    tail_counts = [cnt for _, cnt in rle[-len(groups):]]
    return tail_counts == groups

def _is_alternating(seq):
    return all(seq[i] != seq[i + 1] for i in range(len(seq) - 1))

def _is_palindrome(seq):
    n = len(seq)
    return all(seq[i] == seq[n - 1 - i] for i in range(n // 2))

# ---------- LỚP 0 MỚI: THEO CẦU (phát hiện chu kỳ lặp) ----------
def _find_cycle(seq, min_len=2, max_len=7):
    n = len(seq)
    best = None
    best_repeats = 0
    for L in range(min_len, max_len + 1):
        if n < L * 2:
            continue
        num_cycles = n // L
        if num_cycles < 2:
            continue
        tail = seq[-(num_cycles * L):]
        cycle = tail[:L]
        ok = all(tail[i] == cycle[i % L] for i in range(len(tail)))
        if ok:
            if num_cycles > best_repeats:
                best_repeats = num_cycles
                best = (L, cycle[0], num_cycles, cycle)
    return best

def _theo_cau_predict(seq):
    if len(seq) < 6:
        return None
    cyc = _find_cycle(seq, 2, 7)
    if not cyc:
        return None
    L, next_char, repeats, cycle = cyc
    if repeats < 2:
        return None
    pred = "TÀI" if next_char == "T" else "XỈU"
    cycle_str = "-".join(cycle)
    if repeats >= 5:
        conf, level = 93.0, "CỰC MẠNH"
    elif repeats >= 4:
        conf, level = 90.0, "RẤT MẠNH"
    elif repeats >= 3:
        conf, level = 87.0, "MẠNH"
    else:
        conf, level = 82.0, "RÕ"
    return {"name": f"THEO_CAU_L{L}_x{repeats}", "prediction": pred, "conf": conf,
            "note": f"🌉 Theo cầu [{cycle_str}] lặp {repeats}x ({level}) → {pred}", "layer": 0}

# ---------- BẢNG CẦU MẪU (mở rộng cho 15 phiên) ----------
# (tên, loại, spec, action, conf, ghi_chú, layer)
PATTERNS = [
    # ===== LỚP 1: BỆT DÀI (bẻ) =====
    ("BET_10+",       "streak", (10, 99), "opp", 95.0, "🐉 Bệt 10+ → Bẻ {opp}", 1),
    ("BET_9",         "streak", (9, 9),   "opp", 94.0, "🐉 Bệt 9 → Bẻ {opp}", 1),
    ("BET_7-8",       "streak", (7, 8),   "opp", 91.0, "🐉 Bệt 7-8 → Bẻ {opp}", 1),
    ("BET_5-6",       "streak", (5, 6),   "opp", 88.0, "⚠️ Bệt 5-6 → Bẻ {opp}", 1),
    # ===== LỚP 2: CHU KỲ ĐỔI CỬA (mở rộng đến 9-9, 5-5-5) =====
    ("CHUKY_9-9",     "groups", [9,9],    "opp", 93.0, "💎 Chu kỳ 9-9 cực hiếm → {opp}", 2),
    ("CHUKY_8-8",     "groups", [8,8],    "opp", 92.0, "💎 Chu kỳ 8-8 → {opp}", 2),
    ("CHUKY_7-7",     "groups", [7,7],    "opp", 92.0, "💎 Chu kỳ 7-7 → {opp}", 2),
    ("CHUKY_6-6",     "groups", [6,6],    "opp", 91.0, "💎 Chu kỳ 6-6 → {opp}", 2),
    ("CHUKY_5-5-5",   "groups", [5,5,5],  "opp", 92.0, "💎 Chu kỳ 5-5-5 (3 tầng) → {opp}", 2),
    ("CHUKY_5-5",     "groups", [5,5],    "opp", 90.0, "💎 Chu kỳ 5-5 → {opp}", 2),
    ("CHUKY_4-4-4",   "groups", [4,4,4],  "opp", 91.0, "💎 Chu kỳ 4-4-4 (3 tầng) → {opp}", 2),
    ("CHUKY_4-4",     "groups", [4,4],    "opp", 89.0, "🎯 Chu kỳ 4-4 → {opp}", 2),
    ("CHUKY_3-3-3",   "groups", [3,3,3],  "opp", 90.0, "💎 Chu kỳ 3-3-3 (3 tầng) → {opp}", 2),
    ("CHUKY_3-3",     "groups", [3,3],    "opp", 89.0, "🎯 Chu kỳ 3-3 → {opp}", 2),
    ("CHUKY_2-2-2-2-2-2","groups",[2,2,2,2,2,2],"opp",90.0,"💎 Chu kỳ 2-2 x6 (hình sin dài) → {opp}", 2),
    ("CHUKY_2-2",     "groups", [2,2,2,2],"opp", 88.0, "🪞 Chu kỳ 2-2 → {opp}", 2),
    ("CHUKY_1-1",     "groups", [1,1,1,1,1,1],"opp",90.0,"⚡ Chu kỳ 1-1 (đảo tay ≥6) → {opp}", 2),
    # ===== LỚP 3: NHỊP PHỨC (mở rộng: Fibonacci, 3-Phase, Zigzag, dài) =====
    ("FIBO_1-1-2-3",  "groups", [1,1,2,3],"opp", 87.0, "🔢 Fibonacci 1-1-2-3 → {opp}", 3),
    ("3PHASE_N-1-1-2-2","groups",[4,1,1,2,2],"opp",88.0,"🔀 3-Phase: Bệt→1-1→2-2 → {opp}", 3),
    ("ZIGZAG_1-1-2-1-1","groups",[1,1,2,1,1],"opp",86.0,"⚡ Zigzag VIP 1-1-2-1-1 → {opp}", 3),
    ("NHIPHUC_3-2-2-3","groups", [3,2,2,3],"opp", 89.0, "📊 Nhịp 3-2-2-3 → {opp}", 3),
    ("NHIPHUC_1-1-2-2-3","groups",[1,1,2,2,3],"opp",86.0,"📊 Nhịp 1-1-2-2-3 → {opp}", 3),
    ("NHIPHUC_2-1-2-1-2","groups",[2,1,2,1,2],"opp",88.0,"🐸 Nhảy cóc 2-1-2-1-2 → {opp}", 3),
    ("NHIPHUC_1-2-1-2-1","groups",[1,2,1,2,1],"opp",88.0,"📊 Nhịp 1-2-1-2-1 → {opp}", 3),
    ("NHIPHUC_3-1-2-2","groups", [3,1,2,2],"opp", 84.0, "📊 Nhịp 3-1-2-2 → {opp}", 3),
    ("NHIPHUC_2-2-1-3","groups", [2,2,1,3],"opp", 85.0, "📊 Nhịp 2-2-1-3 → {opp}", 3),
    ("NHIPHUC_3-2-3-2","groups", [3,2,3,2],"opp", 88.0, "🔁 Vòng lặp 3-2-3-2 → {opp}", 3),
    ("NHIPHUC_1-2-1-3","groups", [1,2,1,3],"opp", 84.0, "📊 Nhịp 1-2-1-3 → {opp}", 3),
    ("NHIPHUC_3-1-1-3","groups", [3,1,1,3],"opp", 90.0, "💎 Nhịp 3-1-1-3 hiếm → {opp}", 3),
    ("NHIPHUC_3-2-3",  "groups", [3,2,3],  "opp", 86.0, "🔁 Vòng lặp 3-2-3 → {opp}", 3),
    ("NHIPHUC_2-3-2",  "groups", [2,3,2],  "opp", 84.0, "🔁 Vòng lặp 2-3-2 → {opp}", 3),
    ("NHIPHUC_3-1-3",  "groups", [3,1,3],  "opp", 91.0, "💎 Nhịp 3-1-3 rất hiếm → {opp}", 3),
    ("NHIPHUC_1-3-1",  "groups", [1,3,1],  "opp", 90.0, "💎 Nhịp 1-3-1 hiếm → {opp}", 3),
    ("NHIPHUC_1-2-3",  "groups", [1,2,3],  "opp", 84.0, "📊 Tam giác 1-2-3 → {opp}", 3),
    ("NHIPHUC_2-1-2",  "groups", [2,1,2],  "opp", 86.0, "📊 Nhịp 2-1-2 → {opp}", 3),
    ("NHIPHUC_1-2-1",  "groups", [1,2,1],  "opp", 85.0, "📊 Nhịp 1-2-1 → {opp}", 3),
    ("NHIPHUC_2-1-1-2","groups", [2,1,1,2],"opp", 87.0, "📊 Nhịp 2-1-1-2 → {opp}", 3),
    ("NHIPHUC_1-2-1-2","groups", [1,2,1,2],"opp", 87.0, "📊 Nhịp 1-2-1-2 → {opp}", 3),
    ("NHIPHUC_1-1-1-2","groups", [1,1,1,2],"opp", 87.0, "📊 Nhịp 1-1-1-2 → {opp}", 3),
    ("NHIPHUC_2-2-1-1","groups", [2,2,1,1],"opp", 88.0, "📊 Nhịp 2-2-1-1 → {opp}", 3),
    ("NHIPHUC_1-1-2-2","groups", [1,1,2,2],"opp", 88.0, "📊 Nhịp 1-1-2-2 → {opp}", 3),
    ("NHIPHUC_1-2-2-1","groups", [1,2,2,1],"opp", 86.0, "🪞 Gương ngược 1-2-2-1 → {opp}", 3),
    ("NHIPHUC_1-1-2",  "groups", [1,1,2],  "opp", 84.0, "📊 Nhịp 1-1-2 → {opp}", 3),
    ("NHIPHUC_1-2-1-1","groups", [1,2,1,1],"opp", 83.0, "📊 Nhịp 1-2-1-1 → {opp}", 3),
    ("NHIPHUC_1-6",    "groups", [1,6],    "opp", 90.0, "⭐ Đảo bệt 1-6 → {opp}", 3),
    ("NHIPHUC_6-1",    "groups", [6,1],    "opp", 90.0, "⭐ Đảo bệt 6-1 → {opp}", 3),
    ("NHIPHUC_1-5",    "groups", [1,5],    "opp", 89.0, "⭐ Đảo bệt 1-5 → {opp}", 3),
    ("NHIPHUC_5-1",    "groups", [5,1],    "opp", 89.0, "⭐ Đảo bệt 5-1 → {opp}", 3),
    ("NHIPHUC_1-4",    "groups", [1,4],    "opp", 85.0, "📊 Đảo bệt 1-4 → {opp}", 3),
    ("NHIPHUC_4-1",    "groups", [4,1],    "opp", 85.0, "📊 Đảo bệt 4-1 → {opp}", 3),
    ("NHIPHUC_1-3",    "groups", [1,3],    "opp", 83.0, "📊 Đảo bệt 1-3 → {opp}", 3),
    ("NHIPHUC_3-1",    "groups", [3,1],    "opp", 83.0, "📊 Đảo bệt 3-1 → {opp}", 3),
    # ===== LỚP 4: ĐỐI XỨNG (mở rộng Gương 13/15) =====
    ("GUONG_15",      "palin", 15, "opp", 90.0, "🪞 Gương 15 đối xứng hoàn hảo → {opp}", 4),
    ("GUONG_13",      "palin", 13, "opp", 89.0, "🪞 Gương 13 đối xứng → {opp}", 4),
    ("GUONG_11",      "palin", 11, "opp", 88.0, "🪞 Gương 11 đối xứng → {opp}", 4),
    ("GUONG_9",       "palin", 9,  "opp", 86.0, "🪞 Gương 9 đối xứng → {opp}", 4),
    ("PALIN_7",       "palin", 7,  "opp", 84.0, "🪞 Palindrome 7 → {opp}", 4),
    ("PALIN_5",       "palin", 5,  "opp", 82.0, "🪞 Palindrome 5 → {opp}", 4),
    # ===== LỚP 1 (thấp): BỆT NGẮN 3-4 → THEO =====
    ("BET_3-4",       "streak", (3, 4), "cont", 82.0, "🔥 Bệt {n} tay ngắn → Theo {cont}", 1),
]

def _collect_matches(seq, rle_full, cont, opp, streak):
    """Quét toàn bộ bảng PATTERNS, thu TẤT CẢ các mẫu khớp (cho Ensemble)."""
    matches = []
    for name, ptype, spec, action, conf, note_tpl, layer in PATTERNS:
        matched = False
        if ptype == "streak":
            lo, hi = spec
            if lo <= streak <= hi:
                matched = True
        elif ptype == "groups":
            if _match_groups(rle_full, spec):
                matched = True
        elif ptype == "palin":
            L = spec
            if len(seq) >= L and _is_palindrome(seq[-L:]):
                matched = True
        if matched:
            pred = cont if action == "cont" else opp
            note = note_tpl.format(opp=opp, cont=cont, n=streak)
            matches.append({"name": name, "prediction": pred, "conf": conf,
                            "note": note, "layer": layer})
    return matches

def tim_thuat_toan_khop(kq_list):
    """
    Engine v8: 15 phiên + 8 lớp + Ensemble.
    Trả về dict {name, prediction, conf, note, layer, matches_count} hoặc None.
    """
    seq = _normalize(kq_list)
    if len(seq) < 3:
        return None
    seq15 = seq[-WINDOW:]
    rle_full = _rle(seq[-20:]) if len(seq) >= 20 else _rle(seq)
    last_char = seq15[-1]
    cont = "TÀI" if last_char == "T" else "XỈU"
    opp = "XỈU" if last_char == "T" else "TÀI"
    streak = rle_full[-1][1] if rle_full else 0

    # ===== LỚP 0: THEO CẦU (ưu tiên CAO NHẤT) =====
    theo = _theo_cau_predict(seq15)
    if theo:
        # Ensemble: kiểm tra xem có pattern nào khác cùng chiều không
        others = _collect_matches(seq, rle_full, cont, opp, streak)
        agree = [m for m in others if m["prediction"] == theo["prediction"]]
        if agree:
            theo["conf"] = min(theo["conf"] + 3, 97)
            theo["note"] += f" | ✅ {len(agree)} thuật toán đồng thuận ({agree[0]['name']}...)"
        theo["matches_count"] = 1 + len(others)
        return theo

    # ===== LỚP 6 (KIỂM TRA SỚM): ANTI-TRAP - 8 đảo liên tiếp = BẪY =====
    seq8 = seq[-8:]
    if len(seq8) >= 8 and _is_alternating(seq8):
        return {"name": "ANTI_TRAP_8DAO", "prediction": cont, "conf": 87.0,
                "note": f"🪤 Anti-trap: 8 tay đảo liên tiếp là bẫy → Bẻ đảo, theo {cont}",
                "layer": 6, "matches_count": 1}

    # ===== LỚP 1 MỚI: ĐẢO BỆT VỪA PHÁ (bệt dài vừa bị đảo 1 tay) =====
    # RLE đuôi: [..., N>=4, 1] → bệt N vừa bị phá 1 tay → cửa mới (cuối) có khả năng tiếp tục
    if len(rle_full) >= 2 and rle_full[-1][1] == 1 and rle_full[-2][1] >= 4:
        n_bet = rle_full[-2][1]
        return {"name": f"DAO_BET_VUA_PHA_{n_bet}", "prediction": cont, "conf": 85.0,
                "note": f"💥 Bệt {n_bet} vừa bị đảo 1 tay → Cửa mới ({cont}) có xu hướng tiếp tục",
                "layer": 1, "matches_count": 1}

    # ===== Quét tất cả patterns (cho Ensemble Lớp 7) =====
    matches = _collect_matches(seq, rle_full, cont, opp, streak)

    if matches:
        # ===== LỚP 7: ENSEMBLE VOTING =====
        tai_votes = sum(m["conf"] for m in matches if m["prediction"] == "TÀI")
        xiu_votes = sum(m["conf"] for m in matches if m["prediction"] == "XỈU")
        total_w = tai_votes + xiu_votes
        best = matches[0]  # ưu tiên cao nhất (bảng đã sắp xếp)
        if len(matches) >= 2:
            if tai_votes > xiu_votes:
                winner, win_w = "TÀI", tai_votes
            else:
                winner, win_w = "XỈU", xiu_votes
            agree_ratio = win_w / total_w
            agree_names = [m["name"] for m in matches if m["prediction"] == winner]
            if agree_ratio >= 0.7:
                # Đồng thuận mạnh → lấy theo đa số, tăng tin
                top_agree = max((m for m in matches if m["prediction"] == winner), key=lambda m: m["conf"])
                boost = 3 + int(len(agree_names))
                final_conf = min(top_agree["conf"] + boost, 97)
                return {"name": f"ENSEMBLE_{'+'.join(agree_names[:2])}", "prediction": winner,
                        "conf": final_conf,
                        "note": f"🤝 Ensemble: {len(agree_names)}/{len(matches)} thuật toán đồng thuận → {winner} ({', '.join(agree_names[:3])})",
                        "layer": 7, "matches_count": len(matches)}
            elif agree_ratio < 0.55:
                # Xung đột mạnh → hạ tin của best
                best = dict(best)
                best["conf"] = max(best["conf"] - 5, 65)
                best["note"] += f" | ⚠️ Xung đột {len(matches)} thuật toán → Hạ tin"
                best["matches_count"] = len(matches)
                return best
        # Chỉ 1 match hoặc đồng thuận yếu → lấy best
        best = dict(best)
        best["matches_count"] = len(matches)
        return best

    # ===== LỚP 5: HỒI QUY =====
    if len(seq) >= 12:
        lastN = seq[-20:] if len(seq) >= 20 else seq
        tai_n = lastN.count("T")
        xiu_n = len(lastN) - tai_n
        lech = abs(tai_n - xiu_n)
        if lech >= 6:
            minority = "TÀI" if tai_n < xiu_n else "XỈU"
            return {"name": "HOI_QUY_20", "prediction": minority, "conf": 78.0,
                    "note": f"📈 Hồi quy: 20 tay lệch {lech} (T{tai_n}/X{xiu_n}) → Về thiểu số {minority}",
                    "layer": 5, "matches_count": 0}

    return None

def _fallback_predict(kq_list):
    """Markov fallback."""
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
# 5. AI CHÍNH
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

    matched = tim_thuat_toan_khop(kq_list)

    if not matched:
        fb_pred, fb_conf = _fallback_predict(kq_list)
        return {
            "du_doan": fb_pred, "ti_le": fb_conf,
            "loi_khuyen": "⚡ 15 phiên chưa khớp cầu mẫu nào → Dự đoán theo Markov",
            "trend": radar,
            "tong_tai": tong_tai, "tong_xiu": tong_xiu,
            "patterns": [], "signal_score": {"TAI": 0, "XIU": 0},
            "entropy": round(ent, 3),
            "status_predict": "FALLBACK",
            "ai_stats": {"win_rate": round(win_rate, 1), "total_learned_sessions": len(history_records)}
        }

    du_doan = matched["prediction"]
    base_conf = matched["conf"]
    pattern_name = matched["name"]
    layer = matched.get("layer", 0)
    notes = [matched["note"]]

    pattern_wr_db = get_pattern_winrate(pattern_name.split("_")[0] if "_" in pattern_name else pattern_name)
    if pattern_wr_db is not None:
        if pattern_wr_db < 0.40:
            du_doan = "XỈU" if du_doan == "TÀI" else "TÀI"
            base_conf = min(base_conf + 5, 96)
            notes.append(f"🧠 Đảo chiều (cầu này thắng chỉ {int(pattern_wr_db*100)}%)")
        elif pattern_wr_db > 0.70:
            base_conf = min(base_conf + 4, 97)
            notes.append(f"✨ Cầu này mạnh ({int(pattern_wr_db*100)}%)")

    is_theo_cau = pattern_name.startswith("THEO_CAU")
    is_anti_trap = pattern_name.startswith("ANTI_TRAP")
    if not (is_theo_cau or is_anti_trap) and ent > 0.95:
        base_conf = min(base_conf, 78.0)
        notes.append("🌊 Nhiễu cao → Hạ tin")
    elif ent < 0.5:
        base_conf = min(base_conf + 2, 97)
        notes.append("🎯 Xu hướng rõ → Tăng tin")
    elif is_theo_cau and ent > 0.95:
        base_conf = min(base_conf + 1, 97)
        notes.append("🌉 Cầu chu kỳ rõ → Giữ tin")

    final_conf = max(min(base_conf, 98.0), 60.0)

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
        "layer": layer,
        "matches_count": matched.get("matches_count", 0),
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

@app.get("/health")
async def health():
    return {"status": "online", "time": datetime.now().isoformat(), "version": "8.0 VIP PRO (15 phiên - 8 lớp - Ensemble)"}

@app.get("/")
async def home():
    if os.path.exists(INDEX_HTML):
        return FileResponse(INDEX_HTML)
    tpl = os.path.join(BASE_DIR, "templates", "index.html")
    if os.path.exists(tpl):
        return FileResponse(tpl)
    return {
        "status": "online",
        "msg": "🚀 Server AI VIP PRO MAX v8.0 - 15 PHIÊN + 8 LỚP + ENSEMBLE",
        "features": [
            "15 phiên gần nhất",
            "Lớp 0: Theo cầu (chu kỳ lặp → tiếp nối)",
            "Lớp 1: Bệt + Đảo bệt vừa phá",
            "Lớp 2: Chu kỳ 1-1 → 9-9, 5-5-5, 4-4-4, 3-3-3",
            "Lớp 3: Nhịp phức + Fibonacci + 3-Phase + Zigzag",
            "Lớp 4: Đối xứng Palindrome 5/7, Gương 9/11/13/15",
            "Lớp 5: Hồi quy 20 tay",
            "Lớp 6: Anti-trap 8 đảo",
            "Lớp 7: Ensemble voting (đa thuật toán đồng thuận)",
            "Tự học winrate theo từng cầu"
        ]
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Server AI VIP PRO MAX v8.0 - Port {port} - 15 phiên + 8 lớp + Ensemble")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
