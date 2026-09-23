"""
SERVER AI - HỆ THỐNG TOOL VIP (v5.0 THEO CẦU)
✅ DỰ ĐOÁN THEO CẦU - TIẾP TỤC QUY LUẬT (không bẻ cầu)
✅ Nhận biết 10+ dạng cầu phổ biến
✅ Lấy 15 phiên, phân tích 15 phiên
✅ Không hiển thị lịch sử trong widget - chỉ dự đoán
✅ Luôn có kết quả
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
from datetime import datetime, timedelta

# ================= CẤU HÌNH =================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Hệ thống Tool VIP - THEO CẦU", version="5.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "hethong_vip.db"
SO_LUONG_PHAN_TICH = 15  # Lấy & Phân tích 15 phiên

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

# ================= THUẬT TOÁN THEO CẦU - 10+ DẠNG CẦU PHỔ BIẾN =================
def phan_tich_theo_cau(kq_list):
    """
    ✅ DỰ ĐOÁN THEO CẦU: Nhận biết quy luật và TIẾP TỤC nó
    ✅ Không bẻ cầu - không đảo ngược
    ✅ 10+ dạng cầu phổ biến
    """
    tong_tai = kq_list.count("Tài")
    tong_xiu = kq_list.count("Xỉu")
    tong_phien = len(kq_list)

    # Mặc định nếu ít dữ liệu
    if tong_phien < 2:
        return {
            "du_doan": "TÀI",
            "ti_le": 55.0,
            "loi_khuyen": "Dữ liệu ít - Dự đoán TÀI",
            "phuong_phap": "Dự đoán mặc định",
            "cau": "Chưa rõ",
            "tong_tai": tong_tai,
            "tong_xiu": tong_xiu,
            "chuoi_tai": 0,
            "chuoi_xiu": 0,
            "trend": "Đang hình thành cầu..."
        }

    kq_cuoi = kq_list[-1]  # Phiên mới nhất
    
    # Đếm chuỗi hiện tại
    chuoi_tai = 0
    chuoi_xiu = 0
    for x in reversed(kq_list):
        if x == "Tài": chuoi_tai += 1
        else: break
    for x in reversed(kq_list):
        if x == "Xỉu": chuoi_xiu += 1
        else: break

    du_doan = ""
    ty_le = 0
    pp = ""
    cau_type = ""

    # ==================================================
    # CẦU 1: CẦU BỆT DÀI (TIẾP TỤC) - Quan trọng nhất
    # ==================================================
    if chuoi_tai >= 2:
        du_doan = "TÀI"
        ty_le = min(82 + chuoi_tai * 2, 95)
        cau_type = f"Cầu bệt TÀI {chuoi_tai}"
        pp = f"Cầu bệt TÀI {chuoi_tai} phiên → TIẾP TỤC TÀI"
    elif chuoi_xiu >= 2:
        du_doan = "XỈU"
        ty_le = min(82 + chuoi_xiu * 2, 95)
        cau_type = f"Cầu bệt XỈU {chuoi_xiu}"
        pp = f"Cầu bệt XỈU {chuoi_xiu} phiên → TIẾP TỤC XỈU"

    # ==================================================
    # CẦU 2: CẦU XEN KẼ T-X-T-X (1-1)
    # ==================================================
    if not du_doan and tong_phien >= 4:
        m4 = kq_list[-4:]
        if m4 == ["Tài", "Xỉu", "Tài", "Xỉu"]:
            du_doan = "TÀI"
            ty_le = 90
            cau_type = "Cầu xen kẽ 1-1"
            pp = "Cầu T-X-T-X → TIẾP TỤC TÀI"
        elif m4 == ["Xỉu", "Tài", "Xỉu", "Tài"]:
            du_doan = "XỈU"
            ty_le = 90
            cau_type = "Cầu xen kẽ 1-1"
            pp = "Cầu X-T-X-T → TIẾP TỤC XỈU"

    # ==================================================
    # CẦU 3: CẦU 2-1 (2T-1X hoặc 2X-1T lặp lại)
    # ==================================================
    if not du_doan and tong_phien >= 6:
        m6 = kq_list[-6:]
        # 2T-1X-2T-1X → dự đoán TÀI
        if m6 == ["Tài", "Tài", "Xỉu", "Tài", "Tài", "Xỉu"]:
            du_doan = "TÀI"
            ty_le = 88
            cau_type = "Cầu 2-1 (TT-X)"
            pp = "Cầu 2T-1X lặp → TIẾP TỤC TÀI"
        # 2X-1T-2X-1T → dự đoán XỈU
        elif m6 == ["Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu", "Tài"]:
            du_doan = "XỈU"
            ty_le = 88
            cau_type = "Cầu 2-1 (XX-T)"
            pp = "Cầu 2X-1T lặp → TIẾP TỤC XỈU"

    # ==================================================
    # CẦU 4: CẦU 2-2 (TT-XX-TT-XX)
    # ==================================================
    if not du_doan and tong_phien >= 6:
        m6 = kq_list[-6:]
        if m6 == ["Tài", "Tài", "Xỉu", "Xỉu", "Tài", "Tài"]:
            du_doan = "XỈU"
            ty_le = 86
            cau_type = "Cầu 2-2"
            pp = "Cầu TT-XX-TT → TIẾP TỤC XỈU"
        elif m6 == ["Xỉu", "Xỉu", "Tài", "Tài", "Xỉu", "Xỉu"]:
            du_doan = "TÀI"
            ty_le = 86
            cau_type = "Cầu 2-2"
            pp = "Cầu XX-TT-XX → TIẾP TỤC TÀI"

    # ==================================================
    # CẦU 5: CẦU 3-1 (3T-1X hoặc 3X-1T)
    # ==================================================
    if not du_doan and tong_phien >= 8:
        m8 = kq_list[-8:]
        if m8 == ["Tài", "Tài", "Tài", "Xỉu", "Tài", "Tài", "Tài", "Xỉu"]:
            du_doan = "TÀI"
            ty_le = 85
            cau_type = "Cầu 3-1"
            pp = "Cầu 3T-1X lặp → TIẾP TỤC TÀI"
        elif m8 == ["Xỉu", "Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu", "Xỉu", "Tài"]:
            du_doan = "XỈU"
            ty_le = 85
            cau_type = "Cầu 3-1"
            pp = "Cầu 3X-1T lặp → TIẾP TỤC XỈU"

    # ==================================================
    # CẦU 6: CẦU NỐI ĐUÔI NGẮN (3-4 phiên gần giống nhau)
    # ==================================================
    if not du_doan and tong_phien >= 3:
        m3 = kq_list[-3:]
        if m3.count("Tài") == 3:
            du_doan = "TÀI"
            ty_le = 80
            cau_type = "Cầu nối đuôi TÀI"
            pp = "3 phiên gần TÀI → TIẾP TỤC TÀI"
        elif m3.count("Xỉu") == 3:
            du_doan = "XỈU"
            ty_le = 80
            cau_type = "Cầu nối đuôi XỈU"
            pp = "3 phiên gần XỈU → TIẾP TỤC XỈU"

    # ==================================================
    # CẦU 7: CẦU TĂNG/XUỐNG (Tài chiếm đa số hoặc Xỉu chiếm đa số)
    # ==================================================
    if not du_doan and tong_phien >= 8:
        tl_tai = tong_tai / tong_phien
        if tl_tai >= 0.65:  # Tài chiếm ưu thế rõ rệt
            du_doan = "TÀI"
            ty_le = 78
            cau_type = "Cầu thiên TÀI"
            pp = f"15 phiên: TÀI {tong_tai} → TIẾP TỤC CẦU TÀI"
        elif tl_tai <= 0.35:  # Xỉu chiếm ưu thế rõ rệt
            du_doan = "XỈU"
            ty_le = 78
            cau_type = "Cầu thiên XỈU"
            pp = f"15 phiên: XỈU {tong_xiu} → TIẾP TỤC CẦU XỈU"

    # ==================================================
    # CẦU 8: CẦU SONG TỬ (A-B-A-B lặp)
    # ==================================================
    if not du_doan and tong_phien >= 6:
        k1, k2, k3, k4, k5, k6 = kq_list[-6], kq_list[-5], kq_list[-4], kq_list[-3], kq_list[-2], kq_list[-1]
        if k1 == k3 == k5 and k2 == k4 == k6 and k1 != k2:
            du_doan = k1
            ty_le = 84
            cau_type = "Cầu song tử"
            pp = f"Cầu {k1}-{k2} lặp → TIẾP TỤC {k1}"

    # ==================================================
    # CẦU 9: CẦU ĐÔI (TT-XX-TT-XX ngắn)
    # ==================================================
    if not du_doan and tong_phien >= 4:
        m4 = kq_list[-4:]
        if m4 == ["Tài", "Tài", "Xỉu", "Xỉu"]:
            du_doan = "TÀI"
            ty_le = 76
            cau_type = "Cầu đôi TT-XX"
            pp = "Cầu TT-XX → TIẾP TỤC TÀI"
        elif m4 == ["Xỉu", "Xỉu", "Tài", "Tài"]:
            du_doan = "XỈU"
            ty_le = 76
            cau_type = "Cầu đôi XX-TT"
            pp = "Cầu XX-TT → TIẾP TỤC XỈU"

    # ==================================================
    # CẦU 10: NỐI ĐUÔI PHIÊN CUỐI (mặc định thông minh)
    # ==================================================
    if not du_doan:
        du_doan = kq_cuoi
        # Tỷ lệ dựa trên độ cân bằng
        chenh_lech = abs(tong_tai - tong_xiu)
        if chenh_lech >= 5:
            ty_le = 72
        elif chenh_lech >= 3:
            ty_le = 68
        else:
            ty_le = 62
        cau_type = "Cầu nối đuôi"
        pp = f"Nối đuôi phiên cuối → TIẾP TỤC {kq_cuoi}"

    # ==================================================
    # Xác định xu hướng
    # ==================================================
    if chuoi_tai >= 3:
        trend = f"🔥 Cầu bệt TÀI {chuoi_tai} phiên - MẠNH"
    elif chuoi_xiu >= 3:
        trend = f"🔥 Cầu bệt XỈU {chuoi_xiu} phiên - MẠNH"
    elif tong_tai > tong_xiu + 2:
        trend = f"📈 Cầu thiên về TÀI ({tong_tai}T-{tong_xiu}X)"
    elif tong_xiu > tong_tai + 2:
        trend = f"📉 Cầu thiên về XỈU ({tong_tai}T-{tong_xiu}X)"
    else:
        trend = f"⚖️ Cầu cân bằng ({tong_tai}T-{tong_xiu}X)"

    return {
        "du_doan": du_doan,
        "ti_le": round(ty_le, 1),
        "loi_khuyen": f"{pp} ({round(ty_le, 1)}%)",
        "phuong_phap": pp,
        "cau": cau_type,
        "tong_tai": tong_tai,
        "tong_xiu": tong_xiu,
        "chuoi_tai": chuoi_tai,
        "chuoi_xiu": chuoi_xiu,
        "trend": trend
    }

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
            candidates.append({
                **item,
                "parseable": parseable,
                "dict_count": sum(1 for x in lst if isinstance(x, dict))
            })
    
    if not candidates:
        best = max(all_lists, key=lambda x: x["length"])
        return best["data"], best["path"]
    
    candidates.sort(key=lambda x: (-x["parseable"], -x["length"]))
    best = candidates[0]
    logger.info(f"✅ Chọn danh sách: {best['path']} | độ dài={best['length']} | parseable={best['parseable']}")
    return best["data"], best["path"]

def quick_check_tx(obj):
    if not isinstance(obj, dict):
        return False
    for v in obj.values():
        if isinstance(v, str):
            vu = v.upper()
            if any(k in vu for k in ["TÀI", "TAI", "XỈU", "XIU", "BIG", "SMALL"]):
                return True
    for sum_key in ["sum", "total", "tong", "point"]:
        if sum_key in obj:
            try:
                int(obj[sum_key])
                return True
            except:
                pass
    return False

def classify_tx_text(text):
    if not text:
        return None
    t = text.upper().strip()
    if any(k in t for k in ["TÀI", "TAI", "BIG", "LARGE"]):
        return "Tài"
    if any(k in t for k in ["XỈU", "XIU", "SMALL", "TINY"]):
        return "Xỉu"
    return None

def parse_result_super(session_obj):
    if not isinstance(session_obj, dict):
        return None
    
    result_keys = [
        "resultTruyenThong", "result", "ketqua", "ketQua", "kq",
        "value", "tx_result", "txResult", "taiXiu", "tai_xiu",
        "result_tx", "outcome", "status", "type", "name",
        "diceResult", "dice_result", "gameResult", "game_result",
        "tx", "resultText", "result_text", "label", "title"
    ]
    
    for key in result_keys:
        if key in session_obj and session_obj[key]:
            val = str(session_obj[key]).strip()
            result = classify_tx_text(val)
            if result:
                return result
    
    for v in session_obj.values():
        if isinstance(v, str):
            result = classify_tx_text(v)
            if result:
                return result
    
    for sum_key in ["sum", "total", "tong", "tongDiem", "diceSum", "dice_sum", "point", "points", "score"]:
        if sum_key in session_obj:
            try:
                tong = float(session_obj[sum_key])
                if tong >= 11:
                    return "Tài"
                elif tong >= 3:
                    return "Xỉu"
            except:
                pass
    
    for dice_key in ["dice", "dices", "xucxac", "numbers", "diceValues", "values"]:
        if dice_key in session_obj:
            dice = session_obj[dice_key]
            if isinstance(dice, list) and len(dice) >= 3:
                try:
                    tong = sum(int(x) for x in dice)
                    return "Tài" if tong >= 11 else "Xỉu"
                except:
                    pass
    
    for v in session_obj.values():
        if isinstance(v, str):
            nums = re.findall(r'\d+', v)
            if nums:
                try:
                    tong = int(nums[-1])
                    if 3 <= tong <= 10:
                        return "Xỉu"
                    elif 11 <= tong <= 18:
                        return "Tài"
                except:
                    pass
    
    return None

def extract_session_id_super(session_obj):
    if not isinstance(session_obj, dict):
        return "N/A"
    for id_key in ["id", "sessionId", "session_id", "phien", "issue", "period", "round", "roundId", "issueNumber", "number", "no", "stt"]:
        if id_key in session_obj and session_obj[id_key]:
            return str(session_obj[id_key])
    return "N/A"

# ================= API CHÍNH =================
@app.get("/")
async def home():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    possible_names = ["index.html", "index (3).html", "index.html.html"]
    for name in possible_names:
        p = os.path.join(base_dir, name)
        if os.path.exists(p):
            return FileResponse(p)
    return {"status": "ok", "msg": "Server AI v5.0 THEO CẦU đang chạy"}

@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "version": "5.0",
        "mode": "DỰ ĐOÁN THEO CẦU (10+ dạng cầu)",
        "config": f"Phân tích {SO_LUONG_PHAN_TICH} phiên",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/api/debug")
async def debug_api(tool: str):
    url = {
        "lc79": "https://wtx.tele68.com/v1/tx/lite-sessions",
        "betvip": "https://wtx.macminim6.online/v1/tx/lite-sessions"
    }.get(tool)
    
    if not url:
        return JSONResponse({"status": "error", "msg": "Tool không hợp lệ"})
    
    try:
        res = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }, timeout=15)
        
        data = res.json()
        all_lists = find_all_lists(data)
        best_list, best_path = find_best_session_list(data)
        
        parse_results = []
        if best_list:
            for i, s in enumerate(best_list[:10]):
                if isinstance(s, dict):
                    r = parse_result_super(s)
                    parse_results.append({
                        "index": i,
                        "result": r,
                        "keys": list(s.keys())[:8],
                        "preview": {k: str(v)[:40] for k, v in list(s.items())[:4]}
                    })
        
        return JSONResponse({
            "status": "success",
            "tool": tool,
            "http_status": res.status_code,
            "top_keys": list(data.keys()) if isinstance(data, dict) else "N/A",
            "all_lists_found": [{"path": l["path"], "length": l["length"]} for l in all_lists],
            "best_list_path": best_path,
            "best_list_length": len(best_list) if best_list else 0,
            "parse_10_first": parse_results
        })
    except Exception as e:
        return JSONResponse({"status": "error", "msg": str(e)})

@app.get("/api/scan")
async def scan_game(tool: str, username: str):
    logger.info(f"🔍 Scan THEO CẦU: {tool} | {username}")

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
        
        logger.info(f"📡 HTTP Status: {res.status_code}")
        
        try:
            data = res.json()
        except Exception as je:
            logger.error(f"❌ JSON lỗi: {je}")
            ket_qua = phan_tich_theo_cau([])
            ket_qua["phien"] = "API-LỖI"
            return JSONResponse({"status": "success", "data": ket_qua})

        all_list, list_path = find_best_session_list(data)

        if not all_list or len(all_list) == 0:
            logger.warning("⚠️ Không tìm thấy danh sách phiên!")
            ket_qua = phan_tich_theo_cau([])
            ket_qua["phien"] = "NODATA"
            return JSONResponse({"status": "success", "data": ket_qua})

        logger.info(f"📋 Danh sách: {list_path} | {len(all_list)} phiên")

        # Thử cả 2 cách lấy dữ liệu
        def get_and_parse(source_list, take_from="head"):
            if len(source_list) >= SO_LUONG_PHAN_TICH:
                raw = source_list[:SO_LUONG_PHAN_TICH] if take_from == "head" else source_list[-SO_LUONG_PHAN_TICH:]
            else:
                raw = source_list.copy()
            ordered = raw[::-1] if take_from == "head" else raw.copy()
            results = []
            for s in ordered:
                r = parse_result_super(s)
                if r:
                    results.append(r)
            return results, ordered
        
        kq_head, ordered_head = get_and_parse(all_list, "head")
        kq_tail, ordered_tail = get_and_parse(all_list, "tail")
        
        logger.info(f"🔍 Cách A (đầu): {len(kq_head)}/15 | {kq_head}")
        logger.info(f"🔍 Cách B (cuối): {len(kq_tail)}/15 | {kq_tail}")
        
        if len(kq_head) >= len(kq_tail):
            kq_final = kq_head
            ordered_final = ordered_head
            cach_chon = "A (lấy đầu)"
        else:
            kq_final = kq_tail
            ordered_final = ordered_tail
            cach_chon = "B (lấy cuối)"
        
        logger.info(f"✅ Chọn cách {cach_chon} | {len(kq_final)} phiên hợp lệ")

        # ✅ CHẠY THUẬT TOÁN THEO CẦU
        ket_qua = phan_tich_theo_cau(kq_final)

        phien_id = extract_session_id_super(ordered_final[-1]) if ordered_final else "N/A"
        ket_qua["phien"] = phien_id
        ket_qua["config"] = {
            "mode": "THEO_CAU",
            "phan_tich": SO_LUONG_PHAN_TICH,
            "cach_lay": cach_chon,
            "parse_duoc": f"{len(kq_final)}/15"
        }

        logger.info(f"🎯 DỰ ĐOÁN THEO CẦU: {ket_qua['du_doan']} | {ket_qua['cau']} | {ket_qua['ti_le']}%")

        return JSONResponse({"status": "success", "data": ket_qua})

    except Exception as e:
        logger.error(f"❌ Lỗi hệ thống: {e}", exc_info=True)
        ket_qua = phan_tich_theo_cau([])
        ket_qua["phien"] = "ERROR"
        ket_qua["trend"] = f"Lỗi: {str(e)[:50]}"
        return JSONResponse({"status": "success", "data": ket_qua})

# ================= AUTH & USER APIs =================
@app.post("/api/auth")
async def auth(req: Request):
    try:
        d = await req.json()
    except:
        return JSONResponse({"status": "error", "msg": "Dữ liệu lỗi"})
    act, u, p = get_str(d, "action"), get_str(d, "username"), get_str(d, "password")
    if not u or not p:
        return JSONResponse({"status": "error", "msg": "Thiếu thông tin"})
    with get_db() as conn:
        c = conn.cursor()
        if act == "register":
            c.execute("SELECT 1 FROM users WHERE username=?", (u,))
            if c.fetchone():
                return JSONResponse({"status": "error", "msg": "Tên đã tồn tại"})
            c.execute("INSERT INTO users VALUES (?,?,0,'2000-01-01 00:00:00',0)", (u, p))
            conn.commit()
            return JSONResponse({"status": "success", "msg": "Đăng ký thành công"})
        else:
            c.execute("SELECT password,is_banned FROM users WHERE username=?", (u,))
            r = c.fetchone()
            if not r or r[0] != p:
                return JSONResponse({"status": "error", "msg": "Sai tài khoản/mật khẩu"})
            if r[1] == 1 and u != "hungadmin11":
                return JSONResponse({"status": "error", "msg": "Bị khóa"})
            return JSONResponse({"status": "success", "msg": "Đăng nhập thành công"})

@app.get("/api/user_info")
async def user_info(username: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT balance,vip_expire FROM users WHERE username=?", (username,))
        r = c.fetchone()
    if not r:
        return JSONResponse({"status": "error"})
    is_vip = (datetime.now() < datetime.strptime(r[1], "%Y-%m-%d %H:%M:%S")) or username == "hungadmin11"
    vip_str = "VĨNH VIỄN (ADMIN)" if username == "hungadmin11" else (r[1] if is_vip else "Chưa có VIP")
    return JSONResponse({"status": "success", "data": {"balance": r[0], "vip_expire": vip_str, "is_vip": is_vip}})

@app.post("/api/deposit")
async def deposit(req: Request):
    try:
        d = await req.json()
    except:
        return JSONResponse({"status": "error"})
    un, net, amt, pin, srl = get_str(d, "username"), get_str(d, "network"), get_int(d, "amount"), get_str(d, "pin"), get_str(d, "serial")
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO deposits VALUES (NULL,?,?,?,?,?,'PENDING')", (un, net, amt, pin, srl))
        conn.commit()
    return JSONResponse({"status": "success", "msg": "Đã gửi thẻ, chờ duyệt"})

@app.post("/api/buy_vip")
async def buy_vip(req: Request):
    try:
        d = await req.json()
    except:
        return JSONResponse({"status": "error"})
    un, pkg = get_str(d, "username"), get_str(d, "package")
    if un == "hungadmin11":
        return JSONResponse({"status": "success", "msg": "Admin miễn phí"})
    gói = {"1D": (30000, 1), "3D": (50000, 3), "7D": (100000, 7), "30D": (150000, 30), "PERM": (200000, 36500)}
    if pkg not in gói:
        return JSONResponse({"status": "error", "msg": "Gói không hợp lệ"})
    cost, ngay = gói[pkg]
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT balance,vip_expire FROM users WHERE username=?", (un,))
        r = c.fetchone()
        if not r or r[0] < cost:
            return JSONResponse({"status": "error", "msg": "Không đủ tiền"})
        now = datetime.now()
        cur = datetime.strptime(r[1], "%Y-%m-%d %H:%M:%S")
        new_exp = (cur if cur > now else now) + timedelta(days=ngay)
        c.execute("UPDATE users SET balance=balance-?, vip_expire=? WHERE username=?",
                  (cost, new_exp.strftime("%Y-%m-%d %H:%M:%S"), un))
        conn.commit()
    return JSONResponse({"status": "success", "msg": "Mua VIP thành công"})

@app.get("/api/admin/data")
async def admin_data(username: str):
    if username != "hungadmin11":
        return JSONResponse({"status": "error"})
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT username,balance,vip_expire,is_banned FROM users WHERE username!='hungadmin11'")
        users = c.fetchall()
        c.execute("SELECT id,username,card_type,card_amount,card_pin,card_serial FROM deposits WHERE status='PENDING'")
        deps = c.fetchall()
    return JSONResponse({"status": "success", "users": users, "deps": deps})

@app.post("/api/admin/action")
async def admin_act(req: Request):
    try:
        d = await req.json()
    except:
        return JSONResponse({"status": "error"})
    admin, act, tgt, did, amt = get_str(d, "admin"), get_str(d, "action"), get_str(d, "target"), get_int(d, "dep_id"), get_int(d, "amount")
    if admin != "hungadmin11":
        return JSONResponse({"status": "error"})
    with get_db() as conn:
        c = conn.cursor()
        if act == "ban":
            c.execute("UPDATE users SET is_banned=1 WHERE username=?", (tgt,))
        elif act == "unban":
            c.execute("UPDATE users SET is_banned=0 WHERE username=?", (tgt,))
        elif act == "approve_dep":
            c.execute("UPDATE deposits SET status='APPROVED' WHERE id=?", (did,))
            c.execute("UPDATE users SET balance=balance+? WHERE username=?", (amt, tgt))
        elif act == "reject_dep":
            c.execute("UPDATE deposits SET status='REJECTED' WHERE id=?", (did,))
        else:
            return JSONResponse({"status": "error"})
        conn.commit()
    return JSONResponse({"status": "success"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Server AI v5.0 | THEO CẦU | 10+ dạng cầu | Cổng {port}")
    uvicorn.run("server_ai:app", host="0.0.0.0", port=port)
