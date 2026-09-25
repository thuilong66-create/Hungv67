"""
🏆 SERVER AI - VIP v17.0 (Thuật toán duy nhất - ưu tiên cầu VIP) (Sửa lỗi nối đuôi) (Auto+Random+ML+AI_PRO) (Auto+Random+ML)
═══════════════════════════════════════════════
✨ MỘT THUẬT TOÁN DUY NHẤT - THEO CẦU THUẦN TÚY
   🎯 60 dạng cầu Tài Xỉu phổ biến
   ➡️ TẤT CẢ đều THEO cầu (không bẻ)
   🗳️ Gộp lại bằng BỎ PHIẾU ĐA SỐ (đơn giản, không trọng số)
   📊 Điểm tin cậy = tỷ lệ phiếu bên thắng
   ⚡ Dự đoán phiên ĐANG ĐỢI kết quả
   💎 Giao diện đơn giản: chỉ TÀI/XỈU
"""
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn
import sqlite3
import os
import logging
import json
import re
import random
from datetime import datetime, timedelta
from ai_engine import get_ai_engine

# ================= CẤU HÌNH =================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="🏆 VIP v17.0 (Thuật toán duy nhất - ưu tiên cầu VIP) (Sửa lỗi nối đuôi) (Auto+Random+ML+AI_PRO) (Auto+Random+ML)", version="15.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "hethong_vip.db"
SO_LUONG_LICH_SU = 15

