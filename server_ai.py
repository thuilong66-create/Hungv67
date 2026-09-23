"""
SERVER AI - HỆ THỐNG DỰ ĐOÁN TÀI XỈU
Đã được sửa chữa & tối ưu hóa để deploy lên web
Author: Hưng Admin
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import uvicorn
import sqlite3
import os
import logging
from datetime import datetime, timedelta

# ================= CẤU HÌNH LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================= KHỞI TẠO APP =================
app = FastAPI(title="Hệ thống AI Dự đoán Tài Xỉu", version="2.0")

# Cấu hình CORS - cho phép tất cả (để frontend gọi từ bất kỳ đâu)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= CẤU HÌNH DATABASE =================
DB_FILE = os.environ.get("DB_FILE", "hethong_vip.db")

def khoi_tao_db():
    """Khởi tạo database và các bảng cần thiết"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Bảng users
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY, 
            password TEXT, 
            balance INTEGER DEFAULT 0, 
            vip_expire DATETIME DEFAULT '2000-01-01 00:00:00', 
            is_banned INTEGER DEFAULT 0
        )''')
        
        # Bảng deposits
        c.execute('''CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT, 
            card_type TEXT, 
            card_amount INTEGER, 
            card_pin TEXT, 
            card_serial TEXT, 
            status TEXT DEFAULT 'PENDING'
        )''')
        
        # Tạo tài khoản admin mặc định nếu chưa có
        c.execute("SELECT username FROM users WHERE username = ?", ('hungadmin11',))
        if not c.fetchone():
            c.execute(
                "INSERT INTO users (username, password, balance, vip_expire, is_banned) VALUES (?, ?, ?, ?, ?)",
                ('hungadmin11', 'hungki98', 999999999, '2099-12-31 23:59:59', 0)
            )
            logger.info("✅ Đã tạo tài khoản admin mặc định: hungadmin11")
        
        conn.commit()
        conn.close()
        logger.info("✅ Database khởi tạo thành công")
    except Exception as e:
        logger.error(f"❌ Lỗi khởi tạo database: {str(e)}")

# Gọi khởi tạo DB khi server chạy
khoi_tao_db()

# ================= THUẬT TOÁN AI CHÍNH =================
def phan_tich_ai(kq_list):
    """
    Thuật toán phân tích và dự đoán Tài/Xỉu
    Logic: 
    - Tìm độ dài chuỗi lặp lại của kết quả cuối
    - Dự đoán ngược lại với kết quả cuối
    - Tỷ lệ tăng theo độ dài chuỗi lặp
    """
    tong_tai = kq_list.count("Tài")
    tong_xiu = kq_list.count("Xỉu")
    
    # Nếu chưa đủ dữ liệu
    if len(kq_list) < 5:
        return {
            "du_doan": "WAIT",
            "ti_le": 0,
            "loi_khuyen": "Đang nạp Data...",
            "trend": "...",
            "tong_tai": tong_tai,
            "tong_xiu": tong_xiu,
            "chuoi_lap": 0,
            "kq_cuoi": "..."
        }
    
    # Tìm độ dài chuỗi lặp lại của kết quả cuối cùng
    kq_cuoi = kq_list[-1]
    chuoi = 1
    for i in range(len(kq_list) - 2, -1, -1):
        if kq_list[i] == kq_cuoi:
            chuoi += 1
        else:
            break
    
    # Dự đoán: NGƯỢC LẠI với kết quả cuối cùng
    du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
    
    # Tính tỷ lệ dự đoán
    if chuoi >= 3:
        ty_le = min(50 + chuoi * 5, 99)
    else:
        ty_le = 60.0
    
    # Tạo radar hiển thị 12 kết quả gần nhất
    radar = "".join(["🔴" if x == "Tài" else "🔵" for x in kq_list[-12:]])
    
    return {
        "du_doan": du_doan,
        "ti_le": round(ty_le, 1),
        "loi_khuyen": f"Vào {du_doan} {ty_le}%",
        "trend": radar,
        "tong_tai": tong_tai,
        "tong_xiu": tong_xiu,
        "chuoi_lap": chuoi,
        "kq_cuoi": kq_cuoi
    }

# ================= MODEL DỮ LIỆU =================
class AuthReq(BaseModel):
    action: str  # "login" hoặc "register"
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

@app.get("/", tags=["Trang chủ"])
async def home():
    """Trả về trang web chính"""
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Server AI đang hoạt động!",
            "version": "2.0",
            "docs": "/docs"
        }
    )

@app.get("/api/health", tags=["Kiểm tra"])
async def health_check():
    """Kiểm tra trạng thái server"""
    return {"status": "online", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

@app.get("/api/scan", tags=["AI Dự đoán"])
async def scan_game(tool: str = "lc79", username: str = "guest"):
    """
    Quét và dự đoán kết quả phiên tiếp theo
    tool: "lc79" hoặc "betvip"
    """
    logger.info(f"🔍 Scan request: tool={tool}, user={username}")
    
    # Kiểm tra tài khoản (nếu không phải guest)
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
                return {"status": "error", "msg": "Tài khoản đã bị Admin khóa!"}
            if datetime.now() > datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S"):
                return {"status": "error", "msg": "Gói VIP đã hết hạn! Vui lòng mua thêm."}
        except Exception as e:
            logger.error(f"Lỗi kiểm tra user: {str(e)}")
    
    # Xác định URL API
    if tool == "lc79":
        url = "https://wtx.tele68.com/v1/tx/lite-sessions"
    elif tool == "betvip":
        url = "https://wtx.macminim6.online/v1/tx/lite-sessions"
    else:
        return {"status": "error", "msg": "Tool không hợp lệ!"}
    
    # Gọi API lấy dữ liệu
    try:
        res = requests.get(
            url, 
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"},
            timeout=10
        )
        res.raise_for_status()
        data = res.json()
        
        if not data.get("list"):
            return {"status": "error", "msg": "Chờ cầu mới..."}
        
        # Đảo ngược danh sách: từ cũ → mới
        lst = data["list"][::-1]
        
        # Chuyển đổi kết quả thành Tài/Xỉu
        kq = []
        for s in lst:
            result = str(s.get("resultTruyenThong", "")).upper()
            if "TAI" in result:
                kq.append("Tài")
            else:
                kq.append("Xỉu")
        
        # Phân tích AI
        du_doan = phan_tich_ai(kq)
        
        # Thêm số phiên tiếp theo
        try:
            du_doan["phien"] = str(int(lst[-1]["id"]) + 1)
        except:
            du_doan["phien"] = "N/A"
        
        # Thêm lịch sử 15 phiên gần nhất
        du_doan["lich_su_15"] = kq[-15:] if len(kq) >= 15 else kq
        
        logger.info(f"✅ Dự đoán xong: {du_doan['du_doan']} ({du_doan['ti_le']}%) - Phiên {du_doan['phien']}")
        
        return {"status": "success", "data": du_doan}
        
    except requests.exceptions.Timeout:
        logger.error(f"⏱️ Timeout kết nối {tool}")
        return {"status": "error", "msg": "Kết nối quá thời gian! Thử lại sau."}
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Lỗi kết nối API: {str(e)}")
        return {"status": "error", "msg": "Bảo trì Server hoặc lỗi kết nối!"}
    except Exception as e:
        logger.error(f"❌ Lỗi không xác định: {str(e)}")
        return {"status": "error", "msg": f"Lỗi hệ thống: {str(e)}"}

@app.post("/api/auth", tags=["Xác thực"])
async def auth_user(req: AuthReq):
    """Đăng nhập / Đăng ký"""
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
            
            c.execute(
                "INSERT INTO users (username, password, balance, vip_expire, is_banned) VALUES (?, ?, 0, '2000-01-01 00:00:00', 0)",
                (u, p)
            )
            conn.commit()
            conn.close()
            logger.info(f"✅ Đăng ký thành công: {u}")
            return {"status": "success", "msg": "Đăng ký thành công!"}
        
        else:  # login
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
        logger.error(f"Lỗi auth: {str(e)}")
        return {"status": "error", "msg": "Lỗi hệ thống!"}

@app.get("/api/user_info", tags=["Người dùng"])
async def get_user_info(username: str):
    """Lấy thông tin người dùng"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT balance, vip_expire FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return {"status": "error", "msg": "Không tìm thấy tài khoản!"}
        
        is_vip = datetime.now() < datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
        return {
            "status": "success",
            "data": {
                "balance": row[0],
                "vip_expire": row[1] if is_vip else "Chưa có VIP",
                "is_vip": is_vip
            }
        }
    except Exception as e:
        logger.error(f"Lỗi lấy user info: {str(e)}")
        return {"status": "error", "msg": "Lỗi hệ thống!"}

@app.post("/api/deposit", tags=["Thanh toán"])
async def deposit(req: DepReq):
    """Gửi thẻ nạp"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            "INSERT INTO deposits (username, card_type, card_amount, card_pin, card_serial, status) VALUES (?, ?, ?, ?, ?, 'PENDING')",
            (req.username, req.network, req.amount, req.pin, req.serial)
        )
        conn.commit()
        conn.close()
        logger.info(f"💳 Gửi thẻ: {req.username} - {req.network} {req.amount}")
        return {"status": "success", "msg": "Gửi thẻ thành công! Chờ Admin duyệt."}
    except Exception as e:
        logger.error(f"Lỗi deposit: {str(e)}")
        return {"status": "error", "msg": "Lỗi hệ thống!"}

@app.post("/api/buy_vip", tags=["Thanh toán"])
async def buy_vip(req: BuyReq):
    """Mua gói VIP"""
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
    
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT balance, vip_expire FROM users WHERE username = ?", (req.username,))
        row = c.fetchone()
        
        if not row:
            conn.close()
            return {"status": "error", "msg": "Tài khoản không tồn tại!"}
        
        if row[0] < cost:
            conn.close()
            return {"status": "error", "msg": "Không đủ tiền! Vui lòng nạp thêm."}
        
        now = datetime.now()
        curr_exp = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
        base_time = curr_exp if curr_exp > now else now
        new_exp = base_time + timedelta(days=days)
        
        c.execute(
            "UPDATE users SET balance = balance - ?, vip_expire = ? WHERE username = ?",
            (cost, new_exp.strftime("%Y-%m-%d %H:%M:%S"), req.username)
        )
        conn.commit()
        conn.close()
        
        logger.info(f"👑 Mua VIP: {req.username} - Gói {req.package}")
        return {"status": "success", "msg": "Mua VIP thành công!"}
    
    except Exception as e:
        logger.error(f"Lỗi mua VIP: {str(e)}")
        return {"status": "error", "msg": "Lỗi hệ thống!"}

@app.get("/api/admin/data", tags=["Admin"])
async def admin_data(username: str):
    """Lấy dữ liệu admin"""
    if username != "hungadmin11":
        return {"status": "error", "msg": "Không có quyền truy cập!"}
    
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
        logger.error(f"Lỗi admin data: {str(e)}")
        return {"status": "error", "msg": "Lỗi hệ thống!"}

@app.post("/api/admin/action", tags=["Admin"])
async def admin_action(req: AdminActReq):
    """Thực hiện hành động admin"""
    if req.admin != "hungadmin11":
        return {"status": "error", "msg": "Không có quyền truy cập!"}
    
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        if req.action == "ban":
            c.execute("UPDATE users SET is_banned = 1 WHERE username = ?", (req.target,))
            logger.info(f"🔨 Khóa tài khoản: {req.target}")
        
        elif req.action == "unban":
            c.execute("UPDATE users SET is_banned = 0 WHERE username = ?", (req.target,))
            logger.info(f"🔓 Mở khóa tài khoản: {req.target}")
        
        elif req.action == "approve_dep":
            c.execute("UPDATE deposits SET status = 'APPROVED' WHERE id = ?", (req.dep_id,))
            c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (req.amount, req.target))
            logger.info(f"✅ Duyệt nạp: {req.target} +{req.amount}")
        
        elif req.action == "reject_dep":
            c.execute("UPDATE deposits SET status = 'REJECTED' WHERE id = ?", (req.dep_id,))
            logger.info(f"❌ Từ chối nạp: ID={req.dep_id}")
        
        else:
            conn.close()
            return {"status": "error", "msg": "Hành động không hợp lệ!"}
        
        conn.commit()
        conn.close()
        return {"status": "success", "msg": "Thực hiện thành công!"}
    
    except Exception as e:
        logger.error(f"Lỗi admin action: {str(e)}")
        return {"status": "error", "msg": "Lỗi hệ thống!"}

# ================= CHẠY SERVER =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    logger.info(f"🚀 Server khởi động tại {host}:{port}")
    uvicorn.run("server_ai:app", host=host, port=port, reload=False)
