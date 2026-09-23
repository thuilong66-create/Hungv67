"""
SERVER AI - HỆ THỐNG TOOL VIP
Phiên bản cuối cùng: KHÔNG DÙNG PYDANTIC BASEMODEL
Chắc chắn chạy trên mọi phiên bản Python
"""

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn
import sqlite3
import os
import random
import logging
from datetime import datetime, timedelta

# ================= CẤU HÌNH =================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Hệ thống Tool VIP", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "hethong_vip.db"

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
                "INSERT OR IGNORE INTO users (username, password, balance, vip_expire, is_banned) VALUES (?, ?, ?, ?, ?)",
                ('hungadmin11', 'hungki98', 999999999, '2099-12-31 23:59:59', 0)
            )
            conn.commit()
        logger.info("✅ Database OK")
    except Exception as e:
        logger.error(f"❌ Lỗi DB: {e}")

khoi_tao_db()

# ================= THUẬT TOÁN AI =================
def phan_tich_ai(kq_list):
    tong_tai = kq_list.count("Tài")
    tong_xiu = kq_list.count("Xỉu")
    
    if len(kq_list) < 5:
        return {
            "du_doan": "WAIT",
            "ti_le": 0,
            "tong_tai": tong_tai,
            "tong_xiu": tong_xiu
        }
    
    gan_nhat = kq_list[-5:]
    kq_cuoi = kq_list[-1]
    
    chuoi = 1
    for i in range(len(kq_list) - 2, -1, -1):
        if kq_list[i] == kq_cuoi:
            chuoi += 1
        else:
            break
    
    if (gan_nhat == ["Tài", "Xỉu", "Tài", "Xỉu", "Tài"] or 
        gan_nhat == ["Xỉu", "Tài", "Xỉu", "Tài", "Xỉu"]):
        du_doan = "XỈU" if kq_cuoi == "Tài" else "TÀI"
        ty_le = round(random.uniform(88.0, 96.0), 1)
    elif chuoi >= 4:
        du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
        ty_le = min(75 + chuoi * 4.5, 99.9)
    else:
        du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
        ty_le = round(random.uniform(70.0, 82.0), 1)
    
    return {
        "du_doan": du_doan,
        "ti_le": round(ty_le, 1),
        "tong_tai": tong_tai,
        "tong_xiu": tong_xiu
    }

# ================= HÀM KIỂM TRA DỮ LIỆU =================
def get_str(data, key, default=""):
    val = data.get(key, default)
    return str(val).strip() if val else default

def get_int(data, key, default=0):
    try:
        return int(data.get(key, default))
    except:
        return default

# ================= API ROUTES =================
@app.get("/")
async def home():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"status": "success", "message": "Server Tool VIP đang hoạt động!"}

