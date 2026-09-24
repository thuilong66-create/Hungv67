"""
🏆 SERVER AI - VIP THEO CẦU 50 v12.0
═══════════════════════════════════════════════
✨ MỘT THUẬT TOÁN DUY NHẤT - THEO CẦU THUẦN TÚY
   🎯 50 dạng cầu Tài Xỉu phổ biến
   ➡️ TẤT CẢ đều THEO cầu (không bẻ)
   🗳️ Gộp lại bằng BỎ PHIẾU ĐA SỐ (đơn giản, không trọng số)
   📊 Điểm tin cậy = tỷ lệ phiếu bên thắng
   ⚡ Dự đoán phiên ĐANG ĐỢI kết quả
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

app = FastAPI(title="🏆 VIP THEO CẦU 50 v12.0", version="12.0")
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
# 🏆 50 DẠNG CẦU PHỔ BIẾN - TẤT CẢ ĐỀU THEO CẦU
# ═══════════════════════════════════════════════════════════

def dem_chuoi_nguoc(kq, muc_tieu):
    dem = 0
    for x in reversed(kq):
        if x == muc_tieu:
            dem += 1
        else:
            break
    return dem

def thuat_toan_theo_cau_50(kq_list):
    """
    🏆 THUẬT TOÁN THEO CẦU 50 DẠNG - BỎ PHIẾU ĐA SỐ
    ------------------------------------------------
    Mỗi dạng cầu → 1 phiếu TÀI hoặc XỈU (hoặc KHOANG nếu không đủ điều kiện)
    Đếm phiếu → bên nào nhiều hơn thắng
    Điểm tin cậy = (phiếu thắng / tổng phiếu) × 100, giới hạn 55-95%
    """
    if not kq_list or len(kq_list) < 2:
        return {"du_doan": "TÀI", "ti_le": 55.0}
    
    kq = list(kq_list)
    tong = len(kq)
    kq_cuoi = kq[-1]
    chuoi_tai = dem_chuoi_nguoc(kq, "Tài")
    chuoi_xiu = dem_chuoi_nguoc(kq, "Xỉu")
    tong_tai = kq.count("Tài")
    tong_xiu = kq.count("Xỉu")
    tl_tai = tong_tai / tong
    
    phieu_tai = 0
    phieu_xiu = 0
    tong_phieu_hoat_dong = 0
    
    def them_phieu(ket_qua, ten_cau):
        nonlocal phieu_tai, phieu_xiu, tong_phieu_hoat_dong
        if ket_qua == "TÀI":
            phieu_tai += 1
            tong_phieu_hoat_dong += 1
        elif ket_qua == "XỈU":
            phieu_xiu += 1
            tong_phieu_hoat_dong += 1
        # None = KHOANG, không đếm
    
    # ═══════════════════════════════════════════
    # 🎯 NHÓM 1: CẦU BỆT (1-8) - THEO tiếp tục
    # ═══════════════════════════════════════════
    
    # 1. Cầu bệt 2 phiên TÀI
    if chuoi_tai == 2: them_phieu("TÀI", "Cầu bệt 2p TÀI")
    # 2. Cầu bệt 2 phiên XỈU
    if chuoi_xiu == 2: them_phieu("XỈU", "Cầu bệt 2p XỈU")
    # 3. Cầu bệt 3 phiên TÀI
    if chuoi_tai == 3: them_phieu("TÀI", "Cầu bệt 3p TÀI")
    # 4. Cầu bệt 3 phiên XỈU
    if chuoi_xiu == 3: them_phieu("XỈU", "Cầu bệt 3p XỈU")
    # 5. Cầu bệt 4 phiên TÀI
    if chuoi_tai == 4: them_phieu("TÀI", "Cầu bệt 4p TÀI")
    # 6. Cầu bệt 4 phiên XỈU
    if chuoi_xiu == 4: them_phieu("XỈU", "Cầu bệt 4p XỈU")
    # 7. Cầu bệt ≥5 phiên TÀI (vẫn THEO)
    if chuoi_tai >= 5: them_phieu("TÀI", "Cầu bệt dài TÀI")
    # 8. Cầu bệt ≥5 phiên XỈU (vẫn THEO)
    if chuoi_xiu >= 5: them_phieu("XỈU", "Cầu bệt dài XỈU")
    
    # ═══════════════════════════════════════════
    # 🎯 NHÓM 2: CẦU NHỊP 1-1 (9-11) - THEO quy luật
    # ═══════════════════════════════════════════
    
    if tong >= 4:
        m4 = kq[-4:]
        if all(m4[i] != m4[i+1] for i in range(3)):
            # 9. Cầu nhịp 1-1 ngắn 4p
            them_phieu("TÀI" if m4[-1] == "Xỉu" else "XỈU", "Cầu nhịp 1-1 4p")
            
            if tong >= 6:
                m6 = kq[-6:]
                if all(m6[i] != m6[i+1] for i in range(5)):
                    # 10. Cầu nhịp 1-1 6p
                    them_phieu("TÀI" if m6[-1] == "Xỉu" else "XỈU", "Cầu nhịp 1-1 6p")
                    
                    if tong >= 8:
                        m8 = kq[-8:]
                        if all(m8[i] != m8[i+1] for i in range(7)):
                            # 11. Cầu nhịp 1-1 8p
                            them_phieu("TÀI" if m8[-1] == "Xỉu" else "XỈU", "Cầu nhịp 1-1 8p")
    
    # ═══════════════════════════════════════════
    # 🎯 NHÓM 3: CẦU CHU KỲ 2-1 & 1-2 (12-15)
    # ═══════════════════════════════════════════
    
    if tong >= 6:
        m6 = kq[-6:]
        # 12. Chu kỳ 2-1 (TT-X-TT-X)
        if m6 == ["Tài", "Tài", "Xỉu", "Tài", "Tài", "Xỉu"]:
            them_phieu("TÀI", "Chu kỳ 2-1 TT-X")
        # 13. Chu kỳ 2-1 ngược (XX-T-XX-T)
        if m6 == ["Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu", "Tài"]:
            them_phieu("XỈU", "Chu kỳ 2-1 XX-T")
        # 14. Chu kỳ 1-2 (T-XX-T-XX)
        if m6 == ["Tài", "Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu"]:
            them_phieu("TÀI", "Chu kỳ 1-2 T-XX")
        # 15. Chu kỳ 1-2 ngược (X-TT-X-TT)
        if m6 == ["Xỉu", "Tài", "Tài", "Xỉu", "Tài", "Tài"]:
            them_phieu("XỈU", "Chu kỳ 1-2 X-TT")
    
    # Dấu hiệu chu kỳ 2-1 (3p cuối)
    if tong >= 3:
        m3 = kq[-3:]
        if m3 == ["Tài", "Tài", "Xỉu"]: them_phieu("TÀI", "Dấu hiệu 2-1 TT-X")
        if m3 == ["Xỉu", "Xỉu", "Tài"]: them_phieu("XỈU", "Dấu hiệu 2-1 XX-T")
        if m3 == ["Tài", "Xỉu", "Xỉu"]: them_phieu("TÀI", "Dấu hiệu 1-2 T-XX")
        if m3 == ["Xỉu", "Tài", "Tài"]: them_phieu("XỈU", "Dấu hiệu 1-2 X-TT")
    
    # ═══════════════════════════════════════════
    # 🎯 NHÓM 4: CẦU CÂN BẰNG 2-2 (16-17)
    # ═══════════════════════════════════════════
    
    if tong >= 8:
        m8 = kq[-8:]
        # 16. Cân bằng 2-2 (TT-XX-TT-XX)
        if m8 == ["Tài", "Tài", "Xỉu", "Xỉu", "Tài", "Tài", "Xỉu", "Xỉu"]:
            them_phieu("TÀI", "Cân bằng 2-2 TT-XX")
        # 17. Cân bằng 2-2 ngược (XX-TT-XX-TT)
        if m8 == ["Xỉu", "Xỉu", "Tài", "Tài", "Xỉu", "Xỉu", "Tài", "Tài"]:
            them_phieu("XỈU", "Cân bằng 2-2 XX-TT")
    
    if tong >= 4:
        m4 = kq[-4:]
        if m4 == ["Tài", "Tài", "Xỉu", "Xỉu"]: them_phieu("TÀI", "Dấu hiệu 2-2 TT-XX")
        if m4 == ["Xỉu", "Xỉu", "Tài", "Tài"]: them_phieu("XỈU", "Dấu hiệu 2-2 XX-TT")
    
    # ═══════════════════════════════════════════
    # 🎯 NHÓM 5: CẦU CHU KỲ 3-1 & 1-3 (18-21)
    # ═══════════════════════════════════════════
    
    if tong >= 8:
        m8 = kq[-8:]
        # 18. Chu kỳ 3-1 (TTT-X-TTT-X)
        if m8 == ["Tài", "Tài", "Tài", "Xỉu", "Tài", "Tài", "Tài", "Xỉu"]:
            them_phieu("TÀI", "Chu kỳ 3-1 TTT-X")
        # 19. Chu kỳ 3-1 ngược (XXX-T-XXX-T)
        if m8 == ["Xỉu", "Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu", "Xỉu", "Tài"]:
            them_phieu("XỈU", "Chu kỳ 3-1 XXX-T")
        # 20. Chu kỳ 1-3 (T-XXX-T-XXX)
        if m8 == ["Tài", "Xỉu", "Xỉu", "Xỉu", "Tài", "Xỉu", "Xỉu", "Xỉu"]:
            them_phieu("TÀI", "Chu kỳ 1-3 T-XXX")
        # 21. Chu kỳ 1-3 ngược (X-TTT-X-TTT)
        if m8 == ["Xỉu", "Tài", "Tài", "Tài", "Xỉu", "Tài", "Tài", "Tài"]:
            them_phieu("XỈU", "Chu kỳ 1-3 X-TTT")
    
    # ═══════════════════════════════════════════
    # 🎯 NHÓM 6: CẦU CHU KỲ 3-2 & 2-3 (22-25)
    # ═══════════════════════════════════════════
    
    if tong >= 10:
        m10 = kq[-10:]
        # 22. Chu kỳ 3-2 (TTT-XX-TTT-XX)
        if m10 == ["Tài"]*3 + ["Xỉu"]*2 + ["Tài"]*3 + ["Xỉu"]*2:
            them_phieu("TÀI", "Chu kỳ 3-2 TTT-XX")
        # 23. Chu kỳ 3-2 ngược (XXX-TT-XXX-TT)
        if m10 == ["Xỉu"]*3 + ["Tài"]*2 + ["Xỉu"]*3 + ["Tài"]*2:
            them_phieu("XỈU", "Chu kỳ 3-2 XXX-TT")
        # 24. Chu kỳ 2-3 (TT-XXX-TT-XXX)
        if m10 == ["Tài"]*2 + ["Xỉu"]*3 + ["Tài"]*2 + ["Xỉu"]*3:
            them_phieu("TÀI", "Chu kỳ 2-3 TT-XXX")
        # 25. Chu kỳ 2-3 ngược (XX-TTT-XX-TTT)
        if m10 == ["Xỉu"]*2 + ["Tài"]*3 + ["Xỉu"]*2 + ["Tài"]*3:
            them_phieu("XỈU", "Chu kỳ 2-3 XX-TTT")
    
    # ═══════════════════════════════════════════
    # 🎯 NHÓM 7: CẦU SONG TỬ (26-27)
    # ═══════════════════════════════════════════
    
    if tong >= 6:
        k1, k2, k3, k4, k5, k6 = kq[-6], kq[-5], kq[-4], kq[-3], kq[-2], kq[-1]
        if k1 == k3 == k5 and k2 == k4 == k6 and k1 != k2:
            # 26. Cầu song tử 6p
            them_phieu("TÀI" if k1 == "Tài" else "XỈU", "Cầu song tử 6p")
            
            if tong >= 8:
                k7, k8 = kq[-8], kq[-7]
                if k7 == k1 and k8 == k2:
                    # 27. Cầu song tử 8p
                    them_phieu("TÀI" if k1 == "Tài" else "XỈU", "Cầu song tử 8p")
    
    # ═══════════════════════════════════════════
    # 🎯 NHÓM 8: CẦU ĐUÔI GOM (28-31)
    # ═══════════════════════════════════════════
    
    if tong >= 3:
        m3 = kq[-3:]
        # 28. Đuôi gom 3p TÀI
        if m3.count("Tài") == 3: them_phieu("TÀI", "Đuôi gom 3p TÀI")
        # 29. Đuôi gom 3p XỈU
        if m3.count("Xỉu") == 3: them_phieu("XỈU", "Đuôi gom 3p XỈU")
    
    if tong >= 4:
        m4 = kq[-4:]
        # 30. Đuôi gom 3/4p TÀI
        if m4.count("Tài") >= 3 and m4[-1] == "Tài": them_phieu("TÀI", "Đuôi gom 4p TÀI")
        # 31. Đuôi gom 3/4p XỈU
        if m4.count("Xỉu") >= 3 and m4[-1] == "Xỉu": them_phieu("XỈU", "Đuôi gom 4p XỈU")
    
    # ═══════════════════════════════════════════
    # 🎯 NHÓM 9: CẦU THIÊN VỊ (32-35)
    # ═══════════════════════════════════════════
    
    if tong >= 10:
        # 32. Thiên TÀI mạnh ≥70%
        if tl_tai >= 0.70: them_phieu("TÀI", "Thiên TÀI mạnh")
        # 33. Thiên XỈU mạnh ≥70%
        if tl_tai <= 0.30: them_phieu("XỈU", "Thiên XỈU mạnh")
        # 34. Thiên TÀI trung bình 60-70%
        if 0.60 <= tl_tai < 0.70: them_phieu("TÀI", "Thiên TÀI TB")
        # 35. Thiên XỈU trung bình 30-40%
        if 0.30 < tl_tai <= 0.40: them_phieu("XỈU", "Thiên XỈU TB")
    
    # ═══════════════════════════════════════════
    # 🎯 NHÓM 10: CẦU GÃY ĐÔI (36-37)
    # ═══════════════════════════════════════════
    
    if tong >= 5:
        m5 = kq[-5:]
        # 36. Gãy đôi XX-TT-X → THEO X
        if m5[:2] == ["Xỉu", "Xỉu"] and m5[2:4] == ["Tài", "Tài"] and m5[4] == "Xỉu":
            them_phieu("XỈU", "Gãy đôi XX-TT-X")
        # 37. Gãy đôi TT-XX-T → THEO T
        if m5[:2] == ["Tài", "Tài"] and m5[2:4] == ["Xỉu", "Xỉu"] and m5[4] == "Tài":
            them_phieu("TÀI", "Gãy đôi TT-XX-T")
    
    # ═══════════════════════════════════════════
    # 🎯 NHÓM 11: CẦU PHỨC TẠP 3-1-1, 1-1-3 (38-39)
    # ═══════════════════════════════════════════
    
    if tong >= 5:
        m5 = kq[-5:]
        # 38. Cầu 3-1-1 (TTT-X-T) → THEO T
        if m5[:3] == ["Tài", "Tài", "Tài"] and m5[3] == "Xỉu" and m5[4] == "Tài":
            them_phieu("TÀI", "Cầu 3-1-1 TTT-X-T")
        # 39. Cầu 1-1-3 (T-X-TTT) → THEO T
        if m5[0] == "Tài" and m5[1] == "Xỉu" and m5[2:] == ["Tài", "Tài", "Tài"]:
            them_phieu("TÀI", "Cầu 1-1-3 T-X-TTT")
        # Ngược cho XỈU
        if m5[:3] == ["Xỉu", "Xỉu", "Xỉu"] and m5[3] == "Tài" and m5[4] == "Xỉu":
            them_phieu("XỈU", "Cầu 3-1-1 XXX-T-X")
        if m5[0] == "Xỉu" and m5[1] == "Tài" and m5[2:] == ["Xỉu", "Xỉu", "Xỉu"]:
            them_phieu("XỈU", "Cầu 1-1-3 X-T-XXX")
    
    # ═══════════════════════════════════════════
    # 🎯 NHÓM 12: CẦU ĐÔI XEN KẼ (40)
    # ═══════════════════════════════════════════
    
    if tong >= 4:
        m4 = kq[-4:]
        # 40. Đôi xen kẽ TT-X-XX (2 TÀI, 1 XỈU, 2 XỈU) → THEO X
        if m4[0] == "Tài" and m4[1] == "Tài" and m4[2] == "Xỉu" and m4[3] == "Xỉu":
            them_phieu("XỈU", "Đôi xen kẽ TT-XX")
        if m4[0] == "Xỉu" and m4[1] == "Xỉu" and m4[2] == "Tài" and m4[3] == "Tài":
            them_phieu("TÀI", "Đôi xen kẽ XX-TT")
    
    # ═══════════════════════════════════════════
    # 🎯 NHÓM 13: CẦU 2-1-1, 1-2-1, 1-1-2 (41-43)
    # ═══════════════════════════════════════════
    
    if tong >= 4:
        m4 = kq[-4:]
        # 41. Cầu 2-1-1 (TT-X-T) → THEO T
        if m4[0] == "Tài" and m4[1] == "Tài" and m4[2] == "Xỉu" and m4[3] == "Tài":
            them_phieu("TÀI", "Cầu 2-1-1 TT-X-T")
        if m4[0] == "Xỉu" and m4[1] == "Xỉu" and m4[2] == "Tài" and m4[3] == "Xỉu":
            them_phieu("XỈU", "Cầu 2-1-1 XX-T-X")
        # 42. Cầu 1-2-1 (T-XX-T) → THEO T
        if m4[0] == "Tài" and m4[1] == "Xỉu" and m4[2] == "Xỉu" and m4[3] == "Tài":
            them_phieu("TÀI", "Cầu 1-2-1 T-XX-T")
        if m4[0] == "Xỉu" and m4[1] == "Tài" and m4[2] == "Tài" and m4[3] == "Xỉu":
            them_phieu("XỈU", "Cầu 1-2-1 X-TT-X")
        # 43. Cầu 1-1-2 (T-X-TT) → THEO T
        if m4[0] == "Tài" and m4[1] == "Xỉu" and m4[2] == "Tài" and m4[3] == "Tài":
            them_phieu("TÀI", "Cầu 1-1-2 T-X-TT")
        if m4[0] == "Xỉu" and m4[1] == "Tài" and m4[2] == "Xỉu" and m4[3] == "Xỉu":
            them_phieu("XỈU", "Cầu 1-1-2 X-T-XX")
    
    # ═══════════════════════════════════════════
    # 🎯 NHÓM 14: ĐA SỐ KHUNG NGẮN (44-47)
    # ═══════════════════════════════════════════
    
    if tong >= 3:
        m3 = kq[-3:]
        # 44. 3 phiên cuối đa số TÀI
        if m3.count("Tài") >= 2: them_phieu("TÀI", "Đa số 3p TÀI")
        # 45. 3 phiên cuối đa số XỈU
        if m3.count("Xỉu") >= 2: them_phieu("XỈU", "Đa số 3p XỈU")
    
    if tong >= 5:
        m5 = kq[-5:]
        # 46. 5 phiên cuối đa số TÀI
        if m5.count("Tài") >= 3: them_phieu("TÀI", "Đa số 5p TÀI")
        # 47. 5 phiên cuối đa số XỈU
        if m5.count("Xỉu") >= 3: them_phieu("XỈU", "Đa số 5p XỈU")
    
    # ═══════════════════════════════════════════
    # 🎯 NHÓM 15: NỐI ĐUÔI & KHUNG DÀI (48-50)
    # ═══════════════════════════════════════════
    
    # 48. Nối đuôi phiên cuối (luôn THEO)
    them_phieu("TÀI" if kq_cuoi == "Tài" else "XỈU", "Nối đuôi cuối")
    
    if tong >= 8:
        m8 = kq[-8:]
        # 49. 8 phiên cuối đa số TÀI
        if m8.count("Tài") >= 5: them_phieu("TÀI", "Đa số 8p TÀI")
        # 50. 8 phiên cuối đa số XỈU
        if m8.count("Xỉu") >= 5: them_phieu("XỈU", "Đa số 8p XỈU")
    
    # ═══════════════════════════════════════════
    # 🗳️ BỎ PHIẾU ĐA SỐ - QUYẾT ĐỊNH CUỐI
    # ═══════════════════════════════════════════
    
    if tong_phieu_hoat_dong == 0:
        return {"du_doan": "TÀI" if kq_cuoi == "Tài" else "XỈU", "ti_le": 55.0}
    
    if phieu_tai > phieu_xiu:
        du_doan = "TÀI"
        phieu_thang = phieu_tai
    elif phieu_xiu > phieu_tai:
        du_doan = "XỈU"
        phieu_thang = phieu_xiu
    else:
        # Hòa nhau → nối đuôi
        du_doan = "TÀI" if kq_cuoi == "Tài" else "XỈU"
        phieu_thang = phieu_tai
    
    # Điểm tin cậy = tỷ lệ phiếu thắng, giới hạn 55-95%
    ty_le_phieu = phieu_thang / tong_phieu_hoat_dong * 100
    ti_le = round(55 + (ty_le_phieu - 50) * 0.8, 1)
    ti_le = max(55.0, min(ti_le, 95.0))
    
    logger.info(f"🗳️ Bầu cử 50 dạng: TÀI={phieu_tai} XỈU={phieu_xiu} | {du_doan} thắng | {ti_le}% | {tong_phieu_hoat_dong}/50 tín hiệu")
    
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
    return {"status": "ok", "msg": "🏆 VIP THEO CẦU 50 v12.0 đang chạy"}

@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "version": "12.0",
        "mode": "🏆 THEO CẦU 50 dạng - Bỏ phiếu đa số",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/api/scan")
async def scan_game(tool: str, username: str):
    logger.info(f"🏆 THEO CẦU 50 Scan: {tool} | {username}")

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
        
        # 🏆 CHẠY THUẬT TOÁN THEO CẦU 50 DẠNG
        ket_qua = thuat_toan_theo_cau_50(lich_su_kq)
        
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
        
        logger.info(f"🎯 KẾT QUẢ: Phiên #{phien_hien_thi} → {response['du_doan']} | {response['ti_le']}%")
        
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
    logger.info(f"🏆 VIP THEO CẦU 50 v12.0 | Bỏ phiếu đa số | Cổng {port}")
    uvicorn.run("server_ai:app", host="0.0.0.0", port=port)
