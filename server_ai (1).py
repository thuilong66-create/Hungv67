"""
SERVER AI - HỆ THỐNG TOOL VIP (FIX NÂNG CAO v3.3)
✅ Luôn lấy 13 phiên gần nhất để phân tích
✅ Dự đoán ngay không chờ
✅ 8 loại cầu phổ biến Tài Xỉu
✅ Tự động parse mọi định dạng API
✅ Có endpoint debug để kiểm tra dữ liệu raw
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
from datetime import datetime, timedelta

# ================= CẤU HÌNH =================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Hệ thống Tool VIP", version="3.3")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "hethong_vip.db"
SO_LUONG_PHAN_TICH = 13  # ✅ LUÔN LẤY 13 PHIÊN

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

# ================= THUẬT TOÁN SOI CẦU — 13 PHIÊN =================
def phan_tich_ai(kq_list):
    tong_tai = kq_list.count("Tài")
    tong_xiu = kq_list.count("Xỉu")
    tong_phien = len(kq_list)

    if tong_phien < 2:
        return {
            "du_doan": "WAIT",
            "ti_le": 0,
            "loi_khuyen": "Chờ thêm dữ liệu...",
            "phuong_phap": "Đang thu thập",
            "tong_tai": tong_tai,
            "tong_xiu": tong_xiu,
            "chuoi_tai": 0,
            "chuoi_xiu": 0,
            "trend": "Đang thu thập dữ liệu..."
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

    du_doan = "WAIT"
    ty_le = 0
    pp = ""

    # 1. CẦU BỆT DÀI (≥3 cùng)
    if chuoi_tai >= 3:
        du_doan = "XỈU"
        ty_le = min(90 + chuoi_tai * 3, 98.5)
        pp = f"Bệt TÀI {chuoi_tai} phiên → bẻ XỈU"
    elif chuoi_xiu >= 3:
        du_doan = "TÀI"
        ty_le = min(90 + chuoi_xiu * 3, 98.5)
        pp = f"Bệt XỈU {chuoi_xiu} phiên → bẻ TÀI"

    # 2. XEN KẼ T-X-T-X
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

    # 3. ĐÔI SONG TỬ
    elif tong_phien >= 4:
        k2, k3, k4 = kq_list[-2], kq_list[-3], kq_list[-4]
        k5 = kq_list[-5] if tong_phien >= 5 else None
        if k5 and k5 == k3 and k2 == k4 and k5 != k2:
            du_doan = k5
            ty_le = 88.0
            pp = "Đôi song tử → lặp lại"

    # 4. CẠNH BẰNG
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

    # 5. LÁI NGƯỢC
    elif tong_phien >= 3:
        k2, k3 = kq_list[-2], kq_list[-3]
        if k3 == k2 and k2 != kq_cuoi:
            du_doan = k2
            ty_le = 82.0
            pp = f"Lái ngược → quay {k2}"

    # 6. CHÊNH LỆCH (dựa 13 phiên)
    else:
        tl_tai = tong_tai / tong_phien
        if tl_tai >= 0.62:
            du_doan = "XỈU"
            ty_le = 78.0
            pp = f"13phiên: TÀI {tong_tai} → cân XỈU"
        elif tl_tai <= 0.38:
            du_doan = "TÀI"
            ty_le = 78.0
            pp = f"13phiên: XỈU đa số → cân TÀI"
        else:
            du_doan = kq_cuoi
            ty_le = 72.0
            pp = f"Nối đuôi: {kq_cuoi} → tiếp {kq_cuoi}"

    # Xác định xu hướng
    if chuoi_tai >= 3:
        trend = f"Chuỗi TÀI {chuoi_tai} phiên - ĐẢO CHIỀU"
    elif chuoi_xiu >= 3:
        trend = f"Chuỗi XỈU {chuoi_xiu} phiên - ĐẢO CHIỀU"
    elif tong_tai > tong_xiu + 2:
        trend = f"TÀI ưu thế ({tong_tai}/{tong_phien})"
    elif tong_xiu > tong_tai + 2:
        trend = f"XỈU ưu thế ({tong_xiu}/{tong_phien})"
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

# ================= HÀM HỖ TRỢ =================
def get_str(d, k, defval=""):
    v = d.get(k, defval)
    return str(v).strip() if v else defval

def get_int(d, k, defval=0):
    try:
        return int(d.get(k, defval))
    except:
        return defval

def find_list_in_data(data):
    """✅ Tìm danh sách phiên trong mọi cấu trúc API"""
    if isinstance(data, list):
        return data
    
    if isinstance(data, dict):
        # Thử các key phổ biến
        list_keys = [
            "list", "data", "sessions", "items", "results", "history",
            "records", "rounds", "games", "tx_list", "txList",
            "sessionList", "session_list", "liteSessions", "lite_sessions"
        ]
        for key in list_keys:
            if key in data and isinstance(data[key], list):
                logger.info(f"✅ Tìm thấy danh sách ở key: '{key}'")
                return data[key]
        
        # Thìm vào data.data (cấu trúc lồng nhau)
        if "data" in data and isinstance(data["data"], dict):
            inner = find_list_in_data(data["data"])
            if inner:
                return inner
        
        # Tìm list đầu tiên trong object
        for v in data.values():
            if isinstance(v, list) and len(v) > 0:
                logger.info(f"✅ Tìm thấy danh sách ở value (key không xác định)")
                return v
    
    return None

def parse_result(session_obj):
    """✅ Phân tích kết quả TÀI/XỈU từ mọi định dạng"""
    if not isinstance(session_obj, dict):
        return None
    
    # 1. Tìm theo key trực tiếp
    result_keys = [
        "resultTruyenThong", "result", "ketqua", "ketQua", "kq",
        "value", "tx_result", "txResult", "taiXiu", "tai_xiu",
        "result_tx", "outcome", "status", "type", "name",
        "diceResult", "dice_result", "gameResult", "game_result"
    ]
    
    for key in result_keys:
        if key in session_obj and session_obj[key]:
            val = str(session_obj[key]).strip()
            if val:
                result = classify_tx(val)
                if result:
                    return result
    
    # 2. Quét toàn bộ giá trị trong object tìm chữ Tài/Xỉu
    for v in session_obj.values():
        if isinstance(v, str):
            result = classify_tx(v)
            if result:
                return result
    
    # 3. Phân tích theo tổng điểm xúc xắc
    for sum_key in ["sum", "total", "tong", "tongDiem", "diceSum", "dice_sum", "point", "points"]:
        if sum_key in session_obj:
            try:
                tong = int(session_obj[sum_key])
                if tong >= 11:
                    return "Tài"
                elif tong >= 3:
                    return "Xỉu"
            except:
                pass
    
    # 4. Nếu có mảng dice, tính tổng
    for dice_key in ["dice", "dices", "xucxac", "numbers"]:
        if dice_key in session_obj:
            dice = session_obj[dice_key]
            if isinstance(dice, list) and len(dice) >= 3:
                try:
                    tong = sum(int(x) for x in dice)
                    return "Tài" if tong >= 11 else "Xỉu"
                except:
                    pass
    
    return None

def classify_tx(text):
    """✅ Phân loại Tài/Xỉu từ text"""
    if not text:
        return None
    t = text.upper().strip()
    # TÀI
    if any(k in t for k in ["TÀI", "TAI", "BIG", "LARGE", "LON"]):
        return "Tài"
    # XỈU
    if any(k in t for k in ["XỈU", "XIU", "SMALL", "TINY", "NHO", "BE"]):
        return None  # Tránh nhầm lẫn, chỉ trả về nếu chắc chắn
    # Kiểm tra riêng Xỉu
    if "XỈU" in t or "XIU" in t:
        return "Xỉu"
    return None

def extract_session_id(session_obj):
    """✅ Lấy ID phiên từ mọi định dạng"""
    if not isinstance(session_obj, dict):
        return "N/A"
    for id_key in ["id", "sessionId", "session_id", "phien", "issue", "period", "round", "roundId", "issueNumber"]:
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
    return {"status": "ok", "msg": "Server AI v3.3 đang chạy"}

@app.get("/api/health")
async def health():
    return {"status": "online", "version": "3.3", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

@app.get("/api/debug")
async def debug_api(tool: str):
    """✅ Endpoint debug - xem raw response từ API game"""
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
        
        raw_text = res.text[:3000]  # Giới hạn 3000 ký tự
        
        try:
            data = res.json()
            all_list = find_list_in_data(data)
            
            # Phân tích thử vài phiên đầu
            sample_results = []
            if all_list and len(all_list) > 0:
                for i, s in enumerate(all_list[:5]):
                    if isinstance(s, dict):
                        result = parse_result(s)
                        keys = list(s.keys())
                        sample_results.append({
                            "index": i,
                            "keys": keys[:10],
                            "parsed_result": result,
                            "raw_sample": {k: str(v)[:50] for k, v in list(s.items())[:5]}
                        })
            
            return JSONResponse({
                "status": "success",
                "tool": tool,
                "url": url,
                "http_status": res.status_code,
                "data_type": type(data).__name__,
                "top_level_keys": list(data.keys()) if isinstance(data, dict) else "N/A",
                "found_list_length": len(all_list) if all_list else 0,
                "list_is_none": all_list is None,
                "sample_analysis": sample_results,
                "raw_preview": raw_text[:1000]
            })
        except Exception as je:
            return JSONResponse({
                "status": "error",
                "msg": f"Parse JSON lỗi: {je}",
                "raw_text": raw_text
            })
            
    except Exception as e:
        return JSONResponse({"status": "error", "msg": str(e)})

@app.get("/api/scan")
async def scan_game(tool: str, username: str):
    logger.info(f"🔍 Scan: {tool} | {username}")

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
        
        logger.info(f"📡 HTTP Status: {res.status_code} | Content-Type: {res.headers.get('Content-Type', '?')}")
        
        try:
            data = res.json()
        except Exception as je:
            logger.error(f"❌ JSON Parse error: {je}")
            logger.error(f"📄 Raw response (first 500 chars): {res.text[:500]}")
            return JSONResponse({
                "status": "error",
                "msg": "API trả về dữ liệu không phải JSON",
                "debug": {"raw": res.text[:300]}
            })

        # ✅ Tìm danh sách phiên trong mọi cấu trúc
        all_list = find_list_in_data(data)

        if not all_list or len(all_list) == 0:
            logger.warning(f"⚠️ Không tìm thấy danh sách phiên")
            if isinstance(data, dict):
                logger.warning(f"⚠️ Top-level keys: {list(data.keys())}")
                # Log thử data để debug
                logger.warning(f"⚠️ Data preview: {json.dumps(data, default=str)[:500]}")
            
            return JSONResponse({
                "status": "error",
                "msg": "API không trả về danh sách phiên. Vui lòng kiểm tra /api/debug",
                "debug": {
                    "data_keys": list(data.keys()) if isinstance(data, dict) else str(type(data)),
                    "data_type": type(data).__name__,
                    "preview": json.dumps(data, default=str)[:300] if isinstance(data, (dict, list)) else str(data)[:300]
                }
            })

        logger.info(f"📋 API trả về {len(all_list)} phiên")

        # ✅ FIX: Lấy 13 phiên MỚI NHẤT
        # Giả định: API trả về phiên MỚI NHẤT ở ĐẦU danh sách
        if len(all_list) >= SO_LUONG_PHAN_TICH:
            lst = all_list[:SO_LUONG_PHAN_TICH]
        else:
            lst = all_list.copy()

        # Đảo ngược: CŨ NHẤT ở đầu, MỚI NHẤT ở cuối (cho thuật toán)
        lst = lst[::-1]

        # ✅ Phân tích kết quả
        kq = []
        for s in lst:
            result = parse_result(s)
            if result:
                kq.append(result)

        logger.info(f"📊 Phân tích: {len(kq)}/{len(lst)} phiên hợp lệ → {kq}")

        if len(kq) < 2:
            # Log chi tiết phiên đầu tiên để debug
            if lst and isinstance(lst[0], dict):
                logger.warning(f"⚠️ Sample session keys: {list(lst[0].keys())}")
                logger.warning(f"⚠️ Sample session data: {json.dumps(lst[0], default=str)[:300]}")
            
            return JSONResponse({
                "status": "error",
                "msg": f"Chỉ phân tích được {len(kq)} phiên. Dùng /api/debug để xem cấu trúc API.",
                "debug": {
                    "tong_phien_api": len(all_list),
                    "tong_phien_hop_le": len(kq),
                    "sample_keys": list(lst[0].keys()) if lst and isinstance(lst[0], dict) else [],
                    "sample_data": json.dumps(lst[0], default=str)[:200] if lst else "empty"
                }
            })

        ket_qua = phan_tich_ai(kq)

        # Lấy ID phiên mới nhất (phần tử cuối trong lst đã đảo)
        ket_qua["phien"] = extract_session_id(lst[-1]) if lst else "N/A"
        ket_qua["lich_su_13"] = kq
        ket_qua["lich_su_15"] = kq  # Tương thích ngược

        logger.info(f"✅ DỰ ĐOÁN: {ket_qua['du_doan']} | {ket_qua['phuong_phap']} | Tỷ lệ: {ket_qua['ti_le']}%")

        return JSONResponse({"status": "success", "data": ket_qua})

    except requests.exceptions.Timeout:
        logger.error("❌ Timeout")
        return JSONResponse({"status": "error", "msg": "Timeout kết nối game server"})
    except requests.exceptions.ConnectionError as ce:
        logger.error(f"❌ Connection error: {ce}")
        return JSONResponse({"status": "error", "msg": "Không thể kết nối game server"})
    except Exception as e:
        logger.error(f"❌ Lỗi hệ thống: {e}", exc_info=True)
        return JSONResponse({"status": "error", "msg": f"Lỗi: {str(e)}"})

# ================= AUTH & USER APIs (giữ nguyên) =================
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
    logger.info(f"🚀 Server AI v3.3 chạy cổng {port}")
    uvicorn.run("server_ai:app", host="0.0.0.0", port=port)
