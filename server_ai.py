"""
🏆 SERVER AI - THUẬT TOÁN VIP DUY NHẤT v9.0
═══════════════════════════════════════════════
✨ MỘT THUẬT TOÁN DUY NHẤT - XỊN VIP CHUẨN
   🧠 Tổng hợp thông minh 10+ dạng cầu
   🎯 Logic THEO & BẺ chuyên nghiệp (biết khi nào theo, khi nào bẻ)
   📊 Hệ thống điểm tin cậy động 55-95%
   📈 Phân tích đa khung thời gian (3-5-8-15 phiên)
   ⚡ Dự đoán cho phiên ĐANG ĐỢI kết quả
   💎 Giao diện đơn giản: chỉ TÀI/XỈU
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

app = FastAPI(title="🏆 VIP DUY NHẤT v9.0", version="9.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "hethong_vip.db"
SO_LUONG_LICH_SU = 15

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
# 🏆 THUẬT TOÁN VIP DUY NHẤT - TỔNG HỢP THÔNG MINH
# ═══════════════════════════════════════════════════════════

class TinHieu:
    """Lưu trữ một tín hiệu dự đoán"""
    def __init__(self, ket_qua, diem, ten_cau, hanh_dong, mo_ta=""):
        self.ket_qua = ket_qua      # "TÀI" hoặc "XỈU"
        self.diem = diem            # 0-100
        self.ten_cau = ten_cau      # Tên loại cầu
        self.hanh_dong = hanh_dong  # "THEO" hoặc "BẺ"
        self.mo_ta = mo_ta

def dem_chuoi_nguoc(kq, muc_tieu):
    """Đếm chuỗi liên tiếp từ cuối lên"""
    dem = 0
    for x in reversed(kq):
        if x == muc_tieu:
            dem += 1
        else:
            break
    return dem

def thuat_toan_vip_duy_nhat(kq_list):
    """
    🏆 THUẬT TOÁN VIP DUY NHẤT - Một thuật toán tổng hợp
    ---------------------------------------------------
    Bước 1: Thu thập tất cả tín hiệu từ các dạng cầu
    Bước 2: Nhóm theo TÀI/XỈU, tính điểm có trọng số
    Bước 3: Quyết định cuối cùng + điểm tin cậy động
    """
    if not kq_list or len(kq_list) < 2:
        return {"du_doan": "TÀI", "ti_le": 55.0}
    
    signals = []
    kq_cuoi = kq_list[-1]
    chuoi_tai = dem_chuoi_nguoc(kq_list, "Tài")
    chuoi_xiu = dem_chuoi_nguoc(kq_list, "Xỉu")
    tong_tai = kq_list.count("Tài")
    tong_xiu = kq_list.count("Xỉu")
    tong = len(kq_list)
    tl_tai = tong_tai / tong

    # ═══════════════════════════════════════════
    # 🏗️ BƯỚC 1: THU THẬP TÍN HIỆU TỪ CÁC DẠNG CẦU
    # ═══════════════════════════════════════════

    # 1. CẦU BỆT - Logic thông minh THEO/BẺ
    chuoi_hien_tai = max(chuoi_tai, chuoi_xiu)
    if chuoi_hien_tai >= 2:
        if chuoi_tai >= 2:
            loai = "Tài"
            doi_phuong = "XỈU"
        else:
            loai = "Xỉu"
            doi_phuong = "TÀI"
        
        if 2 <= chuoi_hien_tai <= 3:
            # THEO - cầu còn mạnh
            diem = 72 if chuoi_hien_tai == 2 else 80
            signals.append(TinHieu(
                "TÀI" if loai == "Tài" else "XỈU",
                diem, f"Cầu bệt {chuoi_hien_tai}p", "THEO",
                f"Cầu bệt {chuoi_hien_tai}p {loai} → THEO"
            ))
        elif chuoi_hien_tai == 4:
            # THEO nhưng yếu - cầu bắt đầu già
            signals.append(TinHieu(
                "TÀI" if loai == "Tài" else "XỈU",
                74, f"Cầu bệt 4p", "THEO",
                f"Cầu bệt 4p {loai} → THEO (yếu)"
            ))
        elif chuoi_hien_tai >= 5:
            # BẺ - cầu quá dài, sắp vỡ
            diem = min(78 + (chuoi_hien_tai - 5) * 3, 92)
            signals.append(TinHieu(
                doi_phuong, diem,
                f"Cầu bệt dài {chuoi_hien_tai}p", "BẺ",
                f"Cầu quá dài {chuoi_hien_tai}p → BẺ {doi_phuong}"
            ))

    # 2. CẦU NHỊP 1-1 (T-X-T-X)
    if tong >= 4:
        m4 = kq_list[-4:]
        if all(m4[i] != m4[i+1] for i in range(3)):
            du_doan = "TÀI" if m4[-1] == "Xỉu" else "XỈU"
            if tong >= 6:
                m6 = kq_list[-6:]
                if all(m6[i] != m6[i+1] for i in range(5)):
                    signals.append(TinHieu(du_doan, 92, "Cầu nhịp 1-1 hoàn hảo", "THEO", "T-X 6p hoàn hảo → THEO"))
                else:
                    signals.append(TinHieu(du_doan, 82, "Cầu nhịp 1-1", "THEO", "T-X 4p → THEO"))
            else:
                signals.append(TinHieu(du_doan, 82, "Cầu nhịp 1-1", "THEO", "T-X 4p → THEO"))

    # 3. CẦU CHU KỲ 2-1 (TT-X-TT-X)
    if tong >= 6:
        m6 = kq_list[-6:]
        if m6 == ["Tài", "Tài", "Xỉu", "Tài", "Tài", "Xỉu"]:
            signals.append(TinHieu("TÀI", 88, "Cầu chu kỳ 2-1", "THEO", "TT-X hoàn hảo → THEO TÀI"))
        elif m6 == ["Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu", "Tài"]:
            signals.append(TinHieu("XỈU", 88, "Cầu chu kỳ 2-1", "THEO", "XX-T hoàn hảo → THEO XỈU"))
        elif tong >= 3:
            m3 = kq_list[-3:]
            if m3 == ["Tài", "Tài", "Xỉu"]:
                signals.append(TinHieu("TÀI", 70, "Cầu chu kỳ 2-1", "THEO", "Dấu hiệu TT-X → THEO TÀI"))
            elif m3 == ["Xỉu", "Xỉu", "Tài"]:
                signals.append(TinHieu("XỈU", 70, "Cầu chu kỳ 2-1", "THEO", "Dấu hiệu XX-T → THEO XỈU"))

    # 4. CẦU CÂN BẰNG 2-2 (TT-XX-TT-XX)
    if tong >= 8:
        m8 = kq_list[-8:]
        if m8 == ["Tài", "Tài", "Xỉu", "Xỉu", "Tài", "Tài", "Xỉu", "Xỉu"]:
            signals.append(TinHieu("TÀI", 86, "Cầu cân bằng 2-2", "THEO", "TT-XX 8p → THEO TÀI"))
        elif m8 == ["Xỉu", "Xỉu", "Tài", "Tài", "Xỉu", "Xỉu", "Tài", "Tài"]:
            signals.append(TinHieu("XỈU", 86, "Cầu cân bằng 2-2", "THEO", "XX-TT 8p → THEO XỈU"))
        elif tong >= 4:
            m4 = kq_list[-4:]
            if m4 == ["Tài", "Tài", "Xỉu", "Xỉu"]:
                signals.append(TinHieu("TÀI", 72, "Cầu cân bằng 2-2", "THEO", "Dấu hiệu TT-XX → THEO TÀI"))
            elif m4 == ["Xỉu", "Xỉu", "Tài", "Tài"]:
                signals.append(TinHieu("XỈU", 72, "Cầu cân bằng 2-2", "THEO", "Dấu hiệu XX-TT → THEO XỈU"))

    # 5. CẦU CHU KỲ 3-1 (TTT-X-TTT-X)
    if tong >= 8:
        m8 = kq_list[-8:]
        if m8 == ["Tài", "Tài", "Tài", "Xỉu", "Tài", "Tài", "Tài", "Xỉu"]:
            signals.append(TinHieu("TÀI", 85, "Cầu chu kỳ 3-1", "THEO", "TTT-X hoàn hảo → THEO TÀI"))
        elif m8 == ["Xỉu", "Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu", "Xỉu", "Tài"]:
            signals.append(TinHieu("XỈU", 85, "Cầu chu kỳ 3-1", "THEO", "XXX-T hoàn hảo → THEO XỈU"))

    # 6. CẦU SONG TỬ (A-B-A-B lặp)
    if tong >= 6:
        k1, k2, k3, k4, k5, k6 = kq_list[-6], kq_list[-5], kq_list[-4], kq_list[-3], kq_list[-2], kq_list[-1]
        if k1 == k3 == k5 and k2 == k4 == k6 and k1 != k2:
            du_doan = "TÀI" if k1 == "Tài" else "XỈU"
            signals.append(TinHieu(du_doan, 84, "Cầu song tử", "THEO", f"Mẫu {k1}-{k2} lặp → THEO"))

    # 7. CẦU ĐUÔI GOM (3-4p cuối cùng chiều)
    if tong >= 3:
        m3 = kq_list[-3:]
        if m3.count("Tài") == 3:
            signals.append(TinHieu("TÀI", 78, "Cầu đuôi gom TÀI", "THEO", "3p cuối TÀI → THEO"))
        elif m3.count("Xỉu") == 3:
            signals.append(TinHieu("XỈU", 78, "Cầu đuôi gom XỈU", "THEO", "3p cuối XỈU → THEO"))
        elif tong >= 4:
            m4 = kq_list[-4:]
            if m4.count("Tài") >= 3 and m4[-1] == "Tài":
                signals.append(TinHieu("TÀI", 72, "Cầu đuôi gom TÀI", "THEO", "3/4p cuối TÀI → THEO"))
            elif m4.count("Xỉu") >= 3 and m4[-1] == "Xỉu":
                signals.append(TinHieu("XỈU", 72, "Cầu đuôi gom XỈU", "THEO", "3/4p cuối XỈU → THEO"))

    # 8. CẦU THIÊN VỊ (một bên chiếm ưu thế)
    if tong >= 10:
        if tl_tai >= 0.67:
            diem = 78 + min(int((tl_tai - 0.67) * 80), 10)
            signals.append(TinHieu("TÀI", diem, "Cầu thiên TÀI", "THEO", f"TÀI {round(tl_tai*100)}% → THEO"))
        elif tl_tai <= 0.33:
            diem = 78 + min(int((0.67 - tl_tai) * 80), 10)
            signals.append(TinHieu("XỈU", diem, "Cầu thiên XỈU", "THEO", f"XỈU {round((1-tl_tai)*100)}% → THEO"))

    # 9. CẦU HỒI QUY (chênh lệch quá lớn → BẺ)
    if tong >= 12:
        chenh = abs(tong_tai - tong_xiu)
        if chenh >= 6:
            if tong_tai > tong_xiu:
                signals.append(TinHieu("XỈU", 74, "Cầu hồi quy", "BẺ", f"Chênh {chenh}p → BẺ XỈU cân bằng"))
            else:
                signals.append(TinHieu("TÀI", 74, "Cầu hồi quy", "BẺ", f"Chênh {chenh}p → BẺ TÀI cân bằng"))

    # 10. CẦU ĐẢO CHIỀU NHANH (vừa đảo 1p → BẺ trở lại)
    if tong >= 4:
        k1, k2, k3, k4 = kq_list[-4], kq_list[-3], kq_list[-2], kq_list[-1]
        if k2 == k3 == k4 and k1 != k2:
            if k2 == "Tài":
                signals.append(TinHieu("XỈU", 66, "Cầu đảo chiều", "BẺ", "Vừa đảo TÀI → BẺ XỈU"))
            else:
                signals.append(TinHieu("TÀI", 66, "Cầu đảo chiều", "BẺ", "Vừa đảo XỈU → BẺ TÀI"))

    # 11. NỐI ĐUÔI MẶC ĐỊNH (luôn có, điểm thấp nhất)
    if tong >= 3:
        m3 = kq_list[-3:]
        diem = 68 if m3.count(kq_cuoi) >= 2 else 62
    else:
        diem = 58
    signals.append(TinHieu(
        "TÀI" if kq_cuoi == "Tài" else "XỈU",
        diem, "Cầu nối đuôi", "THEO",
        f"Nối đuôi → THEO {kq_cuoi}"
    ))

    # ═══════════════════════════════════════════
    # 🏆 BƯỚC 2: TỔNG HỢP ĐIỂM CÓ TRỌNG SỐ
    # ═══════════════════════════════════════════
    nhom_tai = [s for s in signals if s.ket_qua == "TÀI"]
    nhom_xiu = [s for s in signals if s.ket_qua == "XỈU"]

    def tinh_diem_vip(nhom):
        if not nhom:
            return 0.0
        sorted_s = sorted(nhom, key=lambda x: -x.diem)
        tong_diem = sorted_s[0].diem  # Tín hiệu mạnh nhất = 100%
        # Tín hiệu phụ: trọng số giảm dần
        for i, s in enumerate(sorted_s[1:], 1):
            trong_so = max(0.35 - (i - 1) * 0.08, 0.1)
            tong_diem += s.diem * trong_so
        return min(round(tong_diem, 1), 95.0)

    diem_tai = tinh_diem_vip(nhom_tai)
    diem_xiu = tinh_diem_vip(nhom_xiu)

    # ═══════════════════════════════════════════
    # 🎯 BƯỚC 3: QUYẾT ĐỊNH CUỐI CÙNG
    # ═══════════════════════════════════════════
    if diem_tai >= diem_xiu:
        du_doan = "TÀI"
        ti_le = diem_tai
        nhom_chinh = nhom_tai
    else:
        du_doan = "XỈU"
        ti_le = diem_xiu
        nhom_chinh = nhom_xiu

    # Tín hiệu mạnh nhất làm đại diện
    tin_hieu_chinh = max(nhom_chinh, key=lambda x: x.diem) if nhom_chinh else None

    # Log chi tiết
    log_signals = " | ".join([
        f"{s.ket_qua[0]}{s.hanh_dong[0]}{s.diem:.0f}({s.ten_cau[:12]})"
        for s in sorted(signals, key=lambda x: -x.diem)[:5]
    ])
    logger.info(f"🎯 VIP: {du_doan} | {ti_le}% | {tin_hieu_chinh.ten_cau if tin_hieu_chinh else 'Tổng hợp'} | [{log_signals}]")

    return {"du_doan": du_doan, "ti_le": ti_le}

# ═══════════════════════════════════════════════════════════
# ✨ TÌM PHIÊN ĐANG ĐỢI KẾT QUẢ
# ═══════════════════════════════════════════════════════════

def tim_phien_doi_va_lich_su(danh_sach_phien, n_lich_su=15):
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
        
        lich_su_raw = lst[vi_tri_bat_dau : vi_tri_bat_dau + n_lich_su + 5]
        lich_su_kq = []
        for s in lich_su_raw:
            if isinstance(s, dict):
                kq = parse_result_super(s)
                if kq:
                    lich_su_kq.append(kq)
            if len(lich_su_kq) >= n_lich_su:
                break
        lich_su_kq = lich_su_kq[::-1]
        return phien_doi, lich_su_kq
    
    phien_a, ls_a = phan_tich(danh_sach_phien)
    phien_b, ls_b = phan_tich(danh_sach_phien[::-1])
    
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
    return {"status": "ok", "msg": "🏆 VIP DUY NHẤT v9.0 đang chạy"}

@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "version": "9.0",
        "mode": "🏆 VIP DUY NHẤT - Một thuật toán tổng hợp",
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
        
        # 🏆 CHẠY THUẬT TOÁN VIP DUY NHẤT
        ket_qua = thuat_toan_vip_duy_nhat(lich_su_kq)
        
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
        
        logger.info(f"🎯 KẾT QUẢ VIP: Phiên #{phien_hien_thi} → {response['du_doan']} | {response['ti_le']}%")
        
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
    logger.info(f"🏆 THUẬT TOÁN VIP DUY NHẤT v9.0 | Cổng {port}")
    uvicorn.run("server_ai:app", host="0.0.0.0", port=port)
