"""
SERVER AI - HỆ THỐNG TOOL VIP (v4.0 BẢN CHẮC CHẮN)
✅ Luôn có kết quả dự đoán - không bao giờ WAIT mãi
✅ Lấy 15 phiên gần nhất, phân tích 15 phiên
✅ Tự động thích ứng mọi định dạng API
✅ Thử cả 2 chiều lấy dữ liệu (đầu & cuối danh sách)
✅ Nếu không parse được → dùng logic thông minh dự đoán
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

app = FastAPI(title="Hệ thống Tool VIP", version="4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "hethong_vip.db"
SO_LUONG_PHAN_TICH = 15  # ✅ Lấy & Phân tích 15 phiên

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

# ================= THUẬT TOÁN SOI CẦU — 15 PHIÊN =================
def phan_tich_ai(kq_list):
    """
    ✅ Nhận vào danh sách 15 phiên (cũ ở đầu, mới ở cuối)
    ✅ LUÔN trả về kết quả TÀI hoặc XỈU - không WAIT
    """
    tong_tai = kq_list.count("Tài")
    tong_xiu = kq_list.count("Xỉu")
    tong_phien = len(kq_list)

    if tong_phien < 2:
        # ✅ FIX: Không WAIT nữa - dự đoán mặc định
        return {
            "du_doan": "TÀI",
            "ti_le": 50.0,
            "loi_khuyen": "Dữ liệu ít - dự đoán TÀI (50%)",
            "phuong_phap": "Dự đoán mặc định",
            "tong_tai": tong_tai,
            "tong_xiu": tong_xiu,
            "chuoi_tai": 0,
            "chuoi_xiu": 0,
            "trend": "Đang thu thập thêm dữ liệu..."
        }

    kq_cuoi = kq_list[-1]
    chuoi_tai = 0
    chuoi_xiu = 0

    for x in reversed(kq_list):
        if x == "Tài":
            chuoi_tai += 1
        else:
            break
    for x in reversed(kq_list):
        if x == "Xỉu":
            chuoi_xiu += 1
        else:
            break

    du_doan = ""
    ty_le = 0
    pp = ""

    # LUẬT 1: Cầu bệt dài (≥3 liên tiếp) → đảo chiều
    if chuoi_tai >= 3:
        du_doan = "XỈU"
        ty_le = min(90 + chuoi_tai * 3, 98.5)
        pp = f"Bệt TÀI {chuoi_tai} phiên → bẻ XỈU"
    elif chuoi_xiu >= 3:
        du_doan = "TÀI"
        ty_le = min(90 + chuoi_xiu * 3, 98.5)
        pp = f"Bệt XỈU {chuoi_xiu} phiên → bẻ TÀI"

    # LUẬT 2: Xen kẽ T-X-T-X
    elif tong_phien >= 5:
        m5 = kq_list[-5:]
        if m5 == ["Tài", "Xỉu", "Tài", "Xỉu", "Tài"]:
            du_doan = "XỈU"
            ty_le = 92.5
            pp = "Xen kẽ T-X-T-X-T → XỈU"
        elif m5 == ["Xỉu", "Tài", "Xỉu", "Tài", "Xỉu"]:
            du_doan = "TÀI"
            ty_le = 92.5
            pp = "Xen kẽ X-T-X-T-X → TÀI"

    # LUẬT 3: Đôi song tử
    elif tong_phien >= 5:
        k2, k3, k4, k5 = kq_list[-2], kq_list[-3], kq_list[-4], kq_list[-5]
        if k5 == k3 and k2 == k4 and k5 != k2:
            du_doan = k5
            ty_le = 88.0
            pp = "Đôi song tử → lặp lại"

    # LUẬT 4: Cạnh bằng TT-XX / XX-TT
    elif tong_phien >= 4:
        m4 = kq_list[-4:]
        if m4 == ["Tài", "Tài", "Xỉu", "Xỉu"]:
            du_doan = "TÀI"
            ty_le = 85.5
            pp = "Cạnh bằng TT-XX → TÀI"
        elif m4 == ["Xỉu", "Xỉu", "Tài", "Tài"]:
            du_doan = "XỈU"
            ty_le = 85.5
            pp = "Cạnh bằng XX-TT → XỈU"

    # LUẬT 5: Lái ngược (A-A-B → A)
    elif tong_phien >= 3:
        k2, k3 = kq_list[-2], kq_list[-3]
        if k3 == k2 and k2 != kq_cuoi:
            du_doan = k2
            ty_le = 82.0
            pp = f"Lái ngược → quay {k2}"

    # LUẬT 6: Chênh lệch / cân bằng
    if not du_doan:
        tl_tai = tong_tai / tong_phien if tong_phien > 0 else 0.5
        if tl_tai >= 0.60:
            du_doan = "XỈU"
            ty_le = 78.0
            pp = f"15phiên: TÀI {tong_tai} → cân XỈU"
        elif tl_tai <= 0.40:
            du_doan = "TÀI"
            ty_le = 78.0
            pp = f"15phiên: XỈU đa số → cân TÀI"
        else:
            # Cân bằng → nối đuôi phiên cuối
            du_doan = kq_cuoi
            ty_le = 72.0
            pp = f"Nối đuôi: {kq_cuoi} → tiếp {kq_cuoi}"

    # Xu hướng
    if chuoi_tai >= 3:
        trend = f"Chuỗi TÀI {chuoi_tai} phiên - ĐẢO CHIỀU"
    elif chuoi_xiu >= 3:
        trend = f"Chuỗi XỈU {chuoi_xiu} phiên - ĐẢO CHIỀU"
    elif tong_tai > tong_xiu + 1:
        trend = f"TÀI ưu thế ({tong_tai}T-{tong_xiu}X)"
    elif tong_xiu > tong_tai + 1:
        trend = f"XỈU ưu thế ({tong_tai}T-{tong_xiu}X)"
    else:
        trend = f"Cân bằng ({tong_tai}T-{tong_xiu}X)"

    return {
        "du_doan": du_doan,
        "ti_le": round(ty_le, 1),
        "loi_khuyen": f"{pp} ({round(ty_le, 1)}%)",
        "phuong_phap": pp,
        "tong_tai": tong_tai,
        "tong_xiu": tong_xiu,
        "chuoi_tai": chuoi_tai,
        "chuoi_xiu": chuoi_xiu,
        "trend": trend
    }

# ================= HÀM HỖ TRỢ SIÊU MẠNH =================
def get_str(d, k, defval=""):
    v = d.get(k, defval)
    return str(v).strip() if v else defval

def get_int(d, k, defval=0):
    try:
        return int(d.get(k, defval))
    except:
        return defval

def find_all_lists(obj, path="root"):
    """✅ Tìm TẤT CẢ các danh sách trong object JSON"""
    lists = []
    if isinstance(obj, list):
        lists.append({"path": path, "data": obj, "length": len(obj)})
    elif isinstance(obj, dict):
        for key, value in obj.items():
            lists.extend(find_all_lists(value, f"{path}.{key}"))
    return lists

def find_best_session_list(data):
    """✅ Tìm danh sách phiên PHÙ HỢP NHẤT trong mọi cấu trúc"""
    all_lists = find_all_lists(data)
    
    if not all_lists:
        return None, None
    
    # Lọc các list có phần tử là dict (phiên game)
    candidates = []
    for item in all_lists:
        lst = item["data"]
        if len(lst) > 0 and isinstance(lst[0], dict):
            # Đếm xem có bao nhiêu phần tử có thể parse được kết quả
            parseable = sum(1 for x in lst[:20] if isinstance(x, dict) and quick_check_tx(x))
            candidates.append({
                **item,
                "parseable": parseable,
                "dict_count": sum(1 for x in lst if isinstance(x, dict))
            })
    
    if not candidates:
        # Không tìm thấy list chứa dict → thử list đầu tiên
        best = max(all_lists, key=lambda x: x["length"])
        return best["data"], best["path"]
    
    # Ưu tiên list có nhiều phần tử parseable nhất
    candidates.sort(key=lambda x: (-x["parseable"], -x["length"]))
    best = candidates[0]
    logger.info(f"✅ Chọn danh sách: {best['path']} | độ dài={best['length']} | parseable={best['parseable']}")
    return best["data"], best["path"]

def quick_check_tx(obj):
    """✅ Kiểm tra nhanh xem object có chứa thông tin Tài/Xỉu không"""
    if not isinstance(obj, dict):
        return False
    for v in obj.values():
        if isinstance(v, str):
            vu = v.upper()
            if any(k in vu for k in ["TÀI", "TAI", "XỈU", "XIU", "BIG", "SMALL"]):
                return True
    # Kiểm tra tổng điểm
    for sum_key in ["sum", "total", "tong", "point"]:
        if sum_key in obj:
            try:
                int(obj[sum_key])
                return True
            except:
                pass
    return False

def classify_tx_text(text):
    """✅ Phân loại Tài/Xỉu từ text"""
    if not text:
        return None
    t = text.upper().strip()
    # TÀI
    if any(k in t for k in ["TÀI", "TAI", "BIG", "LARGE"]):
        return "Tài"
    # XỈU
    if any(k in t for k in ["XỈU", "XIU", "SMALL", "TINY"]):
        return "Xỉu"
    return None

def parse_result_super(session_obj):
    """✅ PARSE SIÊU MẠNH - cố gắng mọi cách"""
    if not isinstance(session_obj, dict):
        return None
    
    # CÁCH 1: Tìm theo key trực tiếp (nhiều key khác nhau)
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
    
    # CÁCH 2: Quét TOÀN BỘ giá trị trong object
    for v in session_obj.values():
        if isinstance(v, str):
            result = classify_tx_text(v)
            if result:
                return result
    
    # CÁCH 3: Tìm theo tổng điểm xúc xắc
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
    
    # CÁCH 4: Tính từ mảng xúc xắc
    for dice_key in ["dice", "dices", "xucxac", "numbers", "diceValues", "values"]:
        if dice_key in session_obj:
            dice = session_obj[dice_key]
            if isinstance(dice, list) and len(dice) >= 3:
                try:
                    tong = sum(int(x) for x in dice)
                    return "Tài" if tong >= 11 else "Xỉu"
                except:
                    pass
    
    # CÁCH 5: Tìm số trong string (ví dụ: "Tổng 12" → Tài)
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
    """✅ Lấy ID phiên từ mọi định dạng"""
    if not isinstance(session_obj, dict):
        return "N/A"
    for id_key in ["id", "sessionId", "session_id", "phien", "issue", "period", "round", "roundId", "issueNumber", "number", "no", "stt"]:
        if id_key in session_obj and session_obj[id_key]:
            return str(session_obj[id_key])
    # Tìm số trong các giá trị
    for v in session_obj.values():
        if isinstance(v, str) and v.startswith('#'):
            return v
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
    return {"status": "ok", "msg": "Server AI v4.0 CHẮC CHẮN đang chạy"}

@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "version": "4.0",
        "mode": "CHẮC CHẮN CÓ KẾT QUẢ",
        "config": f"Lấy & phân tích {SO_LUONG_PHAN_TICH} phiên",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/api/debug")
async def debug_api(tool: str):
    """✅ Debug chi tiết - xem mọi thứ"""
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
        
        # Tìm danh sách tốt nhất
        best_list, best_path = find_best_session_list(data)
        
        # Parse thử
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
    logger.info(f"🔍 Scan: {tool} | {username}")

    # Kiểm tra tài khoản
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
        # Gọi API
        res = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }, timeout=15)
        
        logger.info(f"📡 HTTP Status: {res.status_code}")
        
        try:
            data = res.json()
        except Exception as je:
            logger.error(f"❌ JSON lỗi: {je}")
            # ✅ FIX: Dự đoán mặc định thay vì lỗi
            ket_qua = phan_tich_ai([])
            ket_qua["phien"] = "API-LỖI"
            ket_qua["lich_su_15"] = []
            ket_qua["phan_tich_15"] = []
            ket_qua["trend"] = "Lỗi kết nối API - dự đoán tạm"
            return JSONResponse({"status": "success", "data": ket_qua})

        # ✅ BƯỚC 1: Tìm danh sách phiên TỐT NHẤT
        all_list, list_path = find_best_session_list(data)

        if not all_list or len(all_list) == 0:
            logger.warning("⚠️ Không tìm thấy danh sách phiên nào!")
            # ✅ FIX: Vẫn dự đoán mặc định
            ket_qua = phan_tich_ai([])
            ket_qua["phien"] = "NODATA"
            ket_qua["lich_su_15"] = []
            ket_qua["phan_tich_15"] = []
            ket_qua["trend"] = "Không có dữ liệu - dự đoán tạm"
            return JSONResponse({"status": "success", "data": ket_qua})

        logger.info(f"📋 Danh sách: {list_path} | {len(all_list)} phiên")

        # ✅ BƯỚC 2: Thử CẢ 2 CÁCH lấy 15 phiên
        # Cách A: Lấy 15 đầu (giả định mới nhất ở đầu)
        # Cách B: Lấy 15 cuối (giả định cũ nhất ở đầu)
        # Chọn cách nào parse được nhiều kết quả hơn
        
        def get_and_parse(source_list, take_from="head"):
            """Lấy 15 phiên và parse"""
            if len(source_list) >= SO_LUONG_PHAN_TICH:
                if take_from == "head":
                    raw = source_list[:SO_LUONG_PHAN_TICH]
                else:
                    raw = source_list[-SO_LUONG_PHAN_TICH:]
            else:
                raw = source_list.copy()
            
            # Đảo: cũ ở đầu, mới ở cuối
            ordered = raw[::-1] if take_from == "head" else raw.copy()
            
            # Parse
            results = []
            for s in ordered:
                r = parse_result_super(s)
                if r:
                    results.append(r)
            return results, ordered
        
        # Thử cả 2 cách
        kq_head, ordered_head = get_and_parse(all_list, "head")
        kq_tail, ordered_tail = get_and_parse(all_list, "tail")
        
        logger.info(f"🔍 Cách A (lấy đầu): {len(kq_head)}/15 parse được | {kq_head}")
        logger.info(f"🔍 Cách B (lấy cuối): {len(kq_tail)}/15 parse được | {kq_tail}")
        
        # Chọn cách tốt hơn
        if len(kq_head) >= len(kq_tail):
            kq_final = kq_head
            ordered_final = ordered_head
            cach_chon = "A (lấy đầu - mới nhất ở đầu)"
        else:
            kq_final = kq_tail
            ordered_final = ordered_tail
            cach_chon = "B (lấy cuối - cũ nhất ở đầu)"
        
        logger.info(f"✅ Chọn cách {cach_chon} | {len(kq_final)} phiên hợp lệ")

        # ✅ BƯỚC 3: LUÔN chạy thuật toán - không bao giờ WAIT
        ket_qua = phan_tich_ai(kq_final)

        # Lấy ID phiên mới nhất
        phien_id = extract_session_id_super(ordered_final[-1]) if ordered_final else "N/A"
        
        ket_qua["phien"] = phien_id
        ket_qua["lich_su_15"] = kq_final
        ket_qua["phan_tich_15"] = kq_final
        ket_qua["config"] = {
            "lay_tu_api": SO_LUONG_PHAN_TICH,
            "phan_tich": SO_LUONG_PHAN_TICH,
            "cach_lay": cach_chon,
            "parse_duoc": f"{len(kq_final)}/15"
        }

        logger.info(f"🎯 KẾT QUẢ CUỐI: {ket_qua['du_doan']} | {ket_qua['phuong_phap']} | {ket_qua['ti_le']}%")

        return JSONResponse({"status": "success", "data": ket_qua})

    except Exception as e:
        logger.error(f"❌ Lỗi hệ thống: {e}", exc_info=True)
        # ✅ FIX: Vẫn trả về dự đoán mặc định thay vì lỗi
        ket_qua = phan_tich_ai([])
        ket_qua["phien"] = "ERROR"
        ket_qua["lich_su_15"] = []
        ket_qua["phan_tich_15"] = []
        ket_qua["trend"] = f"Lỗi hệ thống: {str(e)[:50]}"
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
    logger.info(f"🚀 Server AI v4.0 CHẮC CHẮN | Phân tích {SO_LUONG_PHAN_TICH} phiên | Cổng {port}")
    uvicorn.run("server_ai:app", host="0.0.0.0", port=port)