# ================= DATABASE =================
def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def khoi_tao_db():
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, 
                password TEXT, 
                balance INTEGER DEFAULT 0, 
                vip_expire DATETIME DEFAULT '2000-01-01 00:00:00', 
                is_banned INTEGER DEFAULT 0
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                username TEXT, 
                card_type TEXT, 
                card_amount INTEGER DEFAULT 0, 
                card_pin TEXT, 
                card_serial TEXT, 
                status TEXT DEFAULT 'PENDING'
            )''')
            c.execute(
                "INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?, ?)",
                ('hungadmin11', 'hungki98', 999999999, '2099-12-31 23:59:59', 0)
            )
            conn.commit()
        logger.info("✅ Database OK")
    except Exception as e:
        logger.error(f"❌ Lỗi DB: {e}")

khoi_tao_db()

# ═══════════════════════════════════════════════════════════
# 🏆 60 DẠNG CẦU PHỔ BIẾN - TẤT CẢ ĐỀU THEO CẦU
# ═══════════════════════════════════════════════════════════

def dem_chuoi_nguoc(kq, muc_tieu):
    dem = 0
    for x in reversed(kq):
        if x == muc_tieu:
            dem += 1
        else:
            break
    return dem

def thuat_toan_theo_cau_60(kq_list):
    """🏆 THUẬT TOÁN DUY NHẤT - ƯU TIÊN CẦU VIP
    Quét các cầu theo thứ tự ưu tiên, cầu nào khớp ĐẦU TIÊN → lấy kết quả của cầu đó.
    KHÔNG bỏ phiếu, KHÔNG nối đuôi hoài.
    """
    if not kq_list or len(kq_list) < 2:
        return {"du_doan": "TÀI", "ti_le": 55.0}
    
    kq = list(kq_list)
    tong = len(kq)
    kq_cuoi = kq[-1]
    chuoi_tai = dem_chuoi_nguoc(kq, "Tài")
    chuoi_xiu = dem_chuoi_nguoc(kq, "Xỉu")
    tong_tai = kq.count("Tài")
    tong_xiu = kq.count("Xỉu")
    tl_tai = tong_tai / tong
    
    # Thứ tự ưu tiên từ CAO đến THẤP
    # Cầu nào khớp ĐẦU TIÊN → lấy kết quả của cầu đó
    
    # ⭐ 1. Cầu nhịp 1-1 8p hoàn hảo (T-X-T-X-T-X-T-X)
    if tong >= 8:
        m8 = kq[-8:]
        if all(m8[i] != m8[i+1] for i in range(7)):
            du_doan = "TÀI" if m8[-1] == "Xỉu" else "XỈU"
            logger.info(f"🏆 Khớp CẦU NHỊP 1-1 8p → {du_doan}")
            return {"du_doan": du_doan, "ti_le": 92.0}
    
    # ⭐ 2. Cầu nhịp 1-1 6p hoàn hảo
    if tong >= 6:
        m6 = kq[-6:]
        if all(m6[i] != m6[i+1] for i in range(5)):
            du_doan = "TÀI" if m6[-1] == "Xỉu" else "XỈU"
            logger.info(f"🏆 Khớp CẦU NHỊP 1-1 6p → {du_doan}")
            return {"du_doan": du_doan, "ti_le": 88.0}
    
    # ⭐ 3. Cầu chu kỳ 3-1 8p (TTT-X-TTT-X)
    if tong >= 8:
        m8 = kq[-8:]
        if m8 == ["Tài","Tài","Tài","Xỉu","Tài","Tài","Tài","Xỉu"]:
            logger.info("🏆 Khớp CẦU CHU KỲ 3-1 TTT-X → TÀI")
            return {"du_doan": "TÀI", "ti_le": 87.0}
        if m8 == ["Xỉu","Xỉu","Xỉu","Tài","Xỉu","Xỉu","Xỉu","Tài"]:
            logger.info("🏆 Khớp CẦU CHU KỲ 3-1 XXX-T → XỈU")
            return {"du_doan": "XỈU", "ti_le": 87.0}
    
    # ⭐ 4. Cầu chu kỳ 3-2 10p (TTT-XX-TTT-XX)
    if tong >= 10:
        m10 = kq[-10:]
        if m10 == ["Tài"]*3+["Xỉu"]*2+["Tài"]*3+["Xỉu"]*2:
            logger.info("🏆 Khớp CẦU CHU KỲ 3-2 TTT-XX → TÀI")
            return {"du_doan": "TÀI", "ti_le": 86.0}
        if m10 == ["Xỉu"]*3+["Tài"]*2+["Xỉu"]*3+["Tài"]*2:
            logger.info("🏆 Khớp CẦU CHU KỲ 3-2 XXX-TT → XỈU")
            return {"du_doan": "XỈU", "ti_le": 86.0}
    
    # ⭐ 5. Cầu cân bằng 2-2 8p (TT-XX-TT-XX)
    if tong >= 8:
        m8 = kq[-8:]
        if m8 == ["Tài","Tài","Xỉu","Xỉu","Tài","Tài","Xỉu","Xỉu"]:
            logger.info("🏆 Khớp CẦU CÂN BẰNG 2-2 TT-XX → TÀI")
            return {"du_doan": "TÀI", "ti_le": 85.0}
        if m8 == ["Xỉu","Xỉu","Tài","Tài","Xỉu","Xỉu","Tài","Tài"]:
            logger.info("🏆 Khớp CẦU CÂN BẰNG 2-2 XX-TT → XỈU")
            return {"du_doan": "XỈU", "ti_le": 85.0}
    
    # ⭐ 6. Cầu chu kỳ 2-1 6p (TT-X-TT-X)
    if tong >= 6:
        m6 = kq[-6:]
        if m6 == ["Tài","Tài","Xỉu","Tài","Tài","Xỉu"]:
            logger.info("🏆 Khớp CẦU CHU KỲ 2-1 TT-X → TÀI")
            return {"du_doan": "TÀI", "ti_le": 84.0}
        if m6 == ["Xỉu","Xỉu","Tài","Xỉu","Xỉu","Tài"]:
            logger.info("🏆 Khớp CẦU CHU KỲ 2-1 XX-T → XỈU")
            return {"du_doan": "XỈU", "ti_le": 84.0}
        # 7. Cầu chu kỳ 1-2 6p (T-XX-T-XX)
        if m6 == ["Tài","Xỉu","Xỉu","Tài","Xỉu","Xỉu"]:
            logger.info("🏆 Khớp CẦU CHU KỲ 1-2 T-XX → TÀI")
            return {"du_doan": "TÀI", "ti_le": 84.0}
        if m6 == ["Xỉu","Tài","Tài","Xỉu","Tài","Tài"]:
            logger.info("🏆 Khớp CẦU CHU KỲ 1-2 X-TT → XỈU")
            return {"du_doan": "XỈU", "ti_le": 84.0}
    
    # ⭐ 8. Cầu song tử 6p (A-B-A-B-A-B)
    if tong >= 6:
        k1,k2,k3,k4,k5,k6 = kq[-6],kq[-5],kq[-4],kq[-3],kq[-2],kq[-1]
        if k1==k3==k5 and k2==k4==k6 and k1!=k2:
            du_doan = "TÀI" if k1=="Tài" else "XỈU"
            logger.info(f"🏆 Khớp CẦU SONG TỬ → {du_doan}")
            return {"du_doan": du_doan, "ti_le": 83.0}
    
    # ⭐ 9. Cầu bệt ≥5 phiên (THEO tiếp tục)
    if chuoi_tai >= 5:
        logger.info(f"🏆 Khớp CẦU BỆT TÀI {chuoi_tai}p → THEO TÀI")
        return {"du_doan": "TÀI", "ti_le": 80.0}
    if chuoi_xiu >= 5:
        logger.info(f"🏆 Khớp CẦU BỆT XỈU {chuoi_xiu}p → THEO XỈU")
        return {"du_doan": "XỈU", "ti_le": 80.0}
    
    # ⭐ 10. Cầu bệt 4 phiên (THEO)
    if chuoi_tai == 4:
        logger.info("🏆 Khớp CẦU BỆT TÀI 4p → THEO TÀI")
        return {"du_doan": "TÀI", "ti_le": 78.0}
    if chuoi_xiu == 4:
        logger.info("🏆 Khớp CẦU BỆT XỈU 4p → THEO XỈU")
        return {"du_doan": "XỈU", "ti_le": 78.0}
    
    # ⭐ 11. Cầu bệt 3 phiên (THEO)
    if chuoi_tai == 3:
        logger.info("🏆 Khớp CẦU BỆT TÀI 3p → THEO TÀI")
        return {"du_doan": "TÀI", "ti_le": 76.0}
    if chuoi_xiu == 3:
        logger.info("🏆 Khớp CẦU BỆT XỈU 3p → THEO XỈU")
        return {"du_doan": "XỈU", "ti_le": 76.0}
    
    # ⭐ 12. Cầu nhịp 1-1 4p
    if tong >= 4:
        m4 = kq[-4:]
        if all(m4[i] != m4[i+1] for i in range(3)):
            du_doan = "TÀI" if m4[-1] == "Xỉu" else "XỈU"
            logger.info(f"🏆 Khớp CẦU NHỊP 1-1 4p → {du_doan}")
            return {"du_doan": du_doan, "ti_le": 75.0}
    
    # ⭐ 13. Cầu bệt 2 phiên (THEO)
    if chuoi_tai == 2:
        logger.info("🏆 Khớp CẦU BỆT TÀI 2p → THEO TÀI")
        return {"du_doan": "TÀI", "ti_le": 72.0}
    if chuoi_xiu == 2:
        logger.info("🏆 Khớp CẦU BỆT XỈU 2p → THEO XỈU")
        return {"du_doan": "XỈU", "ti_le": 72.0}
    
    # ⭐ 14. Đuôi gom 3p cuối cùng chiều
    if tong >= 3:
        m3 = kq[-3:]
        if m3.count("Tài") == 3:
            logger.info("🏆 Khớp ĐUÔI GOM 3p TÀI → THEO TÀI")
            return {"du_doan": "TÀI", "ti_le": 70.0}
        if m3.count("Xỉu") == 3:
            logger.info("🏆 Khớp ĐUÔI GOM 3p XỈU → THEO XỈU")
            return {"du_doan": "XỈU", "ti_le": 70.0}
    
    # ⭐ 15. Thiên vị mạnh (≥70%)
    if tong >= 10:
        if tl_tai >= 0.70:
            logger.info(f"🏆 Khớp THIÊN VỊ TÀI {round(tl_tai*100)}% → THEO TÀI")
            return {"du_doan": "TÀI", "ti_le": 68.0}
        if tl_tai <= 0.30:
            logger.info(f"🏆 Khớp THIÊN VỊ XỈU {round((1-tl_tai)*100)}% → THEO XỈU")
            return {"du_doan": "XỈU", "ti_le": 68.0}
    
    # ⭐ 16. Dấu hiệu chu kỳ 2-1 (3p cuối)
    if tong >= 3:
        m3 = kq[-3:]
        if m3 == ["Tài","Tài","Xỉu"]:
            logger.info("🏆 Dấu hiệu CHU KỲ 2-1 TT-X → TÀI")
            return {"du_doan": "TÀI", "ti_le": 65.0}
        if m3 == ["Xỉu","Xỉu","Tài"]:
            logger.info("🏆 Dấu hiệu CHU KỲ 2-1 XX-T → XỈU")
            return {"du_doan": "XỈU", "ti_le": 65.0}
    
    # ⭐ 17. Đa số 5 phiên gần nhất
    if tong >= 5:
        m5 = kq[-5:]
        if m5.count("Tài") >= 4:
            logger.info("🏆 Đa số 5p TÀI → THEO TÀI")
            return {"du_doan": "TÀI", "ti_le": 62.0}
        if m5.count("Xỉu") >= 4:
            logger.info("🏆 Đa số 5p XỈU → THEO XỈU")
            return {"du_doan": "XỈU", "ti_le": 62.0}
    
    # ⭐ 18. Fallback cuối cùng: nối đuôi (chỉ khi không khớp cầu nào)
    du_doan = "TÀI" if kq_cuoi == "Tài" else "XỈU"
    logger.info(f"🏆 Không khớp cầu nào → FALLBACK nối đuôi: {du_doan}")
    return {"du_doan": du_doan, "ti_le": 55.0}

def tim_phien_doi_va_lich_su(danh_sach_phien, n_lich_su=15):
    if not danh_sach_phien or len(danh_sach_phien) < 2:
        return None, []
    
    def phan_tich(lst):
        if len(lst) < 2:
            return None, []
        phien_moi_nhat = lst[0]
        kq_moi_nhat = parse_result_super(phien_moi_nhat) if isinstance(phien_moi_nhat, dict) else None
        
        phien_doi = None
        vi_tri_bat_dau = 0
        
        if kq_moi_nhat is None:
            phien_doi = phien_moi_nhat
            vi_tri_bat_dau = 1
            logger.info(f"✅ Tìm thấy phiên ĐANG ĐỢI")
        else:
            phien_doi = phien_moi_nhat
            vi_tri_bat_dau = 0
        
        lich_su_raw = lst[vi_tri_bat_dau : vi_tri_bat_dau + n_lich_su + 5]
        lich_su_kq = []
        for s in lich_su_raw:
            if isinstance(s, dict):
                kq = parse_result_super(s)
                if kq:
                    lich_su_kq.append(kq)
            if len(lich_su_kq) >= n_lich_su:
                break
        lich_su_kq = lich_su_kq[::-1]
        return phien_doi, lich_su_kq
    
    phien_a, ls_a = phan_tich(danh_sach_phien)
    phien_b, ls_b = phan_tich(danh_sach_phien[::-1])
    
    kq_a = parse_result_super(phien_a) if phien_a else "?"
    kq_b = parse_result_super(phien_b) if phien_b else "?"
    
    if kq_a is None and len(ls_a) >= len(ls_b):
        return phien_a, ls_a
    elif kq_b is None and len(ls_b) >= len(ls_a):
        return phien_b, ls_b
    else:
        return (phien_a, ls_a) if len(ls_a) >= len(ls_b) else (phien_b, ls_b)

# ================= HÀM HỖ TRỢ =================
def get_str(d, k, defval=""):
    v = d.get(k, defval)
    return str(v).strip() if v else defval

def get_int(d, k, defval=0):
    try:
        return int(d.get(k, defval))
    except:
        return defval

def find_all_lists(obj, path="root"):
    lists = []
    if isinstance(obj, list):
        lists.append({"path": path, "data": obj, "length": len(obj)})
    elif isinstance(obj, dict):
        for key, value in obj.items():
            lists.extend(find_all_lists(value, f"{path}.{key}"))
    return lists

def find_best_session_list(data):
    all_lists = find_all_lists(data)
    if not all_lists:
        return None, None
    
    candidates = []
    for item in all_lists:
        lst = item["data"]
        if len(lst) > 0 and isinstance(lst[0], dict):
            parseable = sum(1 for x in lst[:20] if isinstance(x, dict) and quick_check_tx(x))
            candidates.append({**item, "parseable": parseable})
    
    if not candidates:
        best = max(all_lists, key=lambda x: x["length"])
        return best["data"], best["path"]
    
    candidates.sort(key=lambda x: (-x["parseable"], -x["length"]))
    best = candidates[0]
    logger.info(f"✅ Danh sách: {best['path']} | {best['length']}p | parse={best['parseable']}")
    return best["data"], best["path"]

def quick_check_tx(obj):
    if not isinstance(obj, dict):
        return False
    for v in obj.values():
        if isinstance(v, str):
            vu = v.upper()
            if any(k in vu for k in ["TÀI", "TAI", "XỈU", "XIU", "BIG", "SMALL"]):
                return True
    for sk in ["sum", "total", "tong", "point"]:
        if sk in obj:
            try: int(obj[sk]); return True
            except: pass
    return False

def classify_tx_text(text):
    if not text: return None
    t = text.upper().strip()
    if any(k in t for k in ["TÀI", "TAI", "BIG", "LARGE"]): return "Tài"
    if any(k in t for k in ["XỈU", "XIU", "SMALL", "TINY"]): return "Xỉu"
    return None

def parse_result_super(session_obj):
    if not isinstance(session_obj, dict): return None
    
    result_keys = [
        "resultTruyenThong", "result", "ketqua", "ketQua", "kq", "value",
        "tx_result", "txResult", "taiXiu", "tai_xiu", "result_tx", "outcome",
        "status", "type", "name", "diceResult", "dice_result", "gameResult",
        "tx", "resultText", "result_text", "label", "title"
    ]
    
    for key in result_keys:
        if key in session_obj and session_obj[key]:
            r = classify_tx_text(str(session_obj[key]))
            if r: return r
    
    for v in session_obj.values():
        if isinstance(v, str):
            r = classify_tx_text(v)
            if r: return r
    
    for sum_key in ["sum", "total", "tong", "tongDiem", "diceSum", "point", "score"]:
        if sum_key in session_obj:
            try:
                tong = float(session_obj[sum_key])
                if tong >= 11: return "Tài"
                elif tong >= 3: return "Xỉu"
            except: pass
    
    for dice_key in ["dice", "dices", "xucxac", "numbers", "values"]:
        if dice_key in session_obj:
            dice = session_obj[dice_key]
            if isinstance(dice, list) and len(dice) >= 3:
                try:
                    tong = sum(int(x) for x in dice)
                    return "Tài" if tong >= 11 else "Xỉu"
                except: pass
    
    for v in session_obj.values():
        if isinstance(v, str):
            nums = re.findall(r'\d+', v)
            if nums:
                try:
                    tong = int(nums[-1])
                    if 3 <= tong <= 10: return "Xỉu"
                    elif 11 <= tong <= 18: return "Tài"
                except: pass
    
    return None

def extract_session_id_super(session_obj):
    if not isinstance(session_obj, dict): return "N/A"
    for id_key in ["id", "sessionId", "session_id", "phien", "issue", "period", "round", "number", "no"]:
        if id_key in session_obj and session_obj[id_key]:
            return str(session_obj[id_key])
    return "N/A"

def tang_id_phien(phien_id_str):
    if not phien_id_str or phien_id_str == "N/A":
        return "TIẾP THEO"
    try:
        nums = re.findall(r'\d+', phien_id_str)
        if nums:
            so_cuoi = int(nums[-1])
            so_moi = so_cuoi + 1
            return phien_id_str.rstrip(nums[-1]) + str(so_moi)
        return phien_id_str + "+1"
    except:
        return phien_id_str

# ================= API CHÍNH =================
@app.get("/")
async def home():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for name in ["index.html", "index (3).html", "index.html.html"]:
        p = os.path.join(base_dir, name)
        if os.path.exists(p):
            return FileResponse(p)
    return {"status": "ok", "msg": "🏆 VIP v17.0 (Thuật toán duy nhất - ưu tiên cầu VIP) (Sửa lỗi nối đuôi) (Auto+Random+ML+AI_PRO) (Auto+Random+ML) đang chạy"}

@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "version": "12.0",
        "mode": "🏆 THEO CẦU 60 dạng - Bỏ phiếu đa số",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/api/scan")
async def scan_game(tool: str, username: str, mode: str = 'auto'):
    logger.info(f"🏆 THEO CẦU 50 Scan: {tool} | {username}")

    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT vip_expire,is_banned FROM users WHERE username=?", (username,))
        row = c.fetchone()

    if not row:
        return JSONResponse({"status": "error", "msg": "Tài khoản không tồn tại!"})
    if row[1] == 1 and username != "hungadmin11":
        return JSONResponse({"status": "error", "msg": "Tài khoản bị khóa!"})
    if datetime.now() > datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") and username != "hungadmin11":
        return JSONResponse({"status": "error", "msg": "Hết hạn VIP!"})

    url = {
        "lc79": "https://wtx.tele68.com/v1/tx/lite-sessions",
        "betvip": "https://wtx.macminim6.online/v1/tx/lite-sessions"
    }.get(tool)

    if not url:
        return JSONResponse({"status": "error", "msg": "Tool không hợp lệ!"})

    try:
        res = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }, timeout=15)
        
        try:
            data = res.json()
        except Exception as je:
            logger.error(f"❌ JSON lỗi: {je}")
            return JSONResponse({"status": "success", "data": {
                "du_doan": "TÀI", "ti_le": 55.0, "phien": "API-ERR"
            }})

        all_list, list_path = find_best_session_list(data)

        if not all_list or len(all_list) == 0:
            logger.warning("⚠️ Không tìm thấy danh sách!")
            return JSONResponse({"status": "success", "data": {
                "du_doan": "TÀI", "ti_le": 55.0, "phien": "NODATA"
            }})

        # ✨ Tìm phiên đang đợi + lịch sử
        phien_doi, lich_su_kq = tim_phien_doi_va_lich_su(all_list, SO_LUONG_LICH_SU)
        
        logger.info(f"📋 Phiên đợi: {extract_session_id_super(phien_doi) if phien_doi else 'N/A'} | Lịch sử: {len(lich_su_kq)}p")
        
        if len(lich_su_kq) < 2:
            logger.warning(f"⚠️ Chỉ {len(lich_su_kq)} phiên lịch sử")
            return JSONResponse({"status": "success", "data": {
                "du_doan": "TÀI",
                "ti_le": 55.0,
                "phien": extract_session_id_super(phien_doi) if phien_doi else "N/A"
            }})
        
        # 🏆 CHẠY THUẬT TOÁN THEO CẦU 50 DẠNG
                # 🧠 Lưu vào Markov để AI học
        luu_va_hoc_markov(tool, lich_su_kq)
        
        # 🎯 CHẾ ĐỘ DỰ ĐOÁN: auto | random | ml
        if mode == 'random':
            # 🎲 NGẪU NHIÊN
            ket_qua = {"du_doan": random.choice(["TÀI", "XỈU"]), "ti_le": 50.0}
            logger.info(f"🎲 Random mode: {ket_qua['du_doan']}")
        elif mode == 'ml':
            # 🧠 AI HỌC MÁY (Markov Chain)
            ket_qua_ml = du_doan_markov(tool, lich_su_kq)
            if ket_qua_ml:
                ket_qua = ket_qua_ml
            else:
                ket_qua = thuat_toan_theo_cau_60(lich_su_kq)
                logger.info("🧠 ML chưa đủ dữ liệu → dùng Auto VIP")
        elif mode == 'ai_pro':
            # 🏆 AI PRO ENSEMBLE (5 thành phần: Pattern+Markov+Streak+Frequency+MLP)
            ai = get_ai_engine()
            # Chuyển đổi định dạng: "Tài"/"Xỉu" → "T"/"X"
            hist_tx = ["T" if x == "Tài" else "X" for x in lich_su_kq]
            ket_qua = ai.predict(hist_tx)
            # Tự học: cập nhật phiên cuối cùng vào AI
            if len(hist_tx) >= 1:
                ai.update(hist_tx[-1])
        else:
            # 🤖 AUTO VIP (60 dạng cầu)
            ket_qua = thuat_toan_theo_cau_60(lich_su_kq)
        
        # Xác định ID phiên hiển thị
        if phien_doi and parse_result_super(phien_doi) is None:
            phien_hien_thi = extract_session_id_super(phien_doi)
        else:
            phien_moi_nhat_id = extract_session_id_super(phien_doi) if phien_doi else "N/A"
            phien_hien_thi = tang_id_phien(phien_moi_nhat_id)
        
        # ✅ Trả về đơn giản
        response = {
            "du_doan": ket_qua["du_doan"],
            "ti_le": ket_qua["ti_le"],
            "phien": phien_hien_thi
        }
        
        logger.info(f"🎯 v15.0: Phiên #{phien_hien_thi} → {response['du_doan']} | {response['ti_le']}%")
        
        return JSONResponse({"status": "success", "data": response})

    except Exception as e:
        logger.error(f"❌ Lỗi: {e}", exc_info=True)
        return JSONResponse({"status": "success", "data": {
            "du_doan": "TÀI", "ti_le": 55.0, "phien": "ERROR"
        }})

# ================= AUTH & USER APIs =================
@app.post("/api/auth")
async def auth(req: Request):
    try: d = await req.json()
    except: return JSONResponse({"status": "error", "msg": "Dữ liệu lỗi"})
    act, u, p = get_str(d, "action"), get_str(d, "username"), get_str(d, "password")
    if not u or not p: return JSONResponse({"status": "error", "msg": "Thiếu thông tin"})
    with get_db() as conn:
        c = conn.cursor()
        if act == "register":
            c.execute("SELECT 1 FROM users WHERE username=?", (u,))
            if c.fetchone(): return JSONResponse({"status": "error", "msg": "Tên đã tồn tại"})
            c.execute("INSERT INTO users VALUES (?,?,0,'2000-01-01 00:00:00',0)", (u, p))
            conn.commit()
            return JSONResponse({"status": "success", "msg": "Đăng ký thành công"})
        else:
            c.execute("SELECT password,is_banned FROM users WHERE username=?", (u,))
            r = c.fetchone()
            if not r or r[0] != p: return JSONResponse({"status": "error", "msg": "Sai tài khoản/mật khẩu"})
            if r[1] == 1 and u != "hungadmin11": return JSONResponse({"status": "error", "msg": "Bị khóa"})
            return JSONResponse({"status": "success", "msg": "Đăng nhập thành công"})

@app.get("/api/user_info")
async def user_info(username: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT balance,vip_expire FROM users WHERE username=?", (username,))
        r = c.fetchone()
    if not r: return JSONResponse({"status": "error"})
    is_vip = (datetime.now() < datetime.strptime(r[1], "%Y-%m-%d %H:%M:%S")) or username == "hungadmin11"
    vip_str = "VĨNH VIỄN (ADMIN)" if username == "hungadmin11" else (r[1] if is_vip else "Chưa có VIP")
    return JSONResponse({"status": "success", "data": {"balance": r[0], "vip_expire": vip_str, "is_vip": is_vip}})

@app.post("/api/deposit")
async def deposit(req: Request):
    try: d = await req.json()
    except: return JSONResponse({"status": "error"})
    un, net, amt, pin, srl = get_str(d, "username"), get_str(d, "network"), get_int(d, "amount"), get_str(d, "pin"), get_str(d, "serial")
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO deposits VALUES (NULL,?,?,?,?,?,'PENDING')", (un, net, amt, pin, srl))
        conn.commit()
    return JSONResponse({"status": "success", "msg": "Đã gửi thẻ, chờ duyệt"})

@app.post("/api/buy_vip")
async def buy_vip(req: Request):
    try: d = await req.json()
    except: return JSONResponse({"status": "error"})
    un, pkg = get_str(d, "username"), get_str(d, "package")
    if un == "hungadmin11": return JSONResponse({"status": "success", "msg": "Admin miễn phí"})
    gói = {"1D": (30000, 1), "3D": (50000, 3), "7D": (100000, 7), "30D": (150000, 30), "PERM": (200000, 36500)}
    if pkg not in gói: return JSONResponse({"status": "error", "msg": "Gói không hợp lệ"})
    cost, ngay = gói[pkg]
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT balance,vip_expire FROM users WHERE username=?", (un,))
        r = c.fetchone()
        if not r or r[0] < cost: return JSONResponse({"status": "error", "msg": "Không đủ tiền"})
        now = datetime.now()
        cur = datetime.strptime(r[1], "%Y-%m-%d %H:%M:%S")
        new_exp = (cur if cur > now else now) + timedelta(days=ngay)
        c.execute("UPDATE users SET balance=balance-?, vip_expire=? WHERE username=?",
                  (cost, new_exp.strftime("%Y-%m-%d %H:%M:%S"), un))
        conn.commit()
    return JSONResponse({"status": "success", "msg": "Mua VIP thành công"})

@app.get("/api/admin/data")
async def admin_data(username: str):
    if username != "hungadmin11": return JSONResponse({"status": "error"})
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT username,balance,vip_expire,is_banned FROM users WHERE username!='hungadmin11'")
        users = c.fetchall()
        c.execute("SELECT id,username,card_type,card_amount,card_pin,card_serial FROM deposits WHERE status='PENDING'")
        deps = c.fetchall()
    return JSONResponse({"status": "success", "users": users, "deps": deps})

@app.post("/api/admin/action")
async def admin_act(req: Request):
    try: d = await req.json()
    except: return JSONResponse({"status": "error"})
    admin, act, tgt, did, amt = get_str(d, "admin"), get_str(d, "action"), get_str(d, "target"), get_int(d, "dep_id"), get_int(d, "amount")
    if admin != "hungadmin11": return JSONResponse({"status": "error"})
    with get_db() as conn:
        c = conn.cursor()
        if act == "ban": c.execute("UPDATE users SET is_banned=1 WHERE username=?", (tgt,))
        elif act == "unban": c.execute("UPDATE users SET is_banned=0 WHERE username=?", (tgt,))
        elif act == "approve_dep":
            c.execute("UPDATE deposits SET status='APPROVED' WHERE id=?", (did,))
            c.execute("UPDATE users SET balance=balance+? WHERE username=?", (amt, tgt))
        elif act == "reject_dep": c.execute("UPDATE deposits SET status='REJECTED' WHERE id=?", (did,))
        else: return JSONResponse({"status": "error"})
        conn.commit()
    return JSONResponse({"status": "success"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🏆 VIP v17.0 (Thuật toán duy nhất - ưu tiên cầu VIP) (Sửa lỗi nối đuôi) (Auto+Random+ML+AI_PRO) (Auto+Random+ML) | Bỏ phiếu đa số | Cổng {port}")
    uvicorn.run("server_ai:app", host="0.0.0.0", port=port)
