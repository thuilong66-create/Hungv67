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
DB_FILE = "hethong_vip_learning.db"

# ================= 1. KHỞI TẠO DATABASE HỆ THỐNG & AI MEMORY =================
def khoi_tao_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Bảng người dùng & Nạp tiền
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, balance INTEGER, vip_expire DATETIME, is_banned INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deposits (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, card_type TEXT, card_amount INTEGER, card_pin TEXT, card_serial TEXT, status TEXT)''')
    
    # BẢNG BỘ NHỚ AI: Lưu trữ lịch sử dự đoán để AI tự học đúng/sai
    c.execute('''CREATE TABLE IF NOT EXISTS ai_memory (
                    phien TEXT PRIMARY KEY, 
                    du_doan TEXT, 
                    ket_qua TEXT, 
                    is_win INTEGER, 
                    pattern_type TEXT, 
                    created_at DATETIME
                )''')
    
    # Tài khoản Admin Vĩnh Viễn
    c.execute("INSERT OR IGNORE INTO users (username, password, balance, vip_expire, is_banned) VALUES (?, ?, ?, ?, ?)", 
              ('hungadmin11', 'hungki98', 999999999999, '2099-12-31 23:59:59', 0))
    conn.commit()
    conn.close()

khoi_tao_db()

# ================= 2. CƠ CHẾ HỌC MÁY & ĐỐI CHIẾU KẾT QUẢ =================
def cap_nhat_va_hoc_lich_su(lst):
    """
    Duyệt dữ liệu thực tế từ Game, đối chiếu với dự đoán cũ của AI để ghi nhận ĐÚNG/SAI
    và tính toán hiệu suất thi đấu của AI trong 30 phiên gần nhất.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    for s in lst:
        phien_id = str(s.get("id"))
        actual_kq = "TÀI" if "TAI" in str(s.get("resultTruyenThong", "")).upper() else "XỈU"
        
        c.execute("SELECT du_doan, is_win FROM ai_memory WHERE phien = ?", (phien_id,))
        row = c.fetchone()
        
        if row and row[1] is None:  # Nếu phiên này đã được AI dự đoán nhưng chưa chấm điểm
            pred = row[0]
            win_status = 1 if pred == actual_kq else 0
            c.execute("UPDATE ai_memory SET ket_qua = ?, is_win = ? WHERE phien = ?", (actual_kq, win_status, phien_id))
    
    conn.commit()
    
    # Lấy 30 phiên gần nhất AI đã chấm điểm để phân tích hiệu suất
    c.execute("SELECT is_win, pattern_type FROM ai_memory WHERE is_win IS NOT NULL ORDER BY created_at DESC LIMIT 30")
    history_records = c.fetchall()
    
    # Lấy 10 tay gần nhất ra log hiển thị UI
    c.execute("SELECT phien, du_doan, ket_qua, is_win FROM ai_memory WHERE is_win IS NOT NULL ORDER BY created_at DESC LIMIT 10")
    recent_logs = c.fetchall()
    
    conn.close()
    
    total = len(history_records)
    wins = sum(1 for r in history_records if r[0] == 1)
    win_rate = (wins / total * 100) if total > 0 else 80.0
    
    return win_rate, recent_logs, history_records

# ================= 3. THUẬT TOÁN AI DỰ ĐOÁN THÔNG MINH (SELF-LEARNING) =================
def phan_tich_ai_learning(kq_list, next_phien_id, win_rate, history_records):
    tong_tai = kq_list.count("Tài")
    tong_xiu = kq_list.count("Xỉu")
    
    if len(kq_list) < 5:
        du_doan = "TÀI" if random.choice([True, False]) else "XỈU"
        return {
            "du_doan": du_doan, "ti_le": 50.0, "loi_khuyen": "🔍 Đang nạp dữ liệu cầu...", 
            "trend": "...", "tong_tai": tong_tai, "tong_xiu": tong_xiu,
            "ai_stats": {"win_rate": 80.0, "total_sessions": 0, "logs": []}
        }
        
    kq_cuoi = kq_list[-1]
    chuoi = 1
    for i in range(len(kq_list)-2, -1, -1):
        if kq_list[i] == kq_cuoi: chuoi += 1
        else: break
            
    history_10 = kq_list[-10:]
    pattern_type = "NORMAL"
    du_doan = "TÀI"
    base_confidence = 70.0
    loi_khuyen = ""

    # [BƯỚC 1: PHÂN TÍCH HÌNH MẪU CẦU]
    # Mẫu 1: Bệt
    if chuoi >= 4:
        if chuoi >= 7:
            pattern_type = "BE_BET"
            du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
            base_confidence = 88.0
            loi_khuyen = f"🛑 Cầu Bệt {chuoi} tay quá dài -> Bẻ {du_doan}"
        else:
            pattern_type = "DU_BET"
            du_doan = kq_cuoi.upper()
            base_confidence = 92.0
            loi_khuyen = f"🔥 Thuật toán Đu Bệt {chuoi} tay -> Theo {du_doan}"
            
    # Mẫu 2: Cầu 1-1
    elif len(history_10) >= 4 and history_10[-1] != history_10[-2] and history_10[-2] != history_10[-3] and history_10[-3] != history_10[-4]:
        pattern_type = "CAU_11"
        du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
        base_confidence = 90.0
        loi_khuyen = f"⚡ Cầu 1-1 Nhịp Điệu -> Đánh {du_doan}"
        
    # Mẫu 3: Cầu 2-2
    elif len(history_10) >= 4 and history_10[-1] == history_10[-2] and history_10[-3] == history_10[-4] and history_10[-2] != history_10[-3]:
        pattern_type = "CAU_22"
        du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
        base_confidence = 86.0
        loi_khuyen = f"⚖️ Cầu 2-2 Kháng Cự -> Chọn {du_doan}"
        
    # Mẫu 4: Hồi Quy Động
    else:
        pattern_type = "HOI_QUY"
        recent_20 = kq_list[-20:] if len(kq_list) >= 20 else kq_list
        t_cnt, x_cnt = recent_20.count("Tài"), recent_20.count("Xỉu")
        if t_cnt >= x_cnt + 4:
            du_doan = "XỈU"
            base_confidence = 81.0
            loi_khuyen = f"📉 Lệch Tài (+{t_cnt - x_cnt}) -> AI Đảo {du_doan}"
        elif x_cnt >= t_cnt + 4:
            du_doan = "TÀI"
            base_confidence = 81.0
            loi_khuyen = f"📈 Lệch Xỉu (+{x_cnt - t_cnt}) -> AI Đảo {du_doan}"
        else:
            pattern_type = "FLEX"
            du_doan = "TÀI" if kq_cuoi == "Xỉu" else "XỈU"
            base_confidence = 68.0
            loi_khuyen = f"🎲 Xung đột sóng -> Đi nhẹ {du_doan}"

    # [BƯỚC 2: HỌC MÁY - TỰ ĐỘNG ĐẢO CHIỀU NẾU DẠNG CẦU ĐÓ ĐANG BỊ BẪY]
    pattern_wins = [r[0] for r in history_records if r[1] == pattern_type]
    if len(pattern_wins) >= 3:
        pattern_wr = sum(pattern_wins) / len(pattern_wins)
        if pattern_wr < 0.40:  # Dạng cầu này gần đây bị bẫy nhiều (Thắng < 40%)
            du_doan = "XỈU" if du_doan == "TÀI" else "TÀI"
            loi_khuyen = f"🧠 AI Học Tự Động: Mẫu {pattern_type} bị lừa -> Bật Đảo Chiều {du_doan}"
            base_confidence = 89.5
        else:
            base_confidence += (pattern_wr - 0.5) * 15 # Cộng thưởng niềm tin nếu thắng nhiều

    adjusted_percentage = min(max(base_confidence + random.uniform(-2.0, 3.0), 65.0), 98.9)
    
    # [BƯỚC 3: LƯU BỘ NHỚ DỰ ĐOÁN PHIÊN MỚI]
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO ai_memory (phien, du_doan, pattern_type, created_at) VALUES (?, ?, ?, ?)",
              (next_phien_id, du_doan, pattern_type, datetime.now()))
    conn.commit()
    conn.close()

    radar = "".join(["🔴" if x == "Tài" else "🔵" for x in kq_list[-15:]])

    return {
        "du_doan": du_doan,
        "ti_le": round(adjusted_percentage, 1),
        "loi_khuyen": f"{loi_khuyen} ({round(adjusted_percentage, 1)}%)",
        "trend": radar,
        "tong_tai": tong_tai,
        "tong_xiu": tong_xiu,
        "ai_stats": {
            "win_rate": round(win_rate, 1),
            "total_learned_sessions": len(history_records)
        }
    }

# ================= 4. API SCAN GAME QUÉT LỊCH SỬ real-time =================
@app.get("/api/scan")
async def scan_game(tool: str, username: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT vip_expire, is_banned FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    
    if not row: return {"status": "error", "msg": "Tài khoản không tồn tại!"}
    if row[1] == 1: return {"status": "error", "msg": "Tài khoản bị khóa!"}
    if datetime.now() > datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S"): 
        return {"status": "error", "msg": "Gói VIP hết hạn! Vui lòng nạp thêm."}

    url = "https://wtx.tele68.com/v1/tx/lite-sessions" if tool == "lc79" else "https://wtx.macminim6.online/v1/tx/lite-sessions"
    try:
        res = requests.get(url, headers={"User-Agent": "Chrome/120.0"}, timeout=5).json()
        if not res.get("list"): return {"status": "error", "msg": "Đang kết nối Server Game..."}
        
        lst = res["list"][::-1]
        kq = ["Tài" if "TAI" in str(s.get("resultTruyenThong", "")).upper() else "Xỉu" for s in lst]
        
        # 1. AI Học máy & Chấm điểm các phiên đã qua
        win_rate, recent_logs, history_records = cap_nhat_va_hoc_lich_su(lst)
        
        # 2. AI Dự đoán phiên tiếp theo
        next_phien_id = str(int(lst[-1]["id"]) + 1)
        data = phan_tich_ai_learning(kq, next_phien_id, win_rate, history_records)
        data["phien"] = next_phien_id
        data["logs"] = recent_logs  # Danh sách tay thắng/thua gần nhất
        
        return {"status": "success", "data": data}
    except Exception as e: 
        logger.error(f"Lỗi API: {e}")
        return {"status": "error", "msg": "Bảo trì máy chủ Game!"}

# ================= 5. TÀI KHOẢN & NẠP THẺ =================
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

class DepReq(BaseModel): username: str; network: str; amount: int; pin: str; serial: str
@app.post("/api/deposit")
async def deposit(req: DepReq):
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("INSERT INTO deposits (username, card_type, card_amount, card_pin, card_serial, status) VALUES (?, ?, ?, ?, ?, 'PENDING')", 
              (req.username, req.network, req.amount, req.pin, req.serial))
    conn.commit(); conn.close()
    return {"status": "success", "msg": "Gửi thẻ thành công! Chờ duyệt."}

class BuyReq(BaseModel): username: str; package: str
@app.post("/api/buy_vip")
async def buy_vip(req: BuyReq):
    prices = {"1D": (30000, 1), "3D": (50000, 3), "7D": (100000, 7), "30D": (150000, 30), "PERM": (200000, 36500)}
    if req.package not in prices: return {"status": "error", "msg": "Gói không hợp lệ!"}
    cost, days = prices[req.package]
    
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("SELECT balance, vip_expire FROM users WHERE username = ?", (req.username,)); row = c.fetchone()
    if row[0] < cost: conn.close(); return {"status": "error", "msg": "Không đủ tiền!"}
    
    now = datetime.now()
    curr_exp = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
    base_time = curr_exp if curr_exp > now else now
    new_exp = base_time + timedelta(days=days)
    
    c.execute("UPDATE users SET balance = balance - ?, vip_expire = ? WHERE username = ?", (cost, new_exp.strftime("%Y-%m-%d %H:%M:%S"), req.username))
    conn.commit(); conn.close()
    return {"status": "success", "msg": "Mua VIP thành công!"}

# ================= 6. TRANG CHỦ HOẠT ĐỘNG =================
@app.get("/")
async def home():
    # Kiểm tra đường dẫn hiển thị file HTML
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    elif os.path.exists("templates/index.html"):
        return FileResponse("templates/index.html")
    return {"status": "online", "msg": "Server AI Hưng Admin đang chạy!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
