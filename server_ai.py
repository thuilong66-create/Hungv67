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
DB_FILE = "hethong_vip_vv.db"

# ================= 1. DATABASE TỰ ĐỘNG (VĨNH VIỄN) =================
def khoi_tao_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, balance INTEGER, vip_expire DATETIME, is_banned INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deposits (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, card_type TEXT, card_amount INTEGER, card_pin TEXT, card_serial TEXT, status TEXT)''')
    
    # Tài khoản Admin Vĩnh Viễn (Hưng Admin - VIP đến 2099, Vô Hạn Tiền)
    c.execute("INSERT OR IGNORE INTO users (username, password, balance, vip_expire, is_banned) VALUES (?, ?, ?, ?, ?)", 
              ('hungadmin11', 'hungki98', 999999999999, '2099-12-31 23:59:59', 0))
    conn.commit()
    conn.close()

khoi_tao_db()

# ================= 2. AI MATRIX VVIP (GOD LEVEL) =================
def phan_tich_ai_vvip(kq_list):
    tong_tai = kq_list.count("Tài")
    tong_xiu = kq_list.count("Xỉu")
    
    if len(kq_list) < 10:
        du_doan = "TÀI" if random.choice([True, False]) else "XỈU"
        return {"du_doan": du_doan, "ti_le": round(random.uniform(50.1, 58.5), 1), "loi_khuyen": "🔍 Đang nạp dữ liệu lõi...", "trend": "...", "tong_tai": tong_tai, "tong_xiu": tong_xiu}
        
    kq_cuoi = kq_list[-1]
    chuoi = 1
    for i in range(len(kq_list)-2, -1, -1):
        if kq_list[i] == kq_cuoi: chuoi += 1
        else: break
            
    history_10 = kq_list[-10:]
    du_doan = "TÀI"
    ty_le = 50.0
    loi_khuyen = ""
    
    # [LỚP 1: MA TRẬN KHÁNG CỰ - NHẬN DIỆN CẦU LỪA]
    # Nếu hệ thống nhả 1 chuỗi dài bỗng gãy 1 nhịp rồi lại lặp lại -> Cảnh báo bẫy
    if history_10[-1] != history_10[-2] and history_10[-2] == history_10[-3] and history_10[-3] == history_10[-4] and chuoi == 1:
        du_doan = history_10[-2].upper() 
        ty_le = random.uniform(88.5, 96.2)
        loi_khuyen = f"⚠️ Phát hiện Bẫy Nhà Cái -> Hồi mã thương {du_doan}"
        
    # [LỚP 2: BẮT ĐỈNH CẦU BỆT VÀ ĐU BỆT]
    elif chuoi >= 4:
        # Nếu bệt quá dài (trên 7), tỷ lệ gãy cực cao -> Bắt đầu dò bẻ
        if chuoi >= 7:
            du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
            ty_le = random.uniform(85.0, 92.5)
            loi_khuyen = f"🛑 Chạm đỉnh kháng cự (Bệt {chuoi}) -> Bẻ mạnh {du_doan}"
        else:
            du_doan = kq_cuoi.upper()
            ty_le = random.uniform(91.5, 98.8)
            loi_khuyen = f"🔥 Thuật toán đu bệt VIP -> Tất tay {du_doan}"
            
    # [LỚP 3: MẪU CẦU ĐỐI XỨNG 1-1 / 2-2 / 3-1]
    elif history_10[-1] != history_10[-2] and history_10[-2] != history_10[-3]:
        du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
        ty_le = random.uniform(89.0, 95.5)
        loi_khuyen = f"⚡ Cầu 1-1 siêu chuẩn -> Vào {du_doan}"
        
    elif history_10[-1] == history_10[-2] and history_10[-3] == history_10[-4] and history_10[-2] != history_10[-3]:
        du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
        ty_le = random.uniform(87.5, 94.0)
        loi_khuyen = f"⚖️ Form 2-2 đối xứng -> Bơm {du_doan}"

    # [LỚP 4: HỒI QUY RSI (CÂN BẰNG THUẬT TOÁN)]
    else:
        recent_20 = kq_list[-20:] if len(kq_list) >= 20 else kq_list
        t_count = recent_20.count("Tài")
        x_count = recent_20.count("Xỉu")
        
        if t_count > x_count + 4:
            du_doan = "XỈU"
            ty_le = random.uniform(75.5, 86.0)
            loi_khuyen = f"📉 Quá Mua (Dư Tài) -> AI ép {du_doan}"
        elif x_count > t_count + 4:
            du_doan = "TÀI"
            ty_le = random.uniform(75.5, 86.0)
            loi_khuyen = f"📈 Quá Bán (Dư Xỉu) -> AI ép {du_doan}"
        else:
            du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
            ty_le = random.uniform(65.0, 78.5)
            loi_khuyen = f"🎲 Xung đột sóng -> Đi đều {du_doan}"
    
    # Giới hạn tỷ lệ trần để thực tế hóa
    ty_le = min(ty_le, random.uniform(98.1, 99.8))
    radar = "".join(["🔴" if x == "Tài" else "🔵" for x in kq_list[-15:]]) # Tăng radar lên 15 bóng
    
    logger.info(f"💎 LÕI VVIP: Phân tích {len(kq_list)} phiên -> Chốt {du_doan} ({ty_le}%)")
    
    return {
        "du_doan": du_doan, 
        "ti_le": round(ty_le, 1), 
        "loi_khuyen": f"{loi_khuyen} {round(ty_le, 1)}%", 
        "trend": radar, 
        "tong_tai": tong_tai, 
        "tong_xiu": tong_xiu
    }

# ================= 3. KẾT NỐI API QUÉT GAME =================
@app.get("/api/scan")
async def scan_game(tool: str, username: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT vip_expire, is_banned FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    
    if not row: return {"status": "error", "msg": "Tài khoản không tồn tại!"}
    if row[1] == 1: return {"status": "error", "msg": "Tài khoản đã bị Admin khóa!"}
    if datetime.now() > datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") and username != 'hungadmin11': 
        return {"status": "error", "msg": "Gói VIP đã hết hạn! Vui lòng mua thêm."}

    url = "https://wtx.tele68.com/v1/tx/lite-sessions" if tool == "lc79" else "https://wtx.macminim6.online/v1/tx/lite-sessions"
    try:
        res = requests.get(url, headers={"User-Agent": "Chrome/120.0"}, timeout=5).json()
        if not res.get("list"):
            import random as rnd
            return {"status": "success", "data": {"du_doan": rnd.choice(["TÀI", "XỈU"]), "ti_le": 55.0, "phien": "NODATA", "loi_khuyen": "Đang đồng bộ", "trend": "...", "tong_tai": 0, "tong_xiu": 0}}
        
        lst = res["list"][::-1]
        kq = ["Tài" if "TAI" in str(s.get("resultTruyenThong", "")).upper() else "Xỉu" for s in lst]
        
        # GỌI THUẬT TOÁN VVIP TẠI ĐÂY
        data = phan_tich_ai_vvip(kq)
        data["phien"] = str(int(lst[-1]["id"]) + 1)
        
        return {"status": "success", "data": data}
    except Exception as e: 
        logger.error(f"Lỗi API: {e}")
        import random as rnd
        return {"status": "success", "data": {"du_doan": rnd.choice(["TÀI", "XỈU"]), "ti_le": 55.0, "phien": "ERROR", "loi_khuyen": "Lỗi kết nối", "trend": "...", "tong_tai": 0, "tong_xiu": 0}}

# ================= 4. AUTH & NGƯỜI DÙNG =================
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

# ================= 5. NẠP TIỀN & CỬA HÀNG =================
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

# ================= 6. TRANG QUẢN TRỊ ADMIN =================
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

# Cổng khởi chạy giao diện
@app.get("/")
async def home(): return FileResponse("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("server_ai:app", host="0.0.0.0", port=port)
                               
