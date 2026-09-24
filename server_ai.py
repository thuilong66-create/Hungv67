"""
🏆 SERVER AI - THUẬT TOÁN ĐA TẦNG 20 LỚP v8.0
═══════════════════════════════════════════════════
✨ ĐẶC ĐIỂM:
   🧱 20 TẦNG thuật toán độc lập, mỗi tầng logic riêng
   🗳️ Bỏ phiếu ĐA SỐ: tầng nào vote nhiều hơn chọn cái đó
   📊 Tính điểm tin cậy = tỷ lệ phiếu + độ đồng thuận
   🎯 Dự đoán cho phiên ĐANG ĐỢI kết quả
   💎 15 phiên lịch sử đầu vào cho mỗi tầng
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

app = FastAPI(title="🏆 ĐA TẦNG 20 LỚP v8.0", version="8.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "hethong_vip.db"
SO_LUONG_LICH_SU = 15  # 15 phiên lịch sử cho mỗi tầng

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
# 🧱 HỆ THỐNG ĐA TẦNG - 20 TẦNG THUẬT TOÁN ĐỘC LẬP
# ═══════════════════════════════════════════════════════════

def dem_chuoi_nguoc(kq_list, muc_tieu):
    """Đếm chuỗi liên tiếp từ cuối lên"""
    dem = 0
    for x in reversed(kq_list):
        if x == muc_tieu:
            dem += 1
        else:
            break
    return dem

# ═══════════════════════════════════════════════════════════
# 🏗️ 20 TẦNG THUẬT TOÁN
# ═══════════════════════════════════════════════════════════

def tang_01_cau_bet_ngan_theo(kq):
    """🏗️ TẦNG 1: Cầu bệt ngắn 2-3 phiên → THEO"""
    if len(kq) < 2: return None
    kq_cuoi = kq[-1]
    chuoi = dem_chuoi_nguoc(kq, kq_cuoi)
    if 2 <= chuoi <= 3:
        return "TÀI" if kq_cuoi == "Tài" else "XỈU"
    return None

def tang_02_cau_bet_dai_be(kq):
    """🏗️ TẦNG 2: Cầu bệt dài ≥5 phiên → BẺ"""
    if len(kq) < 5: return None
    kq_cuoi = kq[-1]
    chuoi = dem_chuoi_nguoc(kq, kq_cuoi)
    if chuoi >= 5:
        return "XỈU" if kq_cuoi == "Tài" else "TÀI"
    return None

def tang_03_cau_bet_vua_theo(kq):
    """🏗️ TẦNG 3: Cầu bệt vừa 4 phiên → THEO (yếu)"""
    if len(kq) < 4: return None
    kq_cuoi = kq[-1]
    chuoi = dem_chuoi_nguoc(kq, kq_cuoi)
    if chuoi == 4:
        return "TÀI" if kq_cuoi == "Tài" else "XỈU"
    return None

def tang_04_nhip_11_hoan_hao(kq):
    """🏗️ TẦNG 4: Cầu nhịp 1-1 hoàn hảo 6p → THEO quy luật"""
    if len(kq) < 6: return None
    m6 = kq[-6:]
    if all(m6[i] != m6[i+1] for i in range(5)):
        return "TÀI" if m6[-1] == "Xỉu" else "XỈU"
    return None

def tang_05_nhip_11_ngan(kq):
    """🏗️ TẦNG 5: Cầu nhịp 1-1 ngắn 4p → THEO"""
    if len(kq) < 4: return None
    m4 = kq[-4:]
    if all(m4[i] != m4[i+1] for i in range(3)):
        return "TÀI" if m4[-1] == "Xỉu" else "XỈU"
    return None

def tang_06_chu_ky_21_hoan_hao(kq):
    """🏗️ TẦNG 6: Cầu chu kỳ 2-1 hoàn hảo 6p → THEO"""
    if len(kq) < 6: return None
    m6 = kq[-6:]
    if m6 == ["Tài", "Tài", "Xỉu", "Tài", "Tài", "Xỉu"]:
        return "TÀI"
    if m6 == ["Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu", "Tài"]:
        return "XỈU"
    return None

def tang_07_chu_ky_21_dau_hieu(kq):
    """🏗️ TẦNG 7: Dấu hiệu cầu 2-1 (3p cuối) → THEO"""
    if len(kq) < 3: return None
    m3 = kq[-3:]
    if m3 == ["Tài", "Tài", "Xỉu"]:
        return "TÀI"
    if m3 == ["Xỉu", "Xỉu", "Tài"]:
        return "XỈU"
    return None

def tang_08_can_bang_22_hoan_hao(kq):
    """🏗️ TẦNG 8: Cầu cân bằng 2-2 hoàn hảo 8p → THEO"""
    if len(kq) < 8: return None
    m8 = kq[-8:]
    if m8 == ["Tài", "Tài", "Xỉu", "Xỉu", "Tài", "Tài", "Xỉu", "Xỉu"]:
        return "TÀI"
    if m8 == ["Xỉu", "Xỉu", "Tài", "Tài", "Xỉu", "Xỉu", "Tài", "Tài"]:
        return "XỈU"
    return None

def tang_09_can_bang_22_dau_hieu(kq):
    """🏗️ TẦNG 9: Dấu hiệu cầu 2-2 (4p cuối) → THEO"""
    if len(kq) < 4: return None
    m4 = kq[-4:]
    if m4 == ["Tài", "Tài", "Xỉu", "Xỉu"]:
        return "TÀI"
    if m4 == ["Xỉu", "Xỉu", "Tài", "Tài"]:
        return "XỈU"
    return None

def tang_10_chu_ky_31(kq):
    """🏗️ TẦNG 10: Cầu chu kỳ 3-1 hoàn hảo 8p → THEO"""
    if len(kq) < 8: return None
    m8 = kq[-8:]
    if m8 == ["Tài", "Tài", "Tài", "Xỉu", "Tài", "Tài", "Tài", "Xỉu"]:
        return "TÀI"
    if m8 == ["Xỉu", "Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu", "Xỉu", "Tài"]:
        return "XỈU"
    return None

def tang_11_song_tu(kq):
    """🏗️ TẦNG 11: Cầu song tử A-B-A-B lặp 6p → THEO"""
    if len(kq) < 6: return None
    k1, k2, k3, k4, k5, k6 = kq[-6], kq[-5], kq[-4], kq[-3], kq[-2], kq[-1]
    if k1 == k3 == k5 and k2 == k4 == k6 and k1 != k2:
        return "TÀI" if k1 == "Tài" else "XỈU"
    return None

def tang_12_duoi_gom_3p(kq):
    """🏗️ TẦNG 12: Đuôi gom 3 phiên cuối cùng chiều → THEO"""
    if len(kq) < 3: return None
    m3 = kq[-3:]
    if m3.count("Tài") == 3:
        return "TÀI"
    if m3.count("Xỉu") == 3:
        return "XỈU"
    return None

def tang_13_duoi_gom_4p(kq):
    """🏗️ TẦNG 13: Đuôi gom 3/4 phiên cuối → THEO"""
    if len(kq) < 4: return None
    m4 = kq[-4:]
    if m4.count("Tài") >= 3 and m4[-1] == "Tài":
        return "TÀI"
    if m4.count("Xỉu") >= 3 and m4[-1] == "Xỉu":
        return "XỈU"
    return None

def tang_14_thien_vi_manh(kq):
    """🏗️ TẦNG 14: Thiên vị mạnh ≥70% → THEO xu hướng"""
    if len(kq) < 10: return None
    tai = kq.count("Tài")
    tong = len(kq)
    tl = tai / tong
    if tl >= 0.70:
        return "TÀI"
    elif tl <= 0.30:
        return "XỈU"
    return None

def tang_15_thien_vi_trung_binh(kq):
    """🏗️ TẦNG 15: Thiên vị trung bình ≥60% → THEO xu hướng"""
    if len(kq) < 8: return None
    tai = kq.count("Tài")
    tong = len(kq)
    tl = tai / tong
    if tl >= 0.60 and tl < 0.70:
        return "TÀI"
    elif tl <= 0.40 and tl > 0.30:
        return "XỈU"
    return None

def tang_16_hoi_quy(kq):
    """🏗️ TẦNG 16: Hồi quy - chênh lệch ≥6 → BẺ cân bằng"""
    if len(kq) < 12: return None
    tai = kq.count("Tài")
    xiu = kq.count("Xỉu")
    chenh = abs(tai - xiu)
    if chenh >= 6:
        return "XỈU" if tai > xiu else "TÀI"
    return None

def tang_17_dao_chieu_nhanh(kq):
    """🏗️ TẦNG 17: Đảo chiều nhanh (vừa đảo 1p) → BẺ trở lại"""
    if len(kq) < 4: return None
    k1, k2, k3, k4 = kq[-4], kq[-3], kq[-2], kq[-1]
    if k2 == k3 == k4 and k1 != k2:
        return "XỈU" if k2 == "Tài" else "TÀI"
    return None

def tang_18_noi_duoi_cuoi(kq):
    """🏗️ TẦNG 18: Nối đuôi phiên cuối cùng → THEO"""
    if len(kq) < 1: return None
    return "TÀI" if kq[-1] == "Tài" else "XỈU"

def tang_19_khung_ngan_han(kq):
    """🏗️ TẦNG 19: Phân tích khung ngắn hạn (3p gần) → THEO ưu thế"""
    if len(kq) < 3: return None
    m3 = kq[-3:]
    tai = m3.count("Tài")
    xiu = m3.count("Xỉu")
    if tai > xiu:
        return "TÀI"
    elif xiu > tai:
        return "XỈU"
    return None

def tang_20_da_khung_dong_thuan(kq):
    """🏗️ TẦNG 20: Đa khung đồng thuận (3p, 5p, 8p cùng chiều) → THEO"""
    if len(kq) < 8: return None
    
    def uu_the(lst):
        t = lst.count("Tài")
        x = lst.count("Xỉu")
        if t > x + 0: return "TÀI"
        elif x > t + 0: return "XỈU"
        return None
    
    k3 = uu_the(kq[-3:])
    k5 = uu_the(kq[-5:])
    k8 = uu_the(kq[-8:])
    
    # Nếu ít nhất 2/3 khung cùng chiều
    votes = [k3, k5, k8]
    votes_valid = [v for v in votes if v]
    if len(votes_valid) >= 2:
        counter = Counter(votes_valid)
        common = counter.most_common(1)
        if common and common[0][1] >= 2:
            return common[0][0]
    return None

# ═══════════════════════════════════════════════════════════
# 🗳️ HỆ THỐNG BỎ PHIẾU ĐA TẦNG
# ═══════════════════════════════════════════════════════════

# Danh sách 20 tầng thuật toán
DANH_SACH_TANG = [
    ("Tầng 01 - Cầu bệt ngắn THEO", tang_01_cau_bet_ngan_theo),
    ("Tầng 02 - Cầu bệt dài BẺ", tang_02_cau_bet_dai_be),
    ("Tầng 03 - Cầu bệt vừa THEO", tang_03_cau_bet_vua_theo),
    ("Tầng 04 - Nhịp 1-1 hoàn hảo", tang_04_nhip_11_hoan_hao),
    ("Tầng 05 - Nhịp 1-1 ngắn", tang_05_nhip_11_ngan),
    ("Tầng 06 - Chu kỳ 2-1 HH", tang_06_chu_ky_21_hoan_hao),
    ("Tầng 07 - Chu kỳ 2-1 dấu hiệu", tang_07_chu_ky_21_dau_hieu),
    ("Tầng 08 - Cân bằng 2-2 HH", tang_08_can_bang_22_hoan_hao),
    ("Tầng 09 - Cân bằng 2-2 dấu hiệu", tang_09_can_bang_22_dau_hieu),
    ("Tầng 10 - Chu kỳ 3-1", tang_10_chu_ky_31),
    ("Tầng 11 - Song tử", tang_11_song_tu),
    ("Tầng 12 - Đuôi gom 3p", tang_12_duoi_gom_3p),
    ("Tầng 13 - Đuôi gom 4p", tang_13_duoi_gom_4p),
    ("Tầng 14 - Thiên vị mạnh", tang_14_thien_vi_manh),
    ("Tầng 15 - Thiên vị TB", tang_15_thien_vi_trung_binh),
    ("Tầng 16 - Hồi quy", tang_16_hoi_quy),
    ("Tầng 17 - Đảo chiều nhanh", tang_17_dao_chieu_nhanh),
    ("Tầng 18 - Nối đuôi cuối", tang_18_noi_duoi_cuoi),
    ("Tầng 19 - Khung ngắn hạn", tang_19_khung_ngan_han),
    ("Tầng 20 - Đa khung đồng thuận", tang_20_da_khung_dong_thuan),
]

def thuan_toan_da_tang_20_tang(kq_list):
    """
    🏆 HÀM CHÍNH: THUẬT TOÁN ĐA TẦNG 20 LỚP
    ----------------------------------------
    Input: 15 phiên lịch sử [cũ nhất, ..., mới nhất]
    Output: {du_doan, ti_le, chi_tiet_bau_phieu}
    """
    if not kq_list or len(kq_list) < 2:
        return {"du_doan": "TÀI", "ti_le": 55.0, "bao_phieu": {"TÀI": 0, "XỈU": 0, "khoang": 20}}
    
    # 🗳️ Chạy tất cả 20 tầng
    ket_qua_tung_tang = []
    for ten_tang, ham_tang in DANH_SACH_TANG:
        try:
            kq = ham_tang(kq_list)
            ket_qua_tung_tang.append((ten_tang, kq))
        except Exception as e:
            logger.warning(f"⚠️ Lỗi {ten_tang}: {e}")
            ket_qua_tung_tang.append((ten_tang, None))
    
    # 📊 Đếm phiếu
    phieu_tai = sum(1 for _, kq in ket_qua_tung_tang if kq == "TÀI")
    phieu_xiu = sum(1 for _, kq in ket_qua_tung_tang if kq == "XỈU")
    so_tang_khoang = sum(1 for _, kq in ket_qua_tung_tang if kq is None)
    so_tang_hoat_dong = 20 - so_tang_khoang
    
    # 🏆 Quyết định ĐA SỐ
    if phieu_tai > phieu_xiu:
        du_doan = "TÀI"
        so_phieu_thang = phieu_tai
    elif phieu_xiu > phieu_tai:
        du_doan = "XỈU"
        so_phieu_thang = phieu_xiu
    else:
        # Hòa nhau → dùng tầng nối đuôi làm quyết định
        du_doan = "TÀI" if kq_list[-1] == "Tài" else "XỈU"
        so_phieu_thang = max(phieu_tai, phieu_xiu)
    
    # 📊 Tính điểm tin cậy
    if so_tang_hoat_dong > 0:
        ty_le_phieu = so_phieu_thang / so_tang_hoat_dong * 100
    else:
        ty_le_phieu = 50
    
    # Điểm tin cậy = tỷ lệ phiếu * hệ số độ mạnh
    # 100% đồng thuận = 95%, 50% = 55%
    ti_le = round(55 + (ty_le_phieu - 50) * 0.8, 1)
    ti_le = max(55.0, min(ti_le, 95.0))
    
    # Chi tiết các tầng vote
    chi_tiet = []
    for ten_tang, kq in ket_qua_tung_tang:
        chi_tiet.append({"tang": ten_tang, "vote": kq if kq else "KHOANG"})
    
    # Log đẹp
    log_votes = " ".join([
        f"T{i+1:02d}:{kq[0] if kq else '-'}" 
        for i, (_, kq) in enumerate(ket_qua_tung_tang)
    ])
    logger.info(f"🗳️ Bầu cử: TÀI={phieu_tai} XỈU={phieu_xiu} Khoang={so_tang_khoang} | {du_doan} thắng | {ti_le}%")
    logger.info(f"📊 {log_votes}")
    
    return {
        "du_doan": du_doan,
        "ti_le": ti_le,
        "bao_phieu": {
            "TÀI": phieu_tai,
            "XỈU": phieu_xiu,
            "khoang": so_tang_khoang,
            "tong_hoat_dong": so_tang_hoat_dong
        },
        "chi_tiet_tang": chi_tiet
    }

# ═══════════════════════════════════════════════════════════
# ✨ TÌM PHIÊN ĐANG ĐỢI KẾT QUẢ
# ═══════════════════════════════════════════════════════════

def tim_phien_doi_va_lich_su(danh_sach_phien, n_lich_su=15):
    """Tìm phiên đang đợi + 15 phiên lịch sử trước đó"""
    if not danh_sach_phien or len(danh_sach_phien) < 2:
        return None, []
    
    def phan_tich(lst):
        if len(lst) < 2:
            return None, []
        
        phien_moi_nhat = lst[0]
        kq_moi_nhat = parse_result_super(phien_moi_nhat) if isinstance(phien_moi_nhat, dict) else None
        
        phien_doi = None
        vi_tri_bat_dau = 0
        
        if kq_moi_nhat is None:
            phien_doi = phien_moi_nhat
            vi_tri_bat_dau = 1
            logger.info(f"✅ Tìm thấy phiên ĐANG ĐỢI")
        else:
            phien_doi = phien_moi_nhat
            vi_tri_bat_dau = 0
            logger.info(f"ℹ️ Tất cả đã có kết quả → dự đoán phiên tiếp theo")
        
        lich_su_raw = lst[vi_tri_bat_dau : vi_tri_bat_dau + n_lich_su + 5]
        lich_su_kq = []
        for s in lich_su_raw:
            if isinstance(s, dict):
                kq = parse_result_super(s)
                if kq:
                    lich_su_kq.append(kq)
            if len(lich_su_kq) >= n_lich_su:
                break
        
        lich_su_kq = lich_su_kq[::-1]  # Cũ ở đầu, mới ở cuối
        return phien_doi, lich_su_kq
    
    # Thử cả 2 thứ tự
    phien_a, ls_a = phan_tich(danh_sach_phien)
    phien_b, ls_b = phan_tich(danh_sach_phien[::-1])
    
    # Chọn cách tốt hơn
    kq_a = parse_result_super(phien_a) if phien_a else "?"
    kq_b = parse_result_super(phien_b) if phien_b else "?"
    
    if kq_a is None and len(ls_a) >= len(ls_b):
        return phien_a, ls_a
    elif kq_b is None and len(ls_b) >= len(ls_a):
        return phien_b, ls_b
    else:
        return (phien_a, ls_a) if len(ls_a) >= len(ls_b) else (phien_b, ls_b)

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
    if not phien_id_str or phien_id_str == "N/A":
        return "TIẾP THEO"
    try:
        nums = re.findall(r'\d+', phien_id_str)
        if nums:
            so_cuoi = int(nums[-1])
            so_moi = so_cuoi + 1
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
    return {"status": "ok", "msg": "🏆 ĐA TẦNG 20 LỚP v8.0 đang chạy"}

@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "version": "8.0",
        "mode": "🏆 ĐA TẦNG 20 LỚP - Bỏ phiếu đa số",
        "so_tang": 20,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/api/scan")
async def scan_game(tool: str, username: str):
    logger.info(f"🏆 ĐA TẦNG Scan: {tool} | {username}")

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

        # ✨ Tìm phiên đang đợi + lịch sử
        phien_doi, lich_su_kq = tim_phien_doi_va_lich_su(all_list, SO_LUONG_LICH_SU)
        
        logger.info(f"📋 Phiên đợi: {extract_session_id_super(phien_doi) if phien_doi else 'N/A'} | Lịch sử: {len(lich_su_kq)}p")
        
        if len(lich_su_kq) < 2:
            logger.warning(f"⚠️ Chỉ {len(lich_su_kq)} phiên lịch sử")
            return JSONResponse({"status": "success", "data": {
                "du_doan": "TÀI",
                "ti_le": 55.0,
                "phien": extract_session_id_super(phien_doi) if phien_doi else "N/A"
            }})
        
        # 🏆 CHẠY THUẬT TOÁN ĐA TẦNG 20 LỚP
        ket_qua = thuan_toan_da_tang_20_tang(lich_su_kq)
        
        # Xác định ID phiên hiển thị
        if phien_doi and parse_result_super(phien_doi) is None:
            phien_hien_thi = extract_session_id_super(phien_doi)
        else:
            phien_moi_nhat_id = extract_session_id_super(phien_doi) if phien_doi else "N/A"
            phien_hien_thi = tang_id_phien(phien_moi_nhat_id)
        
        # ✅ Trả về đơn giản
        response = {
            "du_doan": ket_qua["du_doan"],
            "ti_le": ket_qua["ti_le"],
            "phien": phien_hien_thi
        }
        
        logger.info(f"🎯 KẾT QUẢ ĐA TẦNG: Phiên #{phien_hien_thi} → {response['du_doan']} | {response['ti_le']}%")
        
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
    logger.info(f"🏆 THUẬT TOÁN ĐA TẦNG 20 LỚP v8.0 | Cổng {port}")
    uvicorn.run("server_ai:app", host="0.0.0.0", port=port)
