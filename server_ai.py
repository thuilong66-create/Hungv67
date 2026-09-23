"""
🏆 SERVER AI - VIP CHUẨN v7.1
═══════════════════════════════════════════
✨ NÂNG CẤP QUAN TRỌNG:
   🎯 DỰ ĐOÁN CHO PHIÊN ĐANG ĐỢI KẾT QUẢ
   📊 Lấy 15 phiên TRƯỚC ĐÓ (đã có kết quả) phân tích
   🆔 Trả về ID của phiên ĐANG ĐỢI + kết quả dự đoán
   🧠 Thuật toán VIP: THEO & BẺ thông minh 11+ dạng cầu
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

app = FastAPI(title="🏆 VIP CHUẨN v7.1 - Dự đoán phiên đợi", version="7.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "hethong_vip.db"
SO_LUONG_PHAN_TICH = 15  # Dùng 15 phiên đã có kết quả để phân tích

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
# 🏆 THUẬT TOÁN VIP CHUẨN - THEO & BẺ THÔNG MINH
# ═══════════════════════════════════════════════════════════

class Signal:
    def __init__(self, ket_qua, diem_tin_cay, ten_cau, hanh_dong, mo_ta=""):
        self.ket_qua = ket_qua
        self.diem_tin_cay = diem_tin_cay
        self.ten_cau = ten_cau
        self.hanh_dong = hanh_dong
        self.mo_ta = mo_ta

def dem_chuoi_nguoc(kq_list, muc_tieu):
    dem = 0
    for x in reversed(kq_list):
        if x == muc_tieu:
            dem += 1
        else:
            break
    return dem

def kiem_tra_cau_bet_thong_minh(kq_list):
    """🏆 Cầu bệt: 2-4p THEO, ≥5p BẺ"""
    if len(kq_list) < 2: return None
    kq_cuoi = kq_list[-1]
    chuoi = dem_chuoi_nguoc(kq_list, kq_cuoi)
    if chuoi < 2: return None
    
    doi_phuong = "XỈU" if kq_cuoi == "Tài" else "TÀI"
    
    if 2 <= chuoi <= 4:
        diem = 72 if chuoi == 2 else (80 if chuoi == 3 else 76)
        return Signal(
            ket_qua="TÀI" if kq_cuoi == "Tài" else "XỈU",
            diem_tin_cay=diem,
            ten_cau=f"Cầu bệt {chuoi}p",
            hanh_dong="THEO",
            mo_ta=f"Cầu bệt {chuoi}p {kq_cuoi} → THEO"
        )
    elif chuoi >= 5:
        diem = min(78 + (chuoi - 5) * 3, 95)
        return Signal(
            ket_qua=doi_phuong,
            diem_tin_cay=diem,
            ten_cau=f"Cầu bệt dài {chuoi}p",
            hanh_dong="BẺ",
            mo_ta=f"Cầu quá dài {chuoi}p → BẺ {doi_phuong}"
        )
    return None

def kiem_tra_cau_xen_ke_11(kq_list):
    """🎯 Cầu nhịp 1-1 → THEO"""
    if len(kq_list) < 4: return None
    m4 = kq_list[-4:]
    if all(m4[i] != m4[i+1] for i in range(3)):
        du_doan = "TÀI" if m4[-1] == "Xỉu" else "XỈU"
        if len(kq_list) >= 6:
            m6 = kq_list[-6:]
            if all(m6[i] != m6[i+1] for i in range(5)):
                return Signal(du_doan, 92, "Cầu nhịp 1-1 hoàn hảo", "THEO", f"T-X 6p → THEO {du_doan}")
        return Signal(du_doan, 82, "Cầu nhịp 1-1", "THEO", f"T-X 4p → THEO {du_doan}")
    return None

def kiem_tra_cau_chu_ky_21(kq_list):
    """📊 Cầu chu kỳ 2-1 → THEO"""
    if len(kq_list) < 6: return None
    m6 = kq_list[-6:]
    if m6 == ["Tài", "Tài", "Xỉu", "Tài", "Tài", "Xỉu"]:
        return Signal("TÀI", 88, "Cầu chu kỳ 2-1", "THEO", "TT-X hoàn hảo → THEO TÀI")
    if m6 == ["Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu", "Tài"]:
        return Signal("XỈU", 88, "Cầu chu kỳ 2-1", "THEO", "XX-T hoàn hảo → THEO XỈU")
    if len(kq_list) >= 3:
        m3 = kq_list[-3:]
        if m3 == ["Tài", "Tài", "Xỉu"]:
            return Signal("TÀI", 70, "Cầu chu kỳ 2-1", "THEO", "Dấu hiệu TT-X → THEO TÀI")
        if m3 == ["Xỉu", "Xỉu", "Tài"]:
            return Signal("XỈU", 70, "Cầu chu kỳ 2-1", "THEO", "Dấu hiệu XX-T → THEO XỈU")
    return None

def kiem_tra_cau_can_bang_22(kq_list):
    """⚖️ Cầu cân bằng 2-2 → THEO"""
    if len(kq_list) < 8: return None
    m8 = kq_list[-8:]
    if m8 == ["Tài", "Tài", "Xỉu", "Xỉu", "Tài", "Tài", "Xỉu", "Xỉu"]:
        return Signal("TÀI", 86, "Cầu cân bằng 2-2", "THEO", "TT-XX 8p → THEO TÀI")
    if m8 == ["Xỉu", "Xỉu", "Tài", "Tài", "Xỉu", "Xỉu", "Tài", "Tài"]:
        return Signal("XỈU", 86, "Cầu cân bằng 2-2", "THEO", "XX-TT 8p → THEO XỈU")
    if len(kq_list) >= 4:
        m4 = kq_list[-4:]
        if m4 == ["Tài", "Tài", "Xỉu", "Xỉu"]:
            return Signal("TÀI", 72, "Cầu cân bằng 2-2", "THEO", "Dấu hiệu TT-XX → THEO TÀI")
        if m4 == ["Xỉu", "Xỉu", "Tài", "Tài"]:
            return Signal("XỈU", 72, "Cầu cân bằng 2-2", "THEO", "Dấu hiệu XX-TT → THEO XỈU")
    return None

def kiem_tra_cau_chu_ky_31(kq_list):
    """📈 Cầu chu kỳ 3-1 → THEO"""
    if len(kq_list) < 8: return None
    m8 = kq_list[-8:]
    if m8 == ["Tài", "Tài", "Tài", "Xỉu", "Tài", "Tài", "Tài", "Xỉu"]:
        return Signal("TÀI", 85, "Cầu chu kỳ 3-1", "THEO", "TTT-X hoàn hảo → THEO TÀI")
    if m8 == ["Xỉu", "Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu", "Xỉu", "Tài"]:
        return Signal("XỈU", 85, "Cầu chu kỳ 3-1", "THEO", "XXX-T hoàn hảo → THEO XỈU")
    return None

def kiem_tra_cau_song_tu(kq_list):
    """🎭 Cầu song tử → THEO"""
    if len(kq_list) < 6: return None
    k1, k2, k3, k4, k5, k6 = kq_list[-6], kq_list[-5], kq_list[-4], kq_list[-3], kq_list[-2], kq_list[-1]
    if k1 == k3 == k5 and k2 == k4 == k6 and k1 != k2:
        du_doan = "TÀI" if k1 == "Tài" else "XỈU"
        return Signal(du_doan, 84, "Cầu song tử", "THEO", f"Mẫu {k1}-{k2} → THEO {du_doan}")
    return None

def kiem_tra_cau_duoi_gom(kq_list):
    """🎯 Cầu đuôi gom → THEO"""
    if len(kq_list) < 3: return None
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
    """🌟 Cầu thiên vị → THEO"""
    if len(kq_list) < 10: return None
    tai = kq_list.count("Tài")
    xiu = kq_list.count("Xỉu")
    tong = len(kq_list)
    tl_tai = tai / tong
    if tl_tai >= 0.67:
        diem = 78 + min(int((tl_tai - 0.67) * 80), 10)
        return Signal("TÀI", diem, "Cầu thiên TÀI", "THEO", f"TÀI {round(tl_tai*100)}% → THEO")
    elif tl_tai <= 0.33:
        diem = 78 + min(int((0.67 - tl_tai) * 80), 10)
        return Signal("XỈU", diem, "Cầu thiên XỈU", "THEO", f"XỈU {round((1-tl_tai)*100)}% → THEO")
    return None

def kiem_tra_cau_hoi_quy(kq_list):
    """🔄 Cầu hồi quy → BẺ"""
    if len(kq_list) < 12: return None
    tai = kq_list.count("Tài")
    xiu = kq_list.count("Xỉu")
    chenh = abs(tai - xiu)
    if chenh >= 6:
        if tai > xiu:
            return Signal("XỈU", 74, "Cầu hồi quy", "BẺ", f"Chênh {chenh}p → BẺ XỈU cân bằng")
        else:
            return Signal("TÀI", 74, "Cầu hồi quy", "BẺ", f"Chênh {chenh}p → BẺ TÀI cân bằng")
    return None

def kiem_tra_cau_dao_chieu_nhanh(kq_list):
    """⚡ Đảo chiều nhanh → BẺ"""
    if len(kq_list) < 4: return None
    k1, k2, k3, k4 = kq_list[-4], kq_list[-3], kq_list[-2], kq_list[-1]
    if k2 == k3 == k4 and k1 != k2:
        if k2 == "Tài" and k1 == "Xỉu":
            return Signal("XỈU", 66, "Cầu đảo chiều", "BẺ", "Vừa đảo TÀI → BẺ XỈU")
        elif k2 == "Xỉu" and k1 == "Tài":
            return Signal("TÀI", 66, "Cầu đảo chiều", "BẺ", "Vừa đảo XỈU → BẺ TÀI")
    return None

def kiem_tra_cau_noi_duoi(kq_list):
    """🚀 Nối đuôi mặc định → THEO"""
    if len(kq_list) < 2: return None
    kq_cuoi = kq_list[-1]
    if len(kq_list) >= 3:
        m3 = kq_list[-3:]
        diem = 68 if m3.count(kq_cuoi) >= 2 else 62
    else:
        diem = 58
    return Signal(
        ket_qua="TÀI" if kq_cuoi == "Tài" else "XỈU",
        diem_tin_cay=diem,
        ten_cau="Cầu nối đuôi",
        hanh_dong="THEO",
        mo_ta=f"Nối đuôi → THEO {kq_cuoi}"
    )

def tong_hop_tin_hieu_vip(danh_sach_tin_hieu, kq_list):
    """🏆 Tổng hợp thông minh"""
    if not danh_sach_tin_hieu:
        kq_cuoi = kq_list[-1] if kq_list else "Tài"
        return {"du_doan": "TÀI" if kq_cuoi == "Tài" else "XỈU", "ti_le": 55.0}
    
    nhom_tai = [s for s in danh_sach_tin_hieu if s.ket_qua == "TÀI"]
    nhom_xiu = [s for s in danh_sach_tin_hieu if s.ket_qua == "XỈU"]
    
    def tinh_diem(nhom):
        if not nhom: return 0.0
        sorted_s = sorted(nhom, key=lambda x: -x.diem_tin_cay)
        tong = sorted_s[0].diem_tin_cay
        for i, s in enumerate(sorted_s[1:], 1):
            trong_so = max(0.35 - (i - 1) * 0.08, 0.1)
            tong += s.diem_tin_cay * trong_so
        return min(round(tong, 1), 99.0)
    
    diem_tai = tinh_diem(nhom_tai)
    diem_xiu = tinh_diem(nhom_xiu)
    
    if diem_tai >= diem_xiu:
        return {"du_doan": "TÀI", "ti_le": diem_tai}
    else:
        return {"du_doan": "XỈU", "ti_le": diem_xiu}

def thuat_toan_vip_chuan(kq_list):
    """🏆 HÀM CHÍNH - VIP CHUẨN"""
    if not kq_list or len(kq_list) < 2:
        return {"du_doan": "TÀI", "ti_le": 55.0}
    
    signals = []
    
    # Thu thập tất cả tín hiệu
    for func in [
        kiem_tra_cau_bet_thong_minh,
        kiem_tra_cau_xen_ke_11,
        kiem_tra_cau_chu_ky_21,
        kiem_tra_cau_can_bang_22,
        kiem_tra_cau_chu_ky_31,
        kiem_tra_cau_song_tu,
        kiem_tra_cau_duoi_gom,
        kiem_tra_cau_thien_vi,
        kiem_tra_cau_hoi_quy,
        kiem_tra_cau_dao_chieu_nhanh,
        kiem_tra_cau_noi_duoi
    ]:
        s = func(kq_list)
        if s: signals.append(s)
    
    ket_qua = tong_hop_tin_hieu_vip(signals, kq_list)
    
    # Log chi tiết
    log_s = " | ".join([f"{s.ket_qua[0]}{s.hanh_dong[0]}{s.diem_tin_cay:.0f}" for s in sorted(signals, key=lambda x: -x.diem_tin_cay)[:4]])
    logger.info(f"🎯 {ket_qua['du_doan']} | {ket_qua['ti_le']}% | Tín hiệu: [{log_s}]")
    
    return ket_qua

# ═══════════════════════════════════════════════════════════
# ✨ LOGIC MỚI: TÌM PHIÊN ĐANG ĐỢI KẾT QUẢ
# ═══════════════════════════════════════════════════════════

def tim_phien_doi_va_lich_su(danh_sach_phien, n_lich_su=15):
    """
    🎯 Tìm phiên ĐANG ĐỢI KẾT QUẢ và lịch sử 15 phiên TRƯỚC ĐÓ
    --------------------------------------------------------
    Input: danh_sach_phien = [phiên_mới_nhất, ..., phiên_cũ_nhất]
    (hoặc ngược lại - hàm tự động xử lý)
    
    Returns: (phien_doi, lich_su_kq, thu_tu_dung)
    - phien_doi: dict phiên đang đợi (hoặc None nếu không có)
    - lich_su_kq: list ["Tài", "Xỉu", ...] 15 phiên trước đó
    - thu_tu_dung: "head" hoặc "tail" - cách lấy dữ liệu đúng
    """
    if not danh_sach_phien or len(danh_sach_phien) < 2:
        return None, [], "head"
    
    # Thử CÁCH A: phiên MỚI NHẤT ở ĐẦU danh sách (phổ biến nhất)
    # → Phiên đầu tiên = mới nhất → kiểm tra xem nó có kết quả không
    def phan_tich_theo_thu_tu(lst, thu_tu):
        """lst = [mới nhất, ..., cũ nhất]"""
        if len(lst) < 2:
            return None, []
        
        # Kiểm tra phiên đầu tiên (mới nhất) có kết quả không
        phien_moi_nhat = lst[0]
        kq_moi_nhat = parse_result_super(phien_moi_nhat) if isinstance(phien_moi_nhat, dict) else None
        
        phien_doi = None
        vi_tri_bat_dau_lich_su = 0
        
        if kq_moi_nhat is None:
            # ✅ Phiên mới nhất CHƯA có kết quả → Đây là phiên ĐANG ĐỢI!
            phien_doi = phien_moi_nhat
            vi_tri_bat_dau_lich_su = 1  # Lịch sử bắt đầu từ phiên thứ 2
            logger.info(f"✅ Tìm thấy phiên ĐANG ĐỢI ở vị trí đầu tiên")
        else:
            # Tất cả đều có kết quả → Dự đoán cho phiên TIẾP THEO
            # Lấy phiên mới nhất làm "phiên đợi" để có ID tham chiếu
            phien_doi = phien_moi_nhat  # Dùng phiên này làm tham chiếu
            vi_tri_bat_dau_lich_su = 0  # Dùng tất cả để phân tích
            logger.info(f"ℹ️ Tất cả đều có kết quả → Dự đoán cho phiên tiếp theo")
        
        # Lấy n_lich_su phiên TRƯỚC phiên đợi (đã có kết quả)
        lich_su_raw = lst[vi_tri_bat_dau_lich_su : vi_tri_bat_dau_lich_su + n_lich_su + 5]  # Lấy dôi ra để đảm bảo đủ
        
        # Parse kết quả
        lich_su_kq = []
        for s in lich_su_raw:
            if isinstance(s, dict):
                kq = parse_result_super(s)
                if kq:
                    lich_su_kq.append(kq)
            if len(lich_su_kq) >= n_lich_su:
                break
        
        # Đảo ngược lịch sử: CŨ NHẤT ở đầu, MỚI NHẤT ở cuối (cho thuật toán)
        lich_su_kq = lich_su_kq[::-1]
        
        return phien_doi, lich_su_kq
    
    # ====== THỬ CÁCH A: Mới nhất ở ĐẦU ======
    phien_doi_a, lich_su_a = phan_tich_theo_thu_tu(danh_sach_phien, "head")
    
    # ====== THỬ CÁCH B: Mới nhất ở CUỐI ======
    lst_dao = danh_sach_phien[::-1]
    phien_doi_b, lich_su_b = phan_tich_theo_thu_tu(lst_dao, "tail")
    
    # ====== CHỌN CÁCH TỐT HƠN ======
    # Ưu tiên cách nào tìm thấy phiên đang đợi VÀ có nhiều lịch sử hơn
    if phien_doi_a and parse_result_super(phien_doi_a) is None and len(lich_su_a) >= len(lich_su_b):
        logger.info(f"✅ Chọn CÁCH A (mới ở đầu) | Lịch sử: {len(lich_su_a)} phiên")
        return phien_doi_a, lich_su_a, "head"
    elif phien_doi_b and parse_result_super(phien_doi_b) is None and len(lich_su_b) >= len(lich_su_a):
        logger.info(f"✅ Chọn CÁCH B (mới ở cuối) | Lịch sử: {len(lich_su_b)} phiên")
        return phien_doi_b, lich_su_b, "tail"
    else:
        # Không tìm thấy phiên đợi rõ ràng → chọn cách có nhiều lịch sử hơn
        if len(lich_su_a) >= len(lich_su_b):
            logger.info(f"ℹ️ Không có phiên đợi rõ ràng, dùng CÁCH A | Lịch sử: {len(lich_su_a)}")
            return phien_doi_a, lich_su_a, "head"
        else:
            logger.info(f"ℹ️ Không có phiên đợi rõ ràng, dùng CÁCH B | Lịch sử: {len(lich_su_b)}")
            return phien_doi_b, lich_su_b, "tail"

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

def tang_id_phien(phien_id_str):
    """Tăng ID phiên lên 1 để dự đoán phiên tiếp theo"""
    if not phien_id_str or phien_id_str == "N/A":
        return "TIẾP THEO"
    try:
        # Tìm số trong ID
        nums = re.findall(r'\d+', phien_id_str)
        if nums:
            so_cuoi = int(nums[-1])
            so_moi = so_cuoi + 1
            # Thay thế số cuối cùng
            return phien_id_str.rstrip(nums[-1]) + str(so_moi)
        return phien_id_str + "+1"
    except:
        return phien_id_str

# ================= API CHÍNH =================
@app.get("/")
async def home():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for name in ["index.html", "index (3).html", "index.html.html"]:
        p = os.path.join(base_dir, name)
        if os.path.exists(p):
            return FileResponse(p)
    return {"status": "ok", "msg": "🏆 VIP CHUẨN v7.1 đang chạy"}

@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "version": "7.1",
        "mode": "🏆 Dự đoán phiên ĐANG ĐỢI kết quả",
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
            return JSONResponse({"status": "success", "data": {
                "du_doan": "TÀI", "ti_le": 55.0, "phien": "API-ERR"
            }})

        all_list, list_path = find_best_session_list(data)

        if not all_list or len(all_list) == 0:
            logger.warning("⚠️ Không tìm thấy danh sách!")
            return JSONResponse({"status": "success", "data": {
                "du_doan": "TÀI", "ti_le": 55.0, "phien": "NODATA"
            }})

        # ✨✨✨ LOGIC MỚI: TÌM PHIÊN ĐANG ĐỢI + LỊCH SỬ TRƯỚC ĐÓ ✨✨✨
        phien_doi, lich_su_kq, thu_tu = tim_phien_doi_va_lich_su(all_list, SO_LUONG_PHAN_TICH)
        
        logger.info(f"📋 Phiên đợi: {extract_session_id_super(phien_doi) if phien_doi else 'N/A'} | Lịch sử: {len(lich_su_kq)}p")
        
        # Kiểm tra dữ liệu lịch sử
        if len(lich_su_kq) < 2:
            logger.warning(f"⚠️ Chỉ có {len(lich_su_kq)} phiên lịch sử hợp lệ")
            # Dự đoán mặc định
            return JSONResponse({"status": "success", "data": {
                "du_doan": "TÀI",
                "ti_le": 55.0,
                "phien": extract_session_id_super(phien_doi) if phien_doi else "N/A"
            }})
        
        # 🏆 CHẠY THUẬT TOÁN VIP trên lịch sử 15 phiên
        ket_qua = thuat_toan_vip_chuan(lich_su_kq)
        
        # Xác định ID phiên cần hiển thị
        if phien_doi and parse_result_super(phien_doi) is None:
            # Có phiên đang đợi rõ ràng → dùng ID của nó
            phien_hien_thi = extract_session_id_super(phien_doi)
        else:
            # Không có phiên đợi → dự đoán phiên TIẾP THEO
            phien_moi_nhat_id = extract_session_id_super(phien_doi) if phien_doi else "N/A"
            phien_hien_thi = tang_id_phien(phien_moi_nhat_id)
        
        # ✅ Trả về: Kết quả dự đoán + phiên đang đợi
        response = {
            "du_doan": ket_qua["du_doan"],
            "ti_le": ket_qua["ti_le"],
            "phien": phien_hien_thi
        }
        
        logger.info(f"🎯 DỰ ĐOÁN CHO PHIÊN #{phien_hien_thi}: {response['du_doan']} | {response['ti_le']}%")
        
        return JSONResponse({"status": "success", "data": response})

    except Exception as e:
        logger.error(f"❌ Lỗi: {e}", exc_info=True)
        return JSONResponse({"status": "success", "data": {
            "du_doan": "TÀI", "ti_le": 55.0, "phien": "ERROR"
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
    logger.info(f"🏆 VIP CHUẨN v7.1 | Dự đoán phiên ĐANG ĐỢI | Cổng {port}")
    uvicorn.run("server_ai:app", host="0.0.0.0", port=port)
