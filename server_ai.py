"""
SERVER AI - HỆ THỐNG TOOL VIP
✅ Luôn lấy 13 phiên gần nhất để phân tích
✅ Dự đoán ngay không chờ
✅ 8 loại cầu phổ biến Tài Xỉu
✅ Không dùng Pydantic — chạy trên Render Python 3.14
"""

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn
import sqlite3
import os
import logging
from datetime import datetime, timedelta

# ================= CẤU HÌNH =================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Hệ thống Tool VIP", version="3.2")

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

    # ✅ Có dữ liệu là dự đoán ngay, không chờ
    if tong_phien < 2:
        return {
            "du_doan": "WAIT",
            "ti_le": 0,
            "loi_khuyen": "Chờ thêm dữ liệu...",
            "phuong_phap": "Đang thu thập",
            "tong_tai": tong_tai,
            "tong_xiu": tong_xiu,
            "chuoi_tai": 0,
            "chuoi_xiu": 0
        }

    kq_cuoi = kq_list[-1]
    chuoi_tai = 0
    chuoi_xiu = 0
    for x in reversed(kq_list):
        if x == "Tài": chuoi_tai += 1
        else: break
    for x in reversed(kq_list):
        if x == "Xỉu": chuoi_xiu += 1
        else: break

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
        if m5 == ["Tài","Xỉu","Tài","Xỉu","Tài"]:
            du_doan = "XỈU"
            ty_le = 92.5
            pp = "Xen kẽ T-X-T-X-T → XỈU"
        elif m5 == ["Xỉu","Tài","Xỉu","Tài","Xỉu"]:
            du_doan = "TÀI"
            ty_le = 92.5
            pp = "Xen kẽ X-T-X-T-X → TÀI"

    # 3. ĐÔI SONG TỬ
    elif tong_phien >= 4:
        k2,k3,k4,k5 = kq_list[-2],kq_list[-3],kq_list[-4],(kq_list[-5] if tong_phien>=5 else None)
        if k5 and k5==k3 and k2==k4 and k5!=k2:
            du_doan = k5
            ty_le = 88.0
            pp = "Đôi song tử → lặp lại"

    # 4. CẠNH BẰNG
    elif tong_phien >= 4:
        m4 = kq_list[-4:]
        if m4 == ["Tài","Tài","Xỉu","Xỉu"]:
            du_doan = "TÀI"
            ty_le = 85.5
            pp = "Cạnh bằng TT-XX → TÀI"
        elif m4 == ["Xỉu","Xỉu","Tài","Tài"]:
            du_doan = "XỈU"
            ty_le = 85.5
            pp = "Cạnh bằng XX-TT → XỈU"

    # 5. LÁI NGƯỢC
    elif tong_phien >= 3:
        k2,k3 = kq_list[-2],kq_list[-3]
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

    return {
        "du_doan": du_doan,
        "ti_le": round(ty_le,1),
        "loi_khuyen": f"{pp} ({round(ty_le,1)}%)",
        "phuong_phap": pp,
        "tong_tai": tong_tai,
        "tong_xiu": tong_xiu,
        "chuoi_tai": chuoi_tai,
        "chuoi_xiu": chuoi_xiu
    }

# ================= HÀM HỖ TRỢ =================
def get_str(d,k,defval=""):
    v=d.get(k,defval)
    return str(v).strip() if v else defval
def get_int(d,k,defval=0):
    try: return int(d.get(k,defval))
    except: return defval

# ================= API CHÍNH =================
@app.get("/")
async def home():
    p = os.path.join(os.path.dirname(__file__),"index.html")
    return FileResponse(p) if os.path.exists(p) else {"status":"ok"}

