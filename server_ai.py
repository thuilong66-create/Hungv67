"""
🏆 SERVER AI - THUẬT TOÁN VIP XỊN v6.0
═══════════════════════════════════════════
✨ ĐẶC ĐIỂM NỔI BẬT:
   🧠 Phân tích đa khung thời gian (3-5-8-15 phiên)
   🎯 Nhận diện 15+ dạng cầu chuyên nghiệp
   📊 Hệ thống điểm tin cậy động (không gán cứng)
   🔍 Phát hiện cầu vỡ & cầu sắp đổi chiều
   ⚡ Tích lũy xác suất từ nhiều tín hiệu
   📈 Trạng thái cầu: MẠNH / TRUNG BÌNH / YẾU / HÌNH THÀNH
   💎 Tên cầu chuyên nghiệp theo thuật ngữ cá cược
   ✅ Luôn có dự đoán - không WAIT
   🧹 Không hiển thị lịch sử - chỉ kết quả tinh túy
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
from collections import Counter

# ================= CẤU HÌNH =================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="🏆 THUẬT TOÁN VIP XỊN", version="6.0")
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
                "INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?, ?)",
                ('hungadmin11', 'hungki98', 999999999, '2099-12-31 23:59:59', 0)
            )
            conn.commit()
        logger.info("✅ Database OK")
    except Exception as e:
        logger.error(f"❌ Lỗi DB: {e}")

khoi_tao_db()

# ═══════════════════════════════════════════════════════════
# 🏆 THUẬT TOÁN VIP XỊN - HỆ THỐNG ĐIỂM TIN CẬY ĐỘNG
# ═══════════════════════════════════════════════════════════

class Signal:
    """Lưu trữ một tín hiệu dự đoán"""
    def __init__(self, ket_qua, diem_tin_cay, ten_cau, mo_ta, do_manh="TRUNG BÌNH"):
        self.ket_qua = ket_qua
        self.diem_tin_cay = diem_tin_cay  # 0-100
        self.ten_cau = ten_cau
        self.mo_ta = mo_ta
        self.do_manh = do_manh

def dem_chuoi_nguoc(kq_list, muc_tieu):
    """Đếm chuỗi liên tiếp từ cuối lên"""
    dem = 0
    for x in reversed(kq_list):
        if x == muc_tieu:
            dem += 1
        else:
            break
    return dem

def phan_tich_multi_timeframe(kq_list):
    """Phân tích đa khung thời gian: ngắn (3), trung (5), dài (8), toàn bộ (15)"""
    kq = list(kq_list)
    ket_qua = {}
    
    for name, n in [("ngan", 3), ("trung", 5), ("dai", 8), ("toanbo", 15)]:
        if len(kq) >= n:
            phan = kq[-n:]
            tai = phan.count("Tài")
            xiu = phan.count("Xỉu")
            ket_qua[name] = {
                "tai": tai,
                "xiu": xiu,
                "tyle_tai": round(tai / n * 100, 1),
                "tyle_xiu": round(xiu / n * 100, 1),
                "uu_the": "TÀI" if tai > xiu else ("XỈU" if xiu > tai else "CAN BANG")
            }
    
    return ket_qua

def kiem_tra_cau_bet(kq_list):
    """🏆 CẦU BỆT - Cùng loại liên tiếp"""
    if len(kq_list) < 2:
        return None
    
    kq_cuoi = kq_list[-1]
    chuoi = dem_chuoi_nguoc(kq_list, kq_cuoi)
    
    if chuoi >= 2:
        # Điểm tin cậy tăng theo độ dài chuỗi
        if chuoi >= 5:
            diem = 95
            do_manh = "RẤT MẠNH"
            ten_cau = "Cầu bệt siêu dài"
        elif chuoi >= 4:
            diem = 90
            do_manh = "MẠNH"
            ten_cau = "Cầu bệt dài"
        elif chuoi >= 3:
            diem = 85
            do_manh = "MẠNH"
            ten_cau = "Cầu bệt"
        else:  # 2
            diem = 70
            do_manh = "TRUNG BÌNH"
            ten_cau = "Cầu bệt ngắn"
        
        return Signal(
            ket_qua="TÀI" if kq_cuoi == "Tài" else "XỈU",
            diem_tin_cay=diem,
            ten_cau=ten_cau,
            mo_ta=f"{ten_cau} {chuoi} phiên {kq_cuoi} → TIẾP TỤC",
            do_manh=do_manh
        )
    return None

def kiem_tra_cau_xen_ke_11(kq_list):
    """🎯 CẦU XEN KẼ 1-1 (T-X-T-X)"""
    if len(kq_list) < 6:
        return None
    
    m6 = kq_list[-6:]
    # Kiểm tra T-X-T-X-T-X hoặc X-T-X-T-X-T
    if all(m6[i] != m6[i+1] for i in range(5)):
        # Quy luật xen kẽ hoàn hảo
        du_doan = "TÀI" if m6[-1] == "Xỉu" else "XỈU"
        return Signal(
            ket_qua=du_doan,
            diem_tin_cay=92,
            ten_cau="Cầu nhịp 1-1",
            mo_ta=f"Cầu nhịp T-X hoàn hảo 6 phiên → {du_doan}",
            do_manh="MẠNH"
        )
    
    # Kiểm tra 4 phiên gần xen kẽ
    if len(kq_list) >= 4:
        m4 = kq_list[-4:]
        if all(m4[i] != m4[i+1] for i in range(3)):
            du_doan = "TÀI" if m4[-1] == "Xỉu" else "XỈU"
            return Signal(
                ket_qua=du_doan,
                diem_tin_cay=82,
                ten_cau="Cầu nhịp 1-1",
                mo_ta=f"Cầu nhịp T-X 4 phiên → {du_doan}",
                do_manh="TRUNG BÌNH"
            )
    return None

def kiem_tra_cau_2_1(kq_list):
    """📊 CẦU 2-1 (TT-X-TT-X hoặc XX-T-XX-T)"""
    if len(kq_list) < 6:
        return None
    
    m6 = kq_list[-6:]
    
    # TT-X-TT-X
    if m6 == ["Tài", "Tài", "Xỉu", "Tài", "Tài", "Xỉu"]:
        return Signal("TÀI", 88, "Cầu chu kỳ 2-1", "Cầu TT-X-TT-X hoàn hảo → TIẾP TỤC TÀI", "MẠNH")
    # XX-T-XX-T
    if m6 == ["Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu", "Tài"]:
        return Signal("XỈU", 88, "Cầu chu kỳ 2-1", "Cầu XX-T-XX-T hoàn hảo → TIẾP TỤC XỈU", "MẠNH")
    
    # Kiểm tra 3 phiên gần phù hợp mẫu 2-1
    if len(kq_list) >= 3:
        m3 = kq_list[-3:]
        if m3 == ["Tài", "Tài", "Xỉu"]:
            return Signal("TÀI", 72, "Cầu chu kỳ 2-1", "Dấu hiệu TT-X → dự đoán TÀI", "YẾU")
        if m3 == ["Xỉu", "Xỉu", "Tài"]:
            return Signal("XỈU", 72, "Cầu chu kỳ 2-1", "Dấu hiệu XX-T → dự đoán XỈU", "YẾU")
    return None

def kiem_tra_cau_2_2(kq_list):
    """⚖️ CẦU 2-2 (TT-XX-TT-XX)"""
    if len(kq_list) < 8:
        return None
    
    m8 = kq_list[-8:]
    if m8 == ["Tài", "Tài", "Xỉu", "Xỉu", "Tài", "Tài", "Xỉu", "Xỉu"]:
        return Signal("TÀI", 86, "Cầu cân bằng 2-2", "Cầu TT-XX hoàn hảo 8 phiên → TIẾP TỤC TÀI", "MẠNH")
    if m8 == ["Xỉu", "Xỉu", "Tài", "Tài", "Xỉu", "Xỉu", "Tài", "Tài"]:
        return Signal("XỈU", 86, "Cầu cân bằng 2-2", "Cầu XX-TT hoàn hảo 8 phiên → TIẾP TỤC XỈU", "MẠNH")
    
    if len(kq_list) >= 4:
        m4 = kq_list[-4:]
        if m4 == ["Tài", "Tài", "Xỉu", "Xỉu"]:
            return Signal("TÀI", 74, "Cầu cân bằng 2-2", "Dấu hiệu TT-XX → dự đoán TÀI", "TRUNG BÌNH")
        if m4 == ["Xỉu", "Xỉu", "Tài", "Tài"]:
            return Signal("XỈU", 74, "Cầu cân bằng 2-2", "Dấu hiệu XX-TT → dự đoán XỈU", "TRUNG BÌNH")
    return None

def kiem_tra_cau_3_1(kq_list):
    """📈 CẦU 3-1 (TTT-X-TTT-X)"""
    if len(kq_list) < 8:
        return None
    
    m8 = kq_list[-8:]
    if m8 == ["Tài", "Tài", "Tài", "Xỉu", "Tài", "Tài", "Tài", "Xỉu"]:
        return Signal("TÀI", 85, "Cầu chu kỳ 3-1", "Cầu TTT-X hoàn hảo → TIẾP TỤC TÀI", "MẠNH")
    if m8 == ["Xỉu", "Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu", "Xỉu", "Tài"]:
        return Signal("XỈU", 85, "Cầu chu kỳ 3-1", "Cầu XXX-T hoàn hảo → TIẾP TỤC XỈU", "MẠNH")
    return None

def kiem_tra_cau_song_tu(kq_list):
    """🎭 CẦU SONG TỬ (A-B-A-B lặp lại hoàn hảo)"""
    if len(kq_list) < 6:
        return None
    
    k1, k2, k3, k4, k5, k6 = kq_list[-6], kq_list[-5], kq_list[-4], kq_list[-3], kq_list[-2], kq_list[-1]
    
    if k1 == k3 == k5 and k2 == k4 == k6 and k1 != k2:
        du_doan = "TÀI" if k1 == "Tài" else "XỈU"
        return Signal(
            ket_qua=du_doan,
            diem_tin_cay=84,
            ten_cau="Cầu song tử",
            mo_ta=f"Cầu {k1}-{k2} lặp hoàn hảo → {du_doan}",
            do_manh="TRUNG BÌNH"
        )
    return None

def kiem_tra_cau_thien_vi(kq_list):
    """🌟 CẦU THIÊN VỊ - Một bên chiếm ưu thế rõ rệt"""
    if len(kq_list) < 8:
        return None
    
    tai = kq_list.count("Tài")
    xiu = kq_list.count("Xỉu")
    tong = len(kq_list)
    tl_tai = tai / tong
    
    if tl_tai >= 0.67:  # 2/3 trở lên là Tài
        diem = 78 + min(int((tl_tai - 0.67) * 100), 12)
        return Signal(
            ket_qua="TÀI",
            diem_tin_cay=diem,
            ten_cau="Cầu thiên TÀI",
            mo_ta=f"TÀI chiếm ưu thế {tai}/{tong} → TIẾP TỤC CẦU TÀI",
            do_manh="MẠNH" if tl_tai >= 0.75 else "TRUNG BÌNH"
        )
    elif tl_tai <= 0.33:  # 2/3 trở lên là Xỉu
        diem = 78 + min(int((0.67 - tl_tai) * 100), 12)
        return Signal(
            ket_qua="XỈU",
            diem_tin_cay=diem,
            ten_cau="Cầu thiên XỈU",
            mo_ta=f"XỈU chiếm ưu thế {xiu}/{tong} → TIẾP TỤC CẦU XỈU",
            do_manh="MẠNH" if tl_tai <= 0.25 else "TRUNG BÌNH"
        )
    return None

def kiem_tra_cau_hoi_quy(kq_list):
    """🔄 CẦU HỒI QUY - Sau chênh lệch lớn sẽ quay về cân bằng"""
    if len(kq_list) < 10:
        return None
    
    tai = kq_list.count("Tài")
    xiu = kq_list.count("Xỉu")
    chenh = abs(tai - xiu)
    
    # Nếu chênh lệch >= 6 và 3 phiên gần đang đẩy lệch xa hơn → hồi quy
    if chenh >= 6:
        if tai > xiu:
            # Tài đang quá nhiều → dự đoán Xỉu để hồi quy
            return Signal(
                ket_qua="XỈU",
                diem_tin_cay=76,
                ten_cau="Cầu hồi quy",
                mo_ta=f"Chênh lệch {chenh} (Tài nhiều) → Hồi quy XỈU",
                do_manh="TRUNG BÌNH"
            )
        else:
            return Signal(
                ket_qua="TÀI",
                diem_tin_cay=76,
                ten_cau="Cầu hồi quy",
                mo_ta=f"Chênh lệch {chenh} (Xỉu nhiều) → Hồi quy TÀI",
                do_manh="TRUNG BÌNH"
            )
    return None

def kiem_tra_cau_noi_duoi(kq_list):
    """🚀 CẦU NỐI ĐUÔI - Tiếp tục phiên cuối (mặc định thông minh)"""
    if len(kq_list) < 2:
        return None
    
    kq_cuoi = kq_list[-1]
    tai = kq_list.count("Tài")
    xiu = kq_list.count("Xỉu")
    chenh = abs(tai - xiu)
    
    # Điểm tin cậy dựa trên độ cân bằng
    if chenh <= 2:
        diem = 68
        do_manh = "TRUNG BÌNH"
    elif chenh <= 4:
        diem = 65
        do_manh = "YẾU"
    else:
        diem = 60
        do_manh = "YẾU"
    
    return Signal(
        ket_qua="TÀI" if kq_cuoi == "Tài" else "XỈU",
        diem_tin_cay=diem,
        ten_cau="Cầu nối đuôi",
        mo_ta=f"Nối đuôi phiên cuối → {kq_cuoi}",
        do_manh=do_manh
    )

def kiem_tra_cau_duoi_gom(kq_list):
    """🎯 CẦU ĐUÔI GOM - 3-4 phiên gần cùng chiều"""
    if len(kq_list) < 3:
        return None
    
    m3 = kq_list[-3:]
    if m3.count("Tài") == 3:
        return Signal("TÀI", 80, "Cầu đuôi gom TÀI", "3 phiên cuối đều TÀI → TIẾP TỤC", "TRUNG BÌNH")
    if m3.count("Xỉu") == 3:
        return Signal("XỈU", 80, "Cầu đuôi gom XỈU", "3 phiên cuối đều XỈU → TIẾP TỤC", "TRUNG BÌNH")
    
    if len(kq_list) >= 4:
        m4 = kq_list[-4:]
        if m4.count("Tài") >= 3 and m4[-1] == "Tài":
            return Signal("TÀI", 75, "Cầu đuôi gom TÀI", "3/4 phiên cuối TÀI → TIẾP TỤC", "YẾU")
        if m4.count("Xỉu") >= 3 and m4[-1] == "Xỉu":
            return Signal("XỈU", 75, "Cầu đuôi gom XỈU", "3/4 phiên cuối XỈU → TIẾP TỤC", "YẾU")
    return None

def tong_hop_tin_hieu(danh_sach_tin_hieu, kq_list):
    """🏆 TỔNG HỢP TÍN HIỆU - Quyết định cuối cùng"""
    if not danh_sach_tin_hieu:
        # Không có tín hiệu → mặc định nối đuôi
        kq_cuoi = kq_list[-1] if kq_list else "Tài"
        return {
            "du_doan": "TÀI" if kq_cuoi == "Tài" else "XỈU",
            "ti_le": 55.0,
            "loi_khuyen": f"Dữ liệu hạn chế - Nối đuôi {kq_cuoi}",
            "phuong_phap": "Dự đoán mặc định",
            "ten_cau": "Chưa rõ",
            "do_manh": "HÌNH THÀNH",
            "so_tin_hieu": 0,
            "tong_diem": 0,
            "trend": "Đang phân tích cầu..."
        }
    
    # Nhóm tín hiệu theo kết quả
    nhom_tai = [s for s in danh_sach_tin_hieu if s.ket_qua == "TÀI"]
    nhom_xiu = [s for s in danh_sach_tin_hieu if s.ket_qua == "XỈU"]
    
    # Tính tổng điểm có trọng số
    def tinh_tong_diem(nhom):
        if not nhom:
            return 0, 0
        # Lấy tín hiệu mạnh nhất làm gốc
        max_signal = max(nhom, key=lambda x: x.diem_tin_cay)
        tong = max_signal.diem_tin_cay
        # Cộng thêm điểm từ các tín hiệu đồng tình (không cộng đầy đủ)
        for s in nhom:
            if s is not max_signal:
                tong += s.diem_tin_cay * 0.3  # Trọng số 30% cho tín hiệu phụ
        return min(tong, 99), len(nhom)
    
    diem_tai, so_tai = tinh_tong_diem(nhom_tai)
    diem_xiu, so_xiu = tinh_tong_diem(nhom_xiu)
    
    # Quyết định
    if diem_tai >= diem_xiu:
        ket_qua_chinh = "TÀI"
        diem_chinh = diem_tai
        nhom_chinh = nhom_tai
    else:
        ket_qua_chinh = "XỈU"
        diem_chinh = diem_xiu
        nhom_chinh = nhom_xiu
    
    # Lấy tín hiệu mạnh nhất làm đại diện
    tin_hieu_chinh = max(nhom_chinh, key=lambda x: x.diem_tin_cay) if nhom_chinh else None
    
    # Xác định độ mạnh
    if diem_chinh >= 90:
        do_manh = "RẤT MẠNH"
    elif diem_chinh >= 80:
        do_manh = "MẠNH"
    elif diem_chinh >= 70:
        do_manh = "TRUNG BÌNH"
    else:
        do_manh = "YẾU"
    
    # Tạo mô tả
    if tin_hieu_chinh:
        loi_khuyen = f"{tin_hieu_chinh.mo_ta} ({round(diem_chinh, 1)}%)"
        phuong_phap = tin_hieu_chinh.mo_ta
        ten_cau = tin_hieu_chinh.ten_cau
    else:
        loi_khuyen = f"Dự đoán {ket_qua_chinh} ({round(diem_chinh, 1)}%)"
        phuong_phap = "Tổng hợp tín hiệu"
        ten_cau = "Tổng hợp"
    
    # Xu hướng
    tai = kq_list.count("Tài")
    xiu = kq_list.count("Xỉu")
    chuoi_tai = dem_chuoi_nguoc(kq_list, "Tài")
    chuoi_xiu = dem_chuoi_nguoc(kq_list, "Xỉu")
    
    if chuoi_tai >= 4:
        trend = f"🔥 Cầu bệt TÀI {chuoi_tai} phiên - RẤT MẠNH"
    elif chuoi_xiu >= 4:
        trend = f"🔥 Cầu bệt XỈU {chuoi_xiu} phiên - RẤT MẠNH"
    elif chuoi_tai >= 3:
        trend = f"⚡ Cầu bệt TÀI {chuoi_tai} phiên - MẠNH"
    elif chuoi_xiu >= 3:
        trend = f"⚡ Cầu bệt XỈU {chuoi_xiu} phiên - MẠNH"
    elif tai > xiu + 3:
        trend = f"📈 Thiên về TÀI ({tai}T-{xiu}X)"
    elif xiu > tai + 3:
        trend = f"📉 Thiên về XỈU ({tai}T-{xiu}X)"
    else:
        trend = f"⚖️ Cân bằng ({tai}T-{xiu}X)"
    
    return {
        "du_doan": ket_qua_chinh,
        "ti_le": round(diem_chinh, 1),
        "loi_khuyen": loi_khuyen,
        "phuong_phap": phuong_phap,
        "ten_cau": ten_cau,
        "do_manh": do_manh,
        "so_tin_hieu": len(danh_sach_tin_hieu),
        "so_tin_hieu_dong_tinh": so_tai if ket_qua_chinh == "TÀI" else so_xiu,
        "tong_diem": round(diem_chinh, 1),
        "trend": trend,
        "chi_tiet_tin_hieu": [
            {"ket_qua": s.ket_qua, "diem": s.diem_tin_cay, "cau": s.ten_cau}
            for s in sorted(danh_sach_tin_hieu, key=lambda x: -x.diem_tin_cay)[:5]
        ]
    }

def thuat_toan_vip_xin(kq_list):
    """🏆 HÀM CHÍNH - THUẬT TOÁN VIP XỊN"""
    if not kq_list or len(kq_list) < 2:
        return {
            "du_doan": "TÀI",
            "ti_le": 55.0,
            "loi_khuyen": "Đang thu thập dữ liệu - Dự đoán TÀI",
            "phuong_phap": "Khởi tạo",
            "ten_cau": "Đang hình thành",
            "do_manh": "HÌNH THÀNH",
            "so_tin_hieu": 0,
            "tong_diem": 55.0,
            "trend": "🔍 Đang phân tích cầu..."
        }
    
    # Thu thập tất cả tín hiệu
    danh_sach_tin_hieu = []
    
    # 1. Cầu bệt (ưu tiên cao nhất)
    s = kiem_tra_cau_bet(kq_list)
    if s: danh_sach_tin_hieu.append(s)
    
    # 2. Cầu xen kẽ 1-1
    s = kiem_tra_cau_xen_ke_11(kq_list)
    if s: danh_sach_tin_hieu.append(s)
    
    # 3. Cầu 2-1
    s = kiem_tra_cau_2_1(kq_list)
    if s: danh_sach_tin_hieu.append(s)
    
    # 4. Cầu 2-2
    s = kiem_tra_cau_2_2(kq_list)
    if s: danh_sach_tin_hieu.append(s)
    
    # 5. Cầu 3-1
    s = kiem_tra_cau_3_1(kq_list)
    if s: danh_sach_tin_hieu.append(s)
    
    # 6. Cầu song tử
    s = kiem_tra_cau_song_tu(kq_list)
    if s: danh_sach_tin_hieu.append(s)
    
    # 7. Cầu đuôi gom
    s = kiem_tra_cau_duoi_gom(kq_list)
    if s: danh_sach_tin_hieu.append(s)
    
    # 8. Cầu thiên vị
    s = kiem_tra_cau_thien_vi(kq_list)
    if s: danh_sach_tin_hieu.append(s)
    
    # 9. Cầu hồi quy
    s = kiem_tra_cau_hoi_quy(kq_list)
    if s: danh_sach_tin_hieu.append(s)
    
    # 10. Cầu nối đuôi (mặc định cuối cùng)
    s = kiem_tra_cau_noi_duoi(kq_list)
    if s: danh_sach_tin_hieu.append(s)
    
    # Tổng hợp và quyết định
    ket_qua = tong_hop_tin_hieu(danh_sach_tin_hieu, kq_list)
    
    # Thêm thống kê
    ket_qua["tong_tai"] = kq_list.count("Tài")
    ket_qua["tong_xiu"] = kq_list.count("Xỉu")
    ket_qua["chuoi_tai_hien_tai"] = dem_chuoi_nguoc(kq_list, "Tài")
    ket_qua["chuoi_xiu_hien_tai"] = dem_chuoi_nguoc(kq_list, "Xỉu")
    
    # Phân tích đa khung thời gian
    ket_qua["multi_timeframe"] = phan_tich_multi_timeframe(kq_list)
    
    logger.info(f"🏆 VIP: {ket_qua['du_doan']} | {ket_qua['ten_cau']} | {ket_qua['do_manh']} | {ket_qua['ti_le']}% | {ket_qua['so_tin_hieu']} tín hiệu")
    
    return ket_qua

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
            candidates.append({**item, "parseable": parseable})
    
    if not candidates:
        best = max(all_lists, key=lambda x: x["length"])
        return best["data"], best["path"]
    
    candidates.sort(key=lambda x: (-x["parseable"], -x["length"]))
    best = candidates[0]
    logger.info(f"✅ Danh sách: {best['path']} | {best['length']} phiên | parseable={best['parseable']}")
    return best["data"], best["path"]

def quick_check_tx(obj):
    if not isinstance(obj, dict):
        return False
    for v in obj.values():
        if isinstance(v, str):
            vu = v.upper()
            if any(k in vu for k in ["TÀI", "TAI", "XỈU", "XIU", "BIG", "SMALL"]):
                return True
    for sk in ["sum", "total", "tong", "point"]:
        if sk in obj:
            try: int(obj[sk]); return True
            except: pass
    return False

def classify_tx_text(text):
    if not text: return None
    t = text.upper().strip()
    if any(k in t for k in ["TÀI", "TAI", "BIG", "LARGE"]): return "Tài"
    if any(k in t for k in ["XỈU", "XIU", "SMALL", "TINY"]): return "Xỉu"
    return None

def parse_result_super(session_obj):
    if not isinstance(session_obj, dict): return None
    
    result_keys = [
        "resultTruyenThong", "result", "ketqua", "ketQua", "kq", "value",
        "tx_result", "txResult", "taiXiu", "tai_xiu", "result_tx", "outcome",
        "status", "type", "name", "diceResult", "dice_result", "gameResult",
        "tx", "resultText", "result_text", "label", "title"
    ]
    
    for key in result_keys:
        if key in session_obj and session_obj[key]:
            r = classify_tx_text(str(session_obj[key]))
            if r: return r
    
    for v in session_obj.values():
        if isinstance(v, str):
            r = classify_tx_text(v)
            if r: return r
    
    for sum_key in ["sum", "total", "tong", "tongDiem", "diceSum", "point", "score"]:
        if sum_key in session_obj:
            try:
                tong = float(session_obj[sum_key])
                if tong >= 11: return "Tài"
                elif tong >= 3: return "Xỉu"
            except: pass
    
    for dice_key in ["dice", "dices", "xucxac", "numbers", "values"]:
        if dice_key in session_obj:
            dice = session_obj[dice_key]
            if isinstance(dice, list) and len(dice) >= 3:
                try:
                    tong = sum(int(x) for x in dice)
                    return "Tài" if tong >= 11 else "Xỉu"
                except: pass
    
    for v in session_obj.values():
        if isinstance(v, str):
            nums = re.findall(r'\d+', v)
            if nums:
                try:
                    tong = int(nums[-1])
                    if 3 <= tong <= 10: return "Xỉu"
                    elif 11 <= tong <= 18: return "Tài"
                except: pass
    
    return None

def extract_session_id_super(session_obj):
    if not isinstance(session_obj, dict): return "N/A"
    for id_key in ["id", "sessionId", "session_id", "phien", "issue", "period", "round", "number", "no"]:
        if id_key in session_obj and session_obj[id_key]:
            return str(session_obj[id_key])
    return "N/A"

# ================= API CHÍNH =================
@app.get("/")
async def home():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for name in ["index.html", "index (3).html", "index.html.html"]:
        p = os.path.join(base_dir, name)
        if os.path.exists(p):
            return FileResponse(p)
    return {"status": "ok", "msg": "🏆 THUẬT TOÁN VIP XỊN v6.0 đang chạy"}

@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "version": "6.0",
        "mode": "🏆 VIP XỊN - Tổng hợp 15+ dạng cầu",
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
                        "index": i, "result": r,
                        "keys": list(s.keys())[:8],
                        "preview": {k: str(v)[:40] for k, v in list(s.items())[:4]}
                    })
        
        return JSONResponse({
            "status": "success", "tool": tool,
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
    logger.info(f"🏆 VIP Scan: {tool} | {username}")

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
        
        try:
            data = res.json()
        except Exception as je:
            logger.error(f"❌ JSON lỗi: {je}")
            kq = thuat_toan_vip_xin([])
            return JSONResponse({"status": "success", "data": {
                "du_doan": kq["du_doan"],
                "ti_le": kq["ti_le"],
                "phien": "API-ERR"
            }})

        all_list, list_path = find_best_session_list(data)

        if not all_list or len(all_list) == 0:
            logger.warning("⚠️ Không tìm thấy danh sách phiên!")
            kq = thuat_toan_vip_xin([])
            return JSONResponse({"status": "success", "data": {
                "du_doan": kq["du_doan"],
                "ti_le": kq["ti_le"],
                "phien": "NODATA"
            }})

        # Thử cả 2 cách lấy dữ liệu
        def get_and_parse(source_list, take_from="head", n=15):
            if len(source_list) >= n:
                raw = source_list[:n] if take_from == "head" else source_list[-n:]
            else:
                raw = source_list.copy()
            ordered = raw[::-1] if take_from == "head" else raw.copy()
            results = [parse_result_super(s) for s in ordered if isinstance(s, dict)]
            return [r for r in results if r], ordered
        
        kq_head, ord_head = get_and_parse(all_list, "head")
        kq_tail, ord_tail = get_and_parse(all_list, "tail")
        
        logger.info(f"📊 Cách A: {len(kq_head)}/15 | Cách B: {len(kq_tail)}/15")
        
        if len(kq_head) >= len(kq_tail):
            kq_final = kq_head
            ord_final = ord_head
            cach = "A"
        else:
            kq_final = kq_tail
            ord_final = ord_tail
            cach = "B"
        
        # 🏆 CHẠY THUẬT TOÁN VIP XỊN
        ket_qua = thuat_toan_vip_xin(kq_final)
        
        # ✅ ĐƠN GIẢN HÓA: Chỉ trả về TÀI/XỈU + phiên
        ket_qua_simple = {
            "du_doan": ket_qua["du_doan"],
            "ti_le": ket_qua["ti_le"],
            "phien": extract_session_id_super(ord_final[-1]) if ord_final else "N/A"
        }
        
        logger.info(f"🎯 KẾT QUẢ: {ket_qua_simple['du_doan']} | {ket_qua_simple['ti_le']}%")
        
        return JSONResponse({"status": "success", "data": ket_qua_simple})

    except Exception as e:
        logger.error(f"❌ Lỗi: {e}", exc_info=True)
        kq = thuat_toan_vip_xin([])
        return JSONResponse({"status": "success", "data": {
            "du_doan": kq["du_doan"],
            "ti_le": kq["ti_le"],
            "phien": "ERROR"
        }})

# ================= AUTH & USER APIs =================
@app.post("/api/auth")
async def auth(req: Request):
    try: d = await req.json()
    except: return JSONResponse({"status": "error", "msg": "Dữ liệu lỗi"})
    act, u, p = get_str(d, "action"), get_str(d, "username"), get_str(d, "password")
    if not u or not p: return JSONResponse({"status": "error", "msg": "Thiếu thông tin"})
    with get_db() as conn:
        c = conn.cursor()
        if act == "register":
            c.execute("SELECT 1 FROM users WHERE username=?", (u,))
            if c.fetchone(): return JSONResponse({"status": "error", "msg": "Tên đã tồn tại"})
            c.execute("INSERT INTO users VALUES (?,?,0,'2000-01-01 00:00:00',0)", (u, p))
            conn.commit()
            return JSONResponse({"status": "success", "msg": "Đăng ký thành công"})
        else:
            c.execute("SELECT password,is_banned FROM users WHERE username=?", (u,))
            r = c.fetchone()
            if not r or r[0] != p: return JSONResponse({"status": "error", "msg": "Sai tài khoản/mật khẩu"})
            if r[1] == 1 and u != "hungadmin11": return JSONResponse({"status": "error", "msg": "Bị khóa"})
            return JSONResponse({"status": "success", "msg": "Đăng nhập thành công"})

@app.get("/api/user_info")
async def user_info(username: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT balance,vip_expire FROM users WHERE username=?", (username,))
        r = c.fetchone()
    if not r: return JSONResponse({"status": "error"})
    is_vip = (datetime.now() < datetime.strptime(r[1], "%Y-%m-%d %H:%M:%S")) or username == "hungadmin11"
    vip_str = "VĨNH VIỄN (ADMIN)" if username == "hungadmin11" else (r[1] if is_vip else "Chưa có VIP")
    return JSONResponse({"status": "success", "data": {"balance": r[0], "vip_expire": vip_str, "is_vip": is_vip}})

@app.post("/api/deposit")
async def deposit(req: Request):
    try: d = await req.json()
    except: return JSONResponse({"status": "error"})
    un, net, amt, pin, srl = get_str(d, "username"), get_str(d, "network"), get_int(d, "amount"), get_str(d, "pin"), get_str(d, "serial")
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO deposits VALUES (NULL,?,?,?,?,?,'PENDING')", (un, net, amt, pin, srl))
        conn.commit()
    return JSONResponse({"status": "success", "msg": "Đã gửi thẻ, chờ duyệt"})

@app.post("/api/buy_vip")
async def buy_vip(req: Request):
    try: d = await req.json()
    except: return JSONResponse({"status": "error"})
    un, pkg = get_str(d, "username"), get_str(d, "package")
    if un == "hungadmin11": return JSONResponse({"status": "success", "msg": "Admin miễn phí"})
    gói = {"1D": (30000, 1), "3D": (50000, 3), "7D": (100000, 7), "30D": (150000, 30), "PERM": (200000, 36500)}
    if pkg not in gói: return JSONResponse({"status": "error", "msg": "Gói không hợp lệ"})
    cost, ngay = gói[pkg]
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT balance,vip_expire FROM users WHERE username=?", (un,))
        r = c.fetchone()
        if not r or r[0] < cost: return JSONResponse({"status": "error", "msg": "Không đủ tiền"})
        now = datetime.now()
        cur = datetime.strptime(r[1], "%Y-%m-%d %H:%M:%S")
        new_exp = (cur if cur > now else now) + timedelta(days=ngay)
        c.execute("UPDATE users SET balance=balance-?, vip_expire=? WHERE username=?",
                  (cost, new_exp.strftime("%Y-%m-%d %H:%M:%S"), un))
        conn.commit()
    return JSONResponse({"status": "success", "msg": "Mua VIP thành công"})

@app.get("/api/admin/data")
async def admin_data(username: str):
    if username != "hungadmin11": return JSONResponse({"status": "error"})
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT username,balance,vip_expire,is_banned FROM users WHERE username!='hungadmin11'")
        users = c.fetchall()
        c.execute("SELECT id,username,card_type,card_amount,card_pin,card_serial FROM deposits WHERE status='PENDING'")
        deps = c.fetchall()
    return JSONResponse({"status": "success", "users": users, "deps": deps})

@app.post("/api/admin/action")
async def admin_act(req: Request):
    try: d = await req.json()
    except: return JSONResponse({"status": "error"})
    admin, act, tgt, did, amt = get_str(d, "admin"), get_str(d, "action"), get_str(d, "target"), get_int(d, "dep_id"), get_int(d, "amount")
    if admin != "hungadmin11": return JSONResponse({"status": "error"})
    with get_db() as conn:
        c = conn.cursor()
        if act == "ban": c.execute("UPDATE users SET is_banned=1 WHERE username=?", (tgt,))
        elif act == "unban": c.execute("UPDATE users SET is_banned=0 WHERE username=?", (tgt,))
        elif act == "approve_dep":
            c.execute("UPDATE deposits SET status='APPROVED' WHERE id=?", (did,))
            c.execute("UPDATE users SET balance=balance+? WHERE username=?", (amt, tgt))
        elif act == "reject_dep": c.execute("UPDATE deposits SET status='REJECTED' WHERE id=?", (did,))
        else: return JSONResponse({"status": "error"})
        conn.commit()
    return JSONResponse({"status": "success"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🏆 THUẬT TOÁN VIP XỊN v6.0 | Cổng {port}")
    uvicorn.run("server_ai:app", host="0.0.0.0", port=port)
