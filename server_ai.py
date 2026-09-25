from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, uvicorn, sqlite3, os, random, logging
from datetime import datetime, timedelta
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
DB_FILE = "hethong_vip.db"

# ================= KHO DATA MỚI =================
def khoi_tao_db():
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, balance INTEGER, vip_expire DATETIME, is_banned INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deposits (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, card_type TEXT, card_amount INTEGER, card_pin TEXT, card_serial TEXT, status TEXT)''')
    # Tạo tài khoản Admin mặc định
    c.execute("INSERT OR IGNORE INTO users (username, password, balance, vip_expire, is_banned) VALUES (?, ?, ?, ?, ?)", ('hungadmin11', 'hungki98', 999999999, '2099-12-31 23:59:59', 0))
    conn.commit(); conn.close()
khoi_tao_db()

# ================= AI LOGIC =================
def phan_tich_ai(kq_list):
    tong_tai = kq_list.count("Tài"); tong_xiu = kq_list.count("Xỉu")
    if len(kq_list) < 5:
        du_doan = "TÀI" if kq_list[-1] == "Xỉu" else "XỈU"
        return {"du_doan": du_doan, "ti_le": 55.0, "loi_khuyen": f"Vào {du_doan}", "trend": "...", "tong_tai": tong_tai, "tong_xiu": tong_xiu}
    kq_cuoi = kq_list[-1]; chuoi = 1
    for i in range(len(kq_list)-2, -1, -1):
        if kq_list[i] == kq_cuoi: chuoi += 1
        else: break
    du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
    ty_le = min(50 + chuoi * 5, 99) if chuoi >= 3 else 60.0
    radar = "".join(["🔴" if x == "Tài" else "🔵" for x in kq_list[-12:]])
    logger.info(f"🎯 BẺ CẦU: chuỗi {chuoi}p {kq_cuoi} → {du_doan} | {ty_le}%")
    return {"du_doan": du_doan, "ti_le": round(ty_le, 1), "loi_khuyen": f"Vào {du_doan} {ty_le}%", "trend": radar, "tong_tai": tong_tai, "tong_xiu": tong_xiu}

@app.get("/api/scan")
async def scan_game(tool: str, username: str):
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("SELECT vip_expire, is_banned FROM users WHERE username = ?", (username,)); row = c.fetchone(); conn.close()
    if not row: return {"status": "error", "msg": "Tài khoản không tồn tại!"}
    if row[1] == 1: return {"status": "error", "msg": "Tài khoản đã bị Admin khóa!"}
    if datetime.now() > datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S"): return {"status": "error", "msg": "Gói VIP đã hết hạn! Vui lòng mua thêm."}

    url = "https://wtx.tele68.com/v1/tx/lite-sessions" if tool == "lc79" else "https://wtx.macminim6.online/v1/tx/lite-sessions"
    try:
        res = requests.get(url, headers={"User-Agent": "Chrome/120.0"}, timeout=5).json()
        if not res.get("list"): return {"status": "error", "msg": "Chờ cầu mới..."}
        lst = res["list"][::-1]
        kq = ["Tài" if "TAI" in str(s.get("resultTruyenThong", "")).upper() else "Xỉu" for s in lst]
        data = phan_tich_ai(kq); data["phien"] = str(int(lst[-1]["id"]) + 1)
        return {"status": "success", "data": data}
    except: return {"status": "error", "msg": "Bảo trì Server!"}

# ================= AUTH & USER =================
class AuthReq(BaseModel): action: str; username: str; password: str
@app.post("/api/auth")
async def auth_user(req: AuthReq):
    u = req.username.strip(); p = req.password.strip()
    if not u or not p: return {"status": "error", "msg": "Nhập đủ thông tin!"}
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    if req.action == "register":
        c.execute("SELECT username FROM users WHERE username = ?", (u,))
        if c.fetchone(): return {"status": "error", "msg": "Tài khoản đã tồn tại!"}
        c.execute("INSERT INTO users VALUES (?, ?, 0, '2000-01-01 00:00:00', 0)", (u, p))
        conn.commit(); conn.close(); return {"status": "success", "msg": "Đăng ký thành công!"}
    else:
        c.execute("SELECT password, is_banned FROM users WHERE username = ?", (u,))
        row = c.fetchone(); conn.close()
        if not row or row[0] != p: return {"status": "error", "msg": "Sai tài khoản hoặc mật khẩu!"}
        if row[1] == 1: return {"status": "error", "msg": "Tài khoản bị khóa!"}
        return {"status": "success", "msg": "Đăng nhập thành công!"}

@app.get("/api/user_info")
async def get_user_info(username: str):
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("SELECT balance, vip_expire FROM users WHERE username = ?", (username,)); row = c.fetchone(); conn.close()
    if not row: return {"status": "error"}
    is_vip = datetime.now() < datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
    return {"status": "success", "data": {"balance": row[0], "vip_expire": row[1] if is_vip else "Chưa có VIP", "is_vip": is_vip}}

# ================= PAYMENT & STORE =================
class DepReq(BaseModel): username: str; network: str; amount: int; pin: str; serial: str
@app.post("/api/deposit")
async def deposit(req: DepReq):
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("INSERT INTO deposits (username, card_type, card_amount, card_pin, card_serial, status) VALUES (?, ?, ?, ?, ?, 'PENDING')", 
              (req.username, req.network, req.amount, req.pin, req.serial))
    conn.commit(); conn.close()
    return {"status": "success", "msg": "Gửi thẻ thành công! Chờ Admin duyệt."}

class BuyReq(BaseModel): username: str; package: str
@app.post("/api/buy_vip")
async def buy_vip(req: BuyReq):
    prices = {"1D": (30000, 1), "3D": (50000, 3), "7D": (100000, 7), "30D": (150000, 30), "PERM": (200000, 36500)}
    if req.package not in prices: return {"status": "error", "msg": "Gói không hợp lệ!"}
    cost, days = prices[req.package]
    
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("SELECT balance, vip_expire FROM users WHERE username = ?", (req.username,)); row = c.fetchone()
    if row[0] < cost: conn.close(); return {"status": "error", "msg": "Không đủ tiền! Vui lòng nạp thêm."}
    
    now = datetime.now()
    curr_exp = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
    base_time = curr_exp if curr_exp > now else now
    new_exp = base_time + timedelta(days=days)
    
    c.execute("UPDATE users SET balance = balance - ?, vip_expire = ? WHERE username = ?", (cost, new_exp.strftime("%Y-%m-%d %H:%M:%S"), req.username))
    conn.commit(); conn.close()
    return {"status": "success", "msg": "Mua VIP thành công!"}

# ================= ADMIN PANEL =================
@app.get("/api/admin/data")
async def admin_data(username: str):
    if username != "hungadmin11": return {"status": "error"}
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("SELECT username, balance, vip_expire, is_banned FROM users WHERE username != 'hungadmin11'"); users = c.fetchall()
    c.execute("SELECT id, username, card_type, card_amount, card_pin, card_serial FROM deposits WHERE status = 'PENDING'"); deps = c.fetchall()
    conn.close()
    return {"status": "success", "users": users, "deps": deps}

class AdminActReq(BaseModel): admin: str; action: str; target: str; dep_id: int = 0; amount: int = 0
@app.post("/api/admin/action")
async def admin_action(req: AdminActReq):
    if req.admin != "hungadmin11": return {"status": "error"}
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    if req.action == "ban": c.execute("UPDATE users SET is_banned = 1 WHERE username = ?", (req.target,))
    elif req.action == "unban": c.execute("UPDATE users SET is_banned = 0 WHERE username = ?", (req.target,))
    elif req.action == "approve_dep":
        c.execute("UPDATE deposits SET status = 'APPROVED' WHERE id = ?", (req.dep_id,))
        c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (req.amount, req.target))
    elif req.action == "reject_dep": c.execute("UPDATE deposits SET status = 'REJECTED' WHERE id = ?", (req.dep_id,))
    conn.commit(); conn.close(); return {"status": "success"}

@app.get("/")
async def home(): return FileResponse("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("server_ai:app", host="0.0.0.0", port=port)