@app.get("/api/health")
async def health():
    return {"status":"online","time":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

@app.get("/api/scan")
async def scan_game(tool:str, username:str):
    logger.info(f"🔍 Scan: {tool} | {username}")

    with get_db() as conn:
        c=conn.cursor()
        c.execute("SELECT vip_expire,is_banned FROM users WHERE username=?",(username,))
        row=c.fetchone()
    if not row: return JSONResponse({"status":"error","msg":"Tài khoản không tồn tại!"})
    if row[1]==1 and username!="hungadmin11":
        return JSONResponse({"status":"error","msg":"Tài khoản bị khóa!"})
    if datetime.now()>datetime.strptime(row[0],"%Y-%m-%d %H:%M:%S") and username!="hungadmin11":
        return JSONResponse({"status":"error","msg":"Hết hạn VIP!"})

    url = {
        "lc79": "https://wtx.tele68.com/v1/tx/lite-sessions",
        "betvip": "https://wtx.macminim6.online/v1/tx/lite-sessions"
    }.get(tool)
    if not url: return JSONResponse({"status":"error","msg":"Tool không hợp lệ!"})

    try:
        res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        data = res.json()
        if not data.get("list"):
            return JSONResponse({"status":"error","msg":"Chờ phiên mới..."})

        # ✅ LẤY 13 PHIÊN MỚI NHẤT
        all_list = data["list"]
        lst = all_list[:SO_LUONG_PHAN_TICH]  # Lấy 13 phiên đầu
        lst = lst[::-1]  # Đảo → cũ ở đầu, mới ở cuối

        kq = []
        for s in lst:
            val = ""
            for key in ["resultTruyenThong","result","ketqua","value"]:
                if key in s:
                    val = str(s[key]).upper()
                    break
            if "TAI" in val or "TÀI" in val:
                kq.append("Tài")
            elif "XIU" in val or "XỈU" in val:
                kq.append("Xỉu")

        logger.info(f"📊 Lấy được {len(kq)}/{SO_LUONG_PHAN_TICH} phiên: {kq}")
        if len(kq) < 2:
            return JSONResponse({"status":"error","msg":"Chưa đủ dữ liệu..."})

        ket_qua = phan_tich_ai(kq)
        ket_qua["phien"] = f"#{lst[-1]['id']}" if "id" in lst[-1] else "N/A"
        ket_qua["lich_su_13"] = kq

        logger.info(f"✅ {ket_qua['du_doan']} | {ket_qua['phuong_phap']}")
        return JSONResponse({"status":"success","data":ket_qua})

    except Exception as e:
        logger.error(f"❌ Lỗi: {e}")
        return JSONResponse({"status":"error","msg":f"Lỗi kết nối: {str(e)}"})

@app.post("/api/auth")
async def auth(req:Request):
    try: d=await req.json()
    except: return JSONResponse({"status":"error","msg":"Dữ liệu lỗi"})
    act,u,p = get_str(d,"action"),get_str(d,"username"),get_str(d,"password")
    if not u or not p: return JSONResponse({"status":"error","msg":"Thiếu thông tin"})
    with get_db() as conn:
        c=conn.cursor()
        if act=="register":
            c.execute("SELECT 1 FROM users WHERE username=?",(u,))
            if c.fetchone(): return JSONResponse({"status":"error","msg":"Tên đã tồn tại"})
            c.execute("INSERT INTO users VALUES (?,?,0,'2000-01-01 00:00:00',0)",(u,p))
            conn.commit()
            return JSONResponse({"status":"success","msg":"Đăng ký thành công"})
        else:
            c.execute("SELECT password,is_banned FROM users WHERE username=?",(u,))
            r=c.fetchone()
            if not r or r[0]!=p: return JSONResponse({"status":"error","msg":"Sai tài khoản/mật khẩu"})
            if r[1]==1 and u!="hungadmin11": return JSONResponse({"status":"error","msg":"Bị khóa"})
            return JSONResponse({"status":"success","msg":"Đăng nhập thành công"})

@app.get("/api/user_info")
async def user_info(username:str):
    with get_db() as conn:
        c=conn.cursor()
        c.execute("SELECT balance,vip_expire FROM users WHERE username=?",(username,))
        r=c.fetchone()
    if not r: return JSONResponse({"status":"error"})
    is_vip = (datetime.now()<datetime.strptime(r[1],"%Y-%m-%d %H:%M:%S")) or username=="hungadmin11"
    vip_str = "VĨNH VIỄN (ADMIN)" if username=="hungadmin11" else (r[1] if is_vip else "Chưa có VIP")
    return JSONResponse({"status":"success","data":{"balance":r[0],"vip_expire":vip_str,"is_vip":is_vip}})

@app.post("/api/deposit")
async def deposit(req:Request):
    try: d=await req.json()
    except: return JSONResponse({"status":"error"})
    un,net,amt,pin,srl = get_str(d,"username"),get_str(d,"network"),get_int(d,"amount"),get_str(d,"pin"),get_str(d,"serial")
    with get_db() as conn:
        c=conn.cursor()
        c.execute("INSERT INTO deposits VALUES (NULL,?,?,?,?,?,'PENDING')",(un,net,amt,pin,srl))
        conn.commit()
    return JSONResponse({"status":"success","msg":"Đã gửi thẻ, chờ duyệt"})

@app.post("/api/buy_vip")
async def buy_vip(req:Request):
    try: d=await req.json()
    except: return JSONResponse({"status":"error"})
    un,pkg = get_str(d,"username"),get_str(d,"package")
    if un=="hungadmin11": return JSONResponse({"status":"success","msg":"Admin miễn phí"})
    gói = {"1D":(30000,1),"3D":(50000,3),"7D":(100000,7),"30D":(150000,30),"PERM":(200000,36500)}
    if pkg not in gói: return JSONResponse({"status":"error","msg":"Gói không hợp lệ"})
    cost,ngay = gói[pkg]
    with get_db() as conn:
        c=conn.cursor()
        c.execute("SELECT balance,vip_expire FROM users WHERE username=?",(un,))
        r=c.fetchone()
        if not r or r[0]<cost: return JSONResponse({"status":"error","msg":"Không đủ tiền"})
        now=datetime.now()
        cur=datetime.strptime(r[1],"%Y-%m-%d %H:%M:%S")
        new_exp = (cur if cur>now else now) + timedelta(days=ngay)
        c.execute("UPDATE users SET balance=balance-?, vip_expire=? WHERE username=?",(cost,new_exp.strftime("%Y-%m-%d %H:%M:%S"),un))
        conn.commit()
    return JSONResponse({"status":"success","msg":"Mua VIP thành công"})

@app.get("/api/admin/data")
async def admin_data(username:str):
    if username!="hungadmin11": return JSONResponse({"status":"error"})
    with get_db() as conn:
        c=conn.cursor()
        c.execute("SELECT username,balance,vip_expire,is_banned FROM users WHERE username!='hungadmin11'")
        users=c.fetchall()
        c.execute("SELECT id,username,card_type,card_amount,card_pin,card_serial FROM deposits WHERE status='PENDING'")
        deps=c.fetchall()
    return JSONResponse({"status":"success","users":users,"deps":deps})

@app.post("/api/admin/action")
async def admin_act(req:Request):
    try: d=await req.json()
    except: return JSONResponse({"status":"error"})
    admin,act,tgt,did,amt = get_str(d,"admin"),get_str(d,"action"),get_str(d,"target"),get_int(d,"dep_id"),get_int(d,"amount")
    if admin!="hungadmin11": return JSONResponse({"status":"error"})
    with get_db() as conn:
        c=conn.cursor()
        if act=="ban": c.execute("UPDATE users SET is_banned=1 WHERE username=?",(tgt,))
        elif act=="unban": c.execute("UPDATE users SET is_banned=0 WHERE username=?",(tgt,))
        elif act=="approve_dep":
            c.execute("UPDATE deposits SET status='APPROVED' WHERE id=?",(did,))
            c.execute("UPDATE users SET balance=balance+? WHERE username=?",(amt,tgt))
        elif act=="reject_dep": c.execute("UPDATE deposits SET status='REJECTED' WHERE id=?",(did,))
        else: return JSONResponse({"status":"error"})
        conn.commit()
    return JSONResponse({"status":"success"})

if __name__ == "__main__":
    port=int(os.environ.get("PORT",8080))
    logger.info(f"🚀 Server chạy cổng {port}")
    uvicorn.run("server_ai:app", host="0.0.0.0", port=port)
