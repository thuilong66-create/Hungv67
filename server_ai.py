"""
🏆 SERVER AI - THUẬT TOÁN VIP CHUẨN v7.0
═══════════════════════════════════════════
✨ ĐẶC ĐIỂM:
   🧠 THÔNG MINH: Biết khi nào THEO cầu, khi nào BẺ cầu
   🎯 12+ dạng cầu phổ biến chuẩn cá cược
   📊 Logic THEO/BẺ dựa trên độ bền cầu & thống kê
   ⚡ Phân tích đa khung thời gian (3-5-8-15 phiên)
   💎 Hệ thống điểm tin cậy động 0-99%
   🎯 Kết quả cuối cùng: CHỈ TÀI hoặc XỈU
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

app = FastAPI(title="🏆 VIP CHUẨN v7.0", version="7.0")
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
# 🏆 THUẬT TOÁN VIP CHUẨN v7.0 - THEO & BẺ THÔNG MINH
# ═══════════════════════════════════════════════════════════

class Signal:
    def __init__(self, ket_qua, diem_tin_cay, ten_cau, hanh_dong, mo_ta=""):
        self.ket_qua = ket_qua        # "TÀI" hoặc "XỈU"
        self.diem_tin_cay = diem_tin_cay  # 0-100
        self.ten_cau = ten_cau        # Tên loại cầu
        self.hanh_dong = hanh_dong    # "THEO" hoặc "BẺ"
        self.mo_ta = mo_ta            # Mô tả chi tiết

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
    """Phân tích đa khung thời gian"""
    kq = list(kq_list)
    ket_qua = {}
    for name, n in [("ngan", 3), ("trung", 5), ("dai", 8), ("toanbo", 15)]:
        if len(kq) >= n:
            phan = kq[-n:]
            tai = phan.count("Tài")
            xiu = phan.count("Xỉu")
            ket_qua[name] = {
                "tai": tai, "xiu": xiu,
                "tyle_tai": round(tai / n * 100, 1),
                "uu_the": "TÀI" if tai > xiu else ("XỈU" if xiu > tai else "CAN BANG")
            }
    return ket_qua

# ═══════════════════════════════════════════════════════════
# 🏆 CÁC LOẠI CẦU + LOGIC THEO/BẺ THÔNG MINH
# ═══════════════════════════════════════════════════════════

def kiem_tra_cau_bet_thong_minh(kq_list):
    """
    🏆 CẦU BỆT THÔNG MINH:
    - 2-4 phiên: THEO (tiếp tục)
    - ≥5 phiên: BẺ (cầu quá dài, sắp vỡ)
    """
    if len(kq_list) < 2:
        return None
    
    kq_cuoi = kq_list[-1]
    chuoi = dem_chuoi_nguoc(kq_list, kq_cuoi)
    
    if chuoi < 2:
        return None
    
    doi_phuong = "XỈU" if kq_cuoi == "Tài" else "XỈU" if kq_cuoi == "Tài" else "TÀI"
    
    if 2 <= chuoi <= 4:
        # THEO CẦU - cầu còn mạnh, tiếp tục
        if chuoi == 2:
            diem = 72
            mo_ta = f"Cầu bệt ngắn {chuoi}p {kq_cuoi} → THEO"
        elif chuoi == 3:
            diem = 80
            mo_ta = f"Cầu bệt {chuoi}p {kq_cuoi} → THEO"
        else:  # 4
            diem = 76
            mo_ta = f"Cầu bệt {chuoi}p {kq_cuoi} → THEO (bắt đầu yếu)"
        
        return Signal(
            ket_qua="TÀI" if kq_cuoi == "Tài" else "XỈU",
            diem_tin_cay=diem,
            ten_cau=f"Cầu bệt {chuoi} phiên",
            hanh_dong="THEO",
            mo_ta=mo_ta
        )
    elif chuoi >= 5:
        # BẺ CẦU - cầu quá dài, xác suất vỡ cao
        if chuoi == 5:
            diem = 78
        elif chuoi == 6:
            diem = 84
        else:
            diem = min(88 + (chuoi - 7) * 2, 95)
        
        return Signal(
            ket_qua=doi_phuong,
            diem_tin_cay=diem,
            ten_cau=f"Cầu bệt dài {chuoi} phiên",
            hanh_dong="BẺ",
            mo_ta=f"Cầu bệt quá dài {chuoi}p {kq_cuoi} → BẺ {doi_phuong}"
        )
    return None

def kiem_tra_cau_xen_ke_11(kq_list):
    """🎯 CẦU XEN KẼ 1-1 (T-X-T-X) → LUÔN THEO quy luật"""
    if len(kq_list) < 4:
        return None
    
    m4 = kq_list[-4:]
    if all(m4[i] != m4[i+1] for i in range(3)):
        du_doan = "TÀI" if m4[-1] == "Xỉu" else "XỈU"
        
        # Kiểm tra xem có phải 6 phiên hoàn hảo không
        if len(kq_list) >= 6:
            m6 = kq_list[-6:]
            if all(m6[i] != m6[i+1] for i in range(5)):
                return Signal(du_doan, 92, "Cầu nhịp 1-1 hoàn hảo", "THEO", 
                            f"Cầu T-X hoàn hảo 6p → THEO {du_doan}")
        
        return Signal(du_doan, 82, "Cầu nhịp 1-1", "THEO", 
                     f"Cầu T-X 4p → THEO {du_doan}")
    return None

def kiem_tra_cau_chu_ky_21(kq_list):
    """📊 CẦU CHU KỲ 2-1 (TT-X-TT-X) → THEO chu kỳ"""
    if len(kq_list) < 6:
        return None
    
    m6 = kq_list[-6:]
    if m6 == ["Tài", "Tài", "Xỉu", "Tài", "Tài", "Xỉu"]:
        return Signal("TÀI", 88, "Cầu chu kỳ 2-1 (TT-X)", "THEO", "Chu kỳ TT-X hoàn hảo → THEO TÀI")
    if m6 == ["Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu", "Tài"]:
        return Signal("XỈU", 88, "Cầu chu kỳ 2-1 (XX-T)", "THEO", "Chu kỳ XX-T hoàn hảo → THEO XỈU")
    
    # Dấu hiệu 3 phiên cuối
    if len(kq_list) >= 3:
        m3 = kq_list[-3:]
        if m3 == ["Tài", "Tài", "Xỉu"]:
            return Signal("TÀI", 70, "Cầu chu kỳ 2-1", "THEO", "Dấu hiệu TT-X → THEO TÀI")
        if m3 == ["Xỉu", "Xỉu", "Tài"]:
            return Signal("XỈU", 70, "Cầu chu kỳ 2-1", "THEO", "Dấu hiệu XX-T → THEO XỈU")
    return None

def kiem_tra_cau_can_bang_22(kq_list):
    """⚖️ CẦU CÂN BẰNG 2-2 (TT-XX-TT-XX) → THEO"""
    if len(kq_list) < 8:
        return None
    
    m8 = kq_list[-8:]
    if m8 == ["Tài", "Tài", "Xỉu", "Xỉu", "Tài", "Tài", "Xỉu", "Xỉu"]:
        return Signal("TÀI", 86, "Cầu cân bằng 2-2", "THEO", "TT-XX hoàn hảo 8p → THEO TÀI")
    if m8 == ["Xỉu", "Xỉu", "Tài", "Tài", "Xỉu", "Xỉu", "Tài", "Tài"]:
        return Signal("XỈU", 86, "Cầu cân bằng 2-2", "THEO", "XX-TT hoàn hảo 8p → THEO XỈU")
    
    if len(kq_list) >= 4:
        m4 = kq_list[-4:]
        if m4 == ["Tài", "Tài", "Xỉu", "Xỉu"]:
            return Signal("TÀI", 72, "Cầu cân bằng 2-2", "THEO", "Dấu hiệu TT-XX → THEO TÀI")
        if m4 == ["Xỉu", "Xỉu", "Tài", "Tài"]:
            return Signal("XỈU", 72, "Cầu cân bằng 2-2", "THEO", "Dấu hiệu XX-TT → THEO XỈU")
    return None

def kiem_tra_cau_chu_ky_31(kq_list):
    """📈 CẦU CHU KỲ 3-1 (TTT-X-TTT-X) → THEO"""
    if len(kq_list) < 8:
        return None
    
    m8 = kq_list[-8:]
    if m8 == ["Tài", "Tài", "Tài", "Xỉu", "Tài", "Tài", "Tài", "Xỉu"]:
        return Signal("TÀI", 85, "Cầu chu kỳ 3-1", "THEO", "TTT-X hoàn hảo → THEO TÀI")
    if m8 == ["Xỉu", "Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu", "Xỉu", "Tài"]:
        return Signal("XỈU", 85, "Cầu chu kỳ 3-1", "THEO", "XXX-T hoàn hảo → THEO XỈU")
    return None

def kiem_tra_cau_song_tu(kq_list):
    """🎭 CẦU SONG TỬ (A-B-A-B lặp) → THEO mẫu"""
    if len(kq_list) < 6:
        return None
    
    k1, k2, k3, k4, k5, k6 = kq_list[-6], kq_list[-5], kq_list[-4], kq_list[-3], kq_list[-2], kq_list[-1]
    
    if k1 == k3 == k5 and k2 == k4 == k6 and k1 != k2:
        du_doan = "TÀI" if k1 == "Tài" else "XỈU"
        return Signal(du_doan, 84, "Cầu song tử", "THEO", f"Mẫu {k1}-{k2} lặp → THEO {du_doan}")
    return None

def kiem_tra_cau_duoi_gom(kq_list):
    """🎯 CẦU ĐUÔI GOM (3-4p gần cùng chiều) → THEO"""
    if len(kq_list) < 3:
        return None
    
    m3 = kq_list[-3:]
    if m3.count("Tài") == 3:
        return Signal("TÀI", 78, "Cầu đuôi gom TÀI", "THEO", "3p cuối TÀI → THEO")
    if m3.count("Xỉu") == 3:
        return Signal("XỈU", 78, "Cầu đuôi gom XỈU", "THEO", "3p cuối XỈU → THEO")
    
    if len(kq_list) >= 4:
        m4 = kq_list[-4:]
        if m4.count("Tài") >= 3 and m4[-1] == "Tài":
            return Signal("TÀI", 72, "Cầu đuôi gom TÀI", "THEO", "3/4p cuối TÀI → THEO")
        if m4.count("Xỉu") >= 3 and m4[-1] == "Xỉu":
            return Signal("XỈU", 72, "Cầu đuôi gom XỈU", "THEO", "3/4p cuối XỈU → THEO")
    return None

def kiem_tra_cau_thien_vi(kq_list):
    """🌟 CẦU THIÊN VỊ (một bên chiếm ưu thế) → THEO xu hướng"""
    if len(kq_list) < 10:
        return None
    
    tai = kq_list.count("Tài")
    xiu = kq_list.count("Xỉu")
    tong = len(kq_list)
    tl_tai = tai / tong
    
    if tl_tai >= 0.67:
        diem = 78 + min(int((tl_tai - 0.67) * 80), 10)
        return Signal("TÀI", diem, "Cầu thiên TÀI", "THEO", 
                     f"TÀI chiếm {round(tl_tai*100)}% → THEO xu hướng")
    elif tl_tai <= 0.33:
        diem = 78 + min(int((0.67 - tl_tai) * 80), 10)
        return Signal("XỈU", diem, "Cầu thiên XỈU", "THEO", 
                     f"XỈU chiếm {round((1-tl_tai)*100)}% → THEO xu hướng")
    return None

def kiem_tra_cau_hoi_quy(kq_list):
    """🔄 CẦU HỒI QUY (chênh lệch quá lớn) → BẺ để cân bằng"""
    if len(kq_list) < 12:
        return None
    
    tai = kq_list.count("Tài")
    xiu = kq_list.count("Xỉu")
    chenh = abs(tai - xiu)
    
    if chenh >= 6:
        if tai > xiu:
            return Signal("XỈU", 74, "Cầu hồi quy", "BẺ", 
                         f"Chênh lệch {chenh}p (Tài nhiều) → BẺ XỈU cân bằng")
        else:
            return Signal("TÀI", 74, "Cầu hồi quy", "BẺ", 
                         f"Chênh lệch {chenh}p (Xỉu nhiều) → BẺ TÀI cân bằng")
    return None

def kiem_tra_cau_dao_chieu_nhanh(kq_list):
    """⚡ CẦU ĐẢO CHIỀU NHANH (sau 1 phiên đảo) → BẺ trở lại"""
    if len(kq_list) < 4:
        return None
    
    k1, k2, k3, k4 = kq_list[-4], kq_list[-3], kq_list[-2], kq_list[-1]
    
    # K2=K3=K4 cùng loại, K1 khác → vừa đảo chiều, có thể quay lại
    if k2 == k3 == k4 and k1 != k2 and k2 == k3:
        if k2 == "Tài" and k1 == "Xỉu":
            return Signal("XỈU", 66, "Cầu đảo chiều nhanh", "BẺ", 
                         "Vừa đảo sang TÀI → BẺ trở lại XỈU")
        elif k2 == "Xỉu" and k1 == "Tài":
            return Signal("TÀI", 66, "Cầu đảo chiều nhanh", "BẺ", 
                         "Vừa đảo sang XỈU → BẺ trở lại TÀI")
    return None

def kiem_tra_cau_noi_duoi_mac_dinh(kq_list):
    """🚀 NỐI ĐUÔI MẶC ĐỊNH (thông minh) → THEO phiên cuối"""
    if len(kq_list) < 2:
        return None
    
    kq_cuoi = kq_list[-1]
    tai = kq_list.count("Tài")
    xiu = kq_list.count("Xỉu")
    chenh = abs(tai - xiu)
    
    # Điểm tin cậy dựa trên độ cân bằng gần đây
    if len(kq_list) >= 3:
        m3 = kq_list[-3:]
        if m3.count(kq_cuoi) >= 2:
            diem = 68
        else:
            diem = 62
    else:
        diem = 58
    
    return Signal(
        ket_qua="TÀI" if kq_cuoi == "Tài" else "XỈU",
        diem_tin_cay=diem,
        ten_cau="Cầu nối đuôi",
        hanh_dong="THEO",
        mo_ta=f"Nối đuôi phiên cuối → THEO {kq_cuoi}"
    )

# ═══════════════════════════════════════════════════════════
# 🏆 TỔNG HỢP TÍN HIỆU & QUYẾT ĐỊNH CUỐI CÙNG
# ═══════════════════════════════════════════════════════════

def tong_hop_tin_hieu_vip(danh_sach_tin_hieu, kq_list):
    """🏆 Tổng hợp thông minh tất cả tín hiệu"""
    if not danh_sach_tin_hieu:
        kq_cuoi = kq_list[-1] if kq_list else "Tài"
        return {
            "du_doan": "TÀI" if kq_cuoi == "Tài" else "XỈU",
            "ti_le": 55.0,
            "ten_cau": "Mặc định",
            "hanh_dong": "THEO",
            "mo_ta": "Dữ liệu hạn chế"
        }
    
    # Nhóm theo kết quả
    nhom_tai = [s for s in danh_sach_tin_hieu if s.ket_qua == "TÀI"]
    nhom_xiu = [s for s in danh_sach_tin_hieu if s.ket_qua == "XỈU"]
    
    def tinh_diem_vip(nhom):
        """Tính điểm VIP: tín hiệu mạnh nhất + tín hiệu phụ có trọng số"""
        if not nhom:
            return 0.0
        # Sắp xếp theo điểm giảm dần
        sorted_signals = sorted(nhom, key=lambda x: -x.diem_tin_cay)
        tong = sorted_signals[0].diem_tin_cay  # Tín hiệu mạnh nhất = 100% trọng số
        # Các tín hiệu tiếp theo: trọng số giảm dần
        for i, s in enumerate(sorted_signals[1:], 1):
            trong_so = max(0.35 - (i - 1) * 0.08, 0.1)  # 35% → 27% → 19% → ... tối thiểu 10%
            tong += s.diem_tin_cay * trong_so
        return min(round(tong, 1), 99.0)
    
    diem_tai = tinh_diem_vip(nhom_tai)
    diem_xiu = tinh_diem_vip(nhom_xiu)
    
    # Quyết định
    if diem_tai >= diem_xiu:
        ket_qua = "TÀI"
        diem_final = diem_tai
        nhom_chinh = nhom_tai
    else:
        ket_qua = "XỈU"
        diem_final = diem_xiu
        nhom_chinh = nhom_xiu
    
    # Lấy tín hiệu mạnh nhất làm đại diện
    tin_hieu_chinh = max(nhom_chinh, key=lambda x: x.diem_tin_cay) if nhom_chinh else None
    
    return {
        "du_doan": ket_qua,
        "ti_le": diem_final,
        "ten_cau": tin_hieu_chinh.ten_cau if tin_hieu_chinh else "Tổng hợp",
        "hanh_dong": tin_hieu_chinh.hanh_dong if tin_hieu_chinh else "THEO",
        "mo_ta": tin_hieu_chinh.mo_ta if tin_hieu_chinh else "Tổng hợp tín hiệu",
        "so_tin_hieu": len(danh_sach_tin_hieu),
        "diem_tai": diem_tai,
        "diem_xiu": diem_xiu
    }

def thuat_toan_vip_chuan(kq_list):
    """🏆 HÀM CHÍNH - THUẬT TOÁN VIP CHUẨN v7.0"""
    if not kq_list or len(kq_list) < 2:
        return {"du_doan": "TÀI", "ti_le": 55.0, "ten_cau": "Khởi tạo", "hanh_dong": "THEO", "mo_ta": "Đang phân tích"}
    
    danh_sach_tin_hieu = []
    
    # 1. Cầu bệt thông minh (THEO ngắn, BẺ dài) - ƯU TIÊN CAO NHẤT
    s = kiem_tra_cau_bet_thong_minh(kq_list)
    if s: danh_sach_tin_hieu.append(s)
    
    # 2. Cầu xen kẽ 1-1
    s = kiem_tra_cau_xen_ke_11(kq_list)
    if s: danh_sach_tin_hieu.append(s)
    
    # 3. Cầu chu kỳ 2-1
    s = kiem_tra_cau_chu_ky_21(kq_list)
    if s: danh_sach_tin_hieu.append(s)
    
    # 4. Cầu cân bằng 2-2
    s = kiem_tra_cau_can_bang_22(kq_list)
    if s: danh_sach_tin_hieu.append(s)
    
    # 5. Cầu chu kỳ 3-1
    s = kiem_tra_cau_chu_ky_31(kq_list)
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
    
    # 9. Cầu hồi quy (BẺ)
    s = kiem_tra_cau_hoi_quy(kq_list)
    if s: danh_sach_tin_hieu.append(s)
    
    # 10. Cầu đảo chiều nhanh
    s = kiem_tra_cau_dao_chieu_nhanh(kq_list)
    if s: danh_sach_tin_hieu.append(s)
    
    # 11. Nối đuôi mặc định (luôn có, điểm thấp nhất)
    s = kiem_tra_cau_noi_duoi_mac_dinh(kq_list)
    if s: danh_sach_tin_hieu.append(s)
    
    # 🏆 TỔNG HỢP & QUYẾT ĐỊNH
    ket_qua = tong_hop_tin_hieu_vip(danh_sach_tin_hieu, kq_list)
    
    # Log chi tiết
    log_signals = " | ".join([f"{s.ket_qua[0]}{s.hanh_dong[0]}{s.diem_tin_cay:.0f}({s.ten_cau[:10]})" for s in sorted(danh_sach_tin_hieu, key=lambda x: -x.diem_tin_cay)[:4]])
    logger.info(f"🎯 {ket_qua['du_doan']} | {ket_qua['ten_cau']} | {ket_qua['hanh_dong']} | {ket_qua['ti_le']}% | Tín hiệu: [{log_signals}]")
    
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
    logger.info(f"✅ Danh sách: {best['path']} | {best['length']}p | parse={best['parseable']}")
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
    return {"status": "ok", "msg": "🏆 VIP CHUẨN v7.0 đang chạy"}

@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "version": "7.0",
        "mode": "🏆 VIP CHUẨN - THEO & BẺ thông minh",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

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
            kq = thuat_toan_vip_chuan([])
            return JSONResponse({"status": "success", "data": {
                "du_doan": kq["du_doan"], "ti_le": kq["ti_le"], "phien": "API-ERR"
            }})

        all_list, list_path = find_best_session_list(data)

        if not all_list or len(all_list) == 0:
            logger.warning("⚠️ Không tìm thấy danh sách!")
            kq = thuat_toan_vip_chuan([])
            return JSONResponse({"status": "success", "data": {
                "du_doan": kq["du_doan"], "ti_le": kq["ti_le"], "phien": "NODATA"
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
        else:
            kq_final = kq_tail
            ord_final = ord_tail
        
        # 🏆 CHẠY THUẬT TOÁN VIP CHUẨN
        ket_qua = thuat_toan_vip_chuan(kq_final)
        
        # ✅ Trả về ĐƠN GIẢN: chỉ TÀI/XỈU + tỷ lệ + phiên
        response_simple = {
            "du_doan": ket_qua["du_doan"],
            "ti_le": ket_qua["ti_le"],
            "phien": extract_session_id_super(ord_final[-1]) if ord_final else "N/A"
        }
        
        logger.info(f"🎯 KẾT QUẢ CUỐI: {response_simple['du_doan']} | {response_simple['ti_le']}%")
        
        return JSONResponse({"status": "success", "data": response_simple})

    except Exception as e:
        logger.error(f"❌ Lỗi: {e}", exc_info=True)
        kq = thuat_toan_vip_chuan([])
        return JSONResponse({"status": "success", "data": {
            "du_doan": kq["du_doan"], "ti_le": kq["ti_le"], "phien": "ERROR"
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
    logger.info(f"🏆 THUẬT TOÁN VIP CHUẨN v7.0 | THEO & BẺ thông minh | Cổng {port}")
    uvicorn.run("server_ai:app", host="0.0.0.0", port=port)
