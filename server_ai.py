"""
SERVER AI - HỆ THỐNG DỰ ĐOÁN TÀI XỈU
Phiên bản cuối cùng - tương thích Python 3.11 + Pydantic v2
"""

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import uvicorn
import sqlite3
import os
import logging
from datetime import datetime, timedelta

# ================= CẤU HÌNH =================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Hệ thống AI Dự đoán", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = os.environ.get("DB_FILE", "hethong_vip.db")

# ================= KHỞI TẠO DB =================
def khoi_tao_db():
    try:
        conn = sqlite3.connect(DB_FILE)
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
            card_amount INTEGER, 
            card_pin TEXT, 
            card_serial TEXT, 
            status TEXT DEFAULT 'PENDING'
        )''')
        c.execute("SELECT username FROM users WHERE username = ?", ('hungadmin11',))
        if not c.fetchone():
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                     ('hungadmin11', 'hungki98', 999999999, '2099-12-31 23:59:59', 0))
        conn.commit()
        conn.close()
        logger.info("✅ Database khởi tạo OK")
    except Exception as e:
        logger.error(f"❌ Lỗi DB: {e}")

khoi_tao_db()

# ================= THUẬT TOÁN AI =================
def phan_tich_ai(kq_list):
    tong_tai = kq_list.count("Tài")
    tong_xiu = kq_list.count("Xỉu")
    
    if len(kq_list) < 5:
        return {"du_doan": "WAIT", "ti_le": 0, "loi_khuyen": "Đang nạp Data...",
                "trend": "...", "tong_tai": tong_tai, "tong_xiu": tong_xiu,
                "chuoi_lap": 0, "kq_cuoi": "..."}
    
    kq_cuoi = kq_list[-1]
    chuoi = 1
    for i in range(len(kq_list)-2, -1, -1):
        if kq_list[i] == kq_cuoi:
            chuoi += 1
        else:
            break
    
    du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
    ty_le = min(50 + chuoi * 5, 99) if chuoi >= 3 else 60.0
    radar = "".join(["🔴" if x == "Tài" else "🔵" for x in kq_list[-12:]])
    
    return {"du_doan": du_doan, "ti_le": round(ty_le, 1),
            "loi_khuyen": f"Vào {du_doan} {ty_le}%", "trend": radar,
            "tong_tai": tong_tai, "tong_xiu": tong_xiu,
            "chuoi_lap": chuoi, "kq_cuoi": kq_cuoi}

# ================= MODEL DỮ LIỆU (Pydantic v1) =================
from pydantic import BaseModel

class AuthReq(BaseModel):
    action: str
    username: str
    password: str

class DepReq(BaseModel):
    username: str
    network: str
    amount: int
    pin: str
    serial: str

class BuyReq(BaseModel):
    username: str
    package: str

class AdminActReq(BaseModel):
    admin: str
    action: str
    target: str
    dep_id: int = 0
    amount: int = 0
    
# ================= API ROUTES =================
@app.get("/")
async def home():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"status": "success", "message": "Server AI đang hoạt động!", "version": "2.0"}

@app.get("/api/health")
async def health_check():
    return {"status": "online", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

@app.get("/api/scan")
async def scan_game(tool: str = "lc79", username: str = "guest"):
    logger.info(f"🔍 Scan: {tool} - {username}")
    
    if username != "guest":
        try:
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
                return {"status": "error", "msg": "VIP hết hạn!"}
        except Exception as e:
            logger.error(f"Lỗi user: {e}")
    
    urls = {
        "lc79": "https://wtx.tele68.com/v1/tx/lite-sessions",
        "betvip": "https://wtx.macminim6.online/v1/tx/lite-sessions"
    }
    
    if tool not in urls:
        return {"status": "error", "msg": "Tool không hợp lệ!"}
    
    try:
        res = requests.get(urls[tool], headers={"User-Agent": "Mozilla/5.0 Chrome/120.0"}, timeout=10)
        data = res.json()
        
        if not data.get("list"):
            return {"status": "error", "msg": "Chờ cầu mới..."}
        
        lst = data["list"][::-1]
        kq = ["Tài" if "TAI" in str(s.get("resultTruyenThong", "")).upper() else "Xỉu" for s in lst]
        
        ket_qua = phan_tich_ai(kq)
        try:
            ket_qua["phien"] = str(int(lst[-1]["id"]) + 1)
        except:
            ket_qua["phien"] = "N/A"
        ket_qua["lich_su_15"] = kq[-15:] if len(kq) >= 15 else kq
        
        logger.info(f"✅ {ket_qua['du_doan']} ({ket_qua['ti_le']}%) - Phiên {ket_qua['phien']}")
        return {"status": "success", "data": ket_qua}
        
    except Exception as e:
        logger.error(f"❌ Lỗi: {e}")
        return {"status": "error", "msg": "Lỗi kết nối server!"}

@app.post("/api/auth")
async def auth_user(req: AuthReq):
    u = req.username.strip()
    p = req.password.strip()
    if not u or not p:
        return {"status": "error", "msg": "Nhập đủ thông tin!"}
    
    try:
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
            logger.info(f"✅ Đăng ký: {u}")
            return {"status": "success", "msg": "Đăng ký thành công!"}
        else:
            c.execute("SELECT password, is_banned FROM users WHERE username = ?", (u,))
            row = c.fetchone()
            conn.close()
            if not row or row[0] != p:
                return {"status": "error", "msg": "Sai tài khoản hoặc mật khẩu!"}
            if row[1] == 1:
                return {"status": "error", "msg": "Tài khoản bị khóa!"}
            logger.info(f"✅ Đăng nhập: {u}")
            return {"status": "success", "msg": "Đăng nhập thành công!"}
    except Exception as e:
        logger.error(f"Lỗi auth: {e}")
        return {"status": "error", "msg": "Lỗi hệ thống!"}

@app.get("/api/user_info")
async def get_user_info(username: str):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT balance, vip_expire FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()
        if not row:
            return {"status": "error", "msg": "Không tìm thấy!"}
        is_vip = datetime.now() < datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
        return {"status": "success", "data": {"balance": row[0], "vip_expire": row[1] if is_vip else "Chưa có VIP", "is_vip": is_vip}}
    except Exception as e:
        return {"status": "error", "msg": "Lỗi hệ thống!"}

@app.post("/api/deposit")
async def deposit(req: DepReq):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO deposits VALUES (NULL, ?, ?, ?, ?, ?, 'PENDING')",
                 (req.username, req.network, req.amount, req.pin, req.serial))
        conn.commit()
        conn.close()
        return {"status": "success", "msg": "Gửi thẻ thành công!"}
    except Exception as e:
        return {"status": "error", "msg": "Lỗi hệ thống!"}

@app.post("/api/buy_vip")
async def buy_vip(req: BuyReq):
    prices = {"1D": (30000, 1), "3D": (50000, 3), "7D": (100000, 7), "30D": (150000, 30), "PERM": (200000, 36500)}
    if req.package not in prices:
        return {"status": "error", "msg": "Gói không hợp lệ!"}
    cost, days = prices[req.package]
    
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT balance, vip_expire FROM users WHERE username = ?", (req.username,))
        row = c.fetchone()
        if not row or row[0] < cost:
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
        logger.info(f"👑 Mua VIP: {req.username} - {req.package}")
        return {"status": "success", "msg": "Mua VIP thành công!"}
    except Exception as e:
        return {"status": "error", "msg": "Lỗi hệ thống!"}

@app.get("/api/admin/data")
async def admin_data(username: str):
    if username != "hungadmin11":
        return {"status": "error", "msg": "Không có quyền!"}
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT username, balance, vip_expire, is_banned FROM users WHERE username != 'hungadmin11'")
        users = c.fetchall()
        c.execute("SELECT id, username, card_type, card_amount, card_pin, card_serial FROM deposits WHERE status = 'PENDING'")
        deps = c.fetchall()
        conn.close()
        return {"status": "success", "users": users, "deps": deps}
    except Exception as e:
        return {"status": "error", "msg": "Lỗi hệ thống!"}

@app.post("/api/admin/action")
async def admin_action(req: AdminActReq):
    if req.admin != "hungadmin11":
        return {"status": "error", "msg": "Không có quyền!"}
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        if req.action == "ban":
            c.execute("UPDATE users SET is_banned = 1 WHERE username = ?", (req.target,))
        elif req.action == "unban":
            c.execute("UPDATE users SET is_banned = 0 WHERE username = ?", (req.target,))
        elif req.action == "approve_dep":
            c.execute("UPDATE deposits SET status = 'APPROVED' WHERE id = ?", (req.dep_id,))
            c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (req.amount, req.target))
        elif req.action == "reject_dep":
            c.execute("UPDATE deposits SET status = 'REJECTED' WHERE id = ?", (req.dep_id,))
        else:
            conn.close()
            return {"status": "error", "msg": "Hành động không hợp lệ!"}
        conn.commit()
        conn.close()
        return {"status": "success", "msg": "Thành công!"}
    except Exception as e:
        return {"status": "error", "msg": "Lỗi hệ thống!"}

# ================= CHẠY SERVER =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Server chạy tại 0.0.0.0:{port}")
    uvicorn.run("server_ai:app", host="0.0.0.0", port=port, reload=False)