@app.get("/api/health")
async def health_check():
    return {"status": "online", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

@app.get("/api/scan")
async def scan_game(tool: str, username: str):
    logger.info(f"🔍 Scan: {tool} - {username}")
    
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT vip_expire, is_banned FROM users WHERE username = ?", (username,))
        row = c.fetchone()
    
    if not row:
        return JSONResponse({"status": "error", "msg": "Tài khoản không tồn tại!"})
    if row[1] == 1 and username != "hungadmin11":
        return JSONResponse({"status": "error", "msg": "Tài khoản đã bị Admin khóa!"})
    if datetime.now() > datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") and username != "hungadmin11":
        return JSONResponse({"status": "error", "msg": "Gói VIP đã hết hạn!"})
    
    urls = {
        "lc79": "https://wtx.tele68.com/v1/tx/lite-sessions",
        "betvip": "https://wtx.macminim6.online/v1/tx/lite-sessions"
    }
    
    if tool not in urls:
        return JSONResponse({"status": "error", "msg": "Tool không hợp lệ!"})
    
    try:
        res = requests.get(
            urls[tool],
            headers={"User-Agent": "Mozilla/5.0 Chrome/120.0"},
            timeout=8
        )
        data = res.json()
        
        if not data.get("list"):
            return JSONResponse({"status": "error", "msg": "Chờ cầu mới..."})
        
        lst = data["list"][::-1]
        kq = ["Tài" if "TAI" in str(s.get("resultTruyenThong", "")).upper() else "Xỉu" for s in lst]
        
        ket_qua = phan_tich_ai(kq)
        
        try:
            ket_qua["phien"] = str(int(lst[-1]["id"]) + 1)
        except:
            ket_qua["phien"] = "N/A"
        
        logger.info(f"✅ {ket_qua['du_doan']} ({ket_qua['ti_le']}%)")
        return JSONResponse({"status": "success", "data": ket_qua})
        
    except Exception as e:
        logger.error(f"❌ Lỗi: {e}")
        return JSONResponse({"status": "error", "msg": "Đứt kết nối Server Game!"})

@app.post("/api/auth")
async def auth_user(request: Request):
    try:
        data = await request.json()
    except:
        return JSONResponse({"status": "error", "msg": "Dữ liệu không hợp lệ!"})
    
    action = get_str(data, "action")
    u = get_str(data, "username")
    p = get_str(data, "password")
    
    if not u or not p:
        return JSONResponse({"status": "error", "msg": "Nhập đủ thông tin!"})
    
    with get_db() as conn:
        c = conn.cursor()
        
        if action == "register":
            c.execute("SELECT username FROM users WHERE username = ?", (u,))
            if c.fetchone():
                return JSONResponse({"status": "error", "msg": "Tài khoản đã có người xài!"})
            c.execute(
                "INSERT INTO users (username, password, balance, vip_expire, is_banned) VALUES (?, ?, 0, '2000-01-01 00:00:00', 0)",
                (u, p)
            )
            conn.commit()
            logger.info(f"✅ Đăng ký: {u}")
            return JSONResponse({"status": "success", "msg": "Đăng ký thành công!"})
        
        else:
            c.execute("SELECT password, is_banned FROM users WHERE username = ?", (u,))
            row = c.fetchone()
            
            if not row or row[0] != p:
                return JSONResponse({"status": "error", "msg": "Sai tài khoản hoặc mật khẩu!"})
            if row[1] == 1 and u != "hungadmin11":
                return JSONResponse({"status": "error", "msg": "Tài khoản bị khóa!"})
            
            logger.info(f"✅ Đăng nhập: {u}")
            return JSONResponse({"status": "success", "msg": "Đăng nhập thành công!"})

@app.get("/api/user_info")
async def get_user_info(username: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT balance, vip_expire FROM users WHERE username = ?", (username,))
        row = c.fetchone()
    
    if not row:
        return JSONResponse({"status": "error"})
    
    is_vip = datetime.now() < datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") or username == "hungadmin11"
    
    if username == "hungadmin11":
        vip_str = "VĨNH VIỄN (ADMIN)"
    else:
        vip_str = row[1] if is_vip else "Chưa có VIP"
    
    return JSONResponse({
        "status": "success",
        "data": {
            "balance": row[0],
            "vip_expire": vip_str,
            "is_vip": is_vip
        }
    })

@app.post("/api/deposit")
async def deposit(request: Request):
    try:
        data = await request.json()
    except:
        return JSONResponse({"status": "error", "msg": "Dữ liệu không hợp lệ!"})
    
    username = get_str(data, "username")
    network = get_str(data, "network")
    amount = get_int(data, "amount")
    pin = get_str(data, "pin")
    serial = get_str(data, "serial")
    
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO deposits (username, card_type, card_amount, card_pin, card_serial, status) VALUES (?, ?, ?, ?, ?, 'PENDING')",
            (username, network, amount, pin, serial)
        )
        conn.commit()
    
    return JSONResponse({"status": "success", "msg": "Đã gửi thẻ! Chờ Admin duyệt."})

@app.post("/api/buy_vip")
async def buy_vip(request: Request):
    try:
        data = await request.json()
    except:
        return JSONResponse({"status": "error", "msg": "Dữ liệu không hợp lệ!"})
    
    username = get_str(data, "username")
    package = get_str(data, "package")
    
    if username == "hungadmin11":
        return JSONResponse({"status": "success", "msg": "Sếp VIP sẵn rồi!"})
    
    prices = {
        "1D": (30000, 1),
        "3D": (50000, 3),
        "7D": (100000, 7),
        "30D": (150000, 30),
        "PERM": (200000, 36500)
    }
    
    if package not in prices:
        return JSONResponse({"status": "error", "msg": "Gói không hợp lệ!"})
    
    cost, days = prices[package]
    
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT balance, vip_expire FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        
        if not row or row[0] < cost:
            return JSONResponse({"status": "error", "msg": "Không đủ lúa!"})
        
        now = datetime.now()
        curr_exp = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
        new_exp = (curr_exp if curr_exp > now else now) + timedelta(days=days)
        
        c.execute(
            "UPDATE users SET balance = balance - ?, vip_expire = ? WHERE username = ?",
            (cost, new_exp.strftime("%Y-%m-%d %H:%M:%S"), username)
        )
        conn.commit()
    
    logger.info(f"👑 Mua VIP: {username} - {package}")
    return JSONResponse({"status": "success", "msg": "Mua VIP thành công!"})

@app.get("/api/admin/data")
async def admin_data(username: str):
    if username != "hungadmin11":
        return JSONResponse({"status": "error"})
    
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT username, balance, vip_expire, is_banned FROM users WHERE username != 'hungadmin11'")
        users = c.fetchall()
        c.execute("SELECT id, username, card_type, card_amount, card_pin, card_serial FROM deposits WHERE status = 'PENDING'")
        deps = c.fetchall()
    
    return JSONResponse({"status": "success", "users": users, "deps": deps})

@app.post("/api/admin/action")
async def admin_action(request: Request):
    try:
        data = await request.json()
    except:
        return JSONResponse({"status": "error", "msg": "Dữ liệu không hợp lệ!"})
    
    admin = get_str(data, "admin")
    action = get_str(data, "action")
    target = get_str(data, "target")
    dep_id = get_int(data, "dep_id")
    amount = get_int(data, "amount")
    
    if admin != "hungadmin11":
        return JSONResponse({"status": "error"})
    
    with get_db() as conn:
        c = conn.cursor()
        
        if action == "ban":
            c.execute("UPDATE users SET is_banned = 1 WHERE username = ?", (target,))
        elif action == "unban":
            c.execute("UPDATE users SET is_banned = 0 WHERE username = ?", (target,))
        elif action == "approve_dep":
            c.execute("UPDATE deposits SET status = 'APPROVED' WHERE id = ?", (dep_id,))
            c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, target))
        elif action == "reject_dep":
            c.execute("UPDATE deposits SET status = 'REJECTED' WHERE id = ?", (dep_id,))
        else:
            return JSONResponse({"status": "error", "msg": "Hành động không hợp lệ!"})
        
        conn.commit()
    
    return JSONResponse({"status": "success"})

# ================= CHẠY SERVER =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Server chạy tại 0.0.0.0:{port}")
    uvicorn.run("server_ai:app", host="0.0.0.0", port=port)
        
