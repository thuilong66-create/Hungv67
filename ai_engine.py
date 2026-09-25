"""
🧠 AI ENGINE PRO - Gộp từ ai_core.py + taixiu_ai.py
═══════════════════════════════════════════════════════
✅ PatternEngine (23 dạng cầu) - từ ai_core.py
✅ MarkovEngine (order 1-5) - kết hợp cả 2 file
✅ StreakEngine (phát hiện cầu bệt dài) - từ ai_core.py
✅ FrequencyEngine (đa khung 10/30/50) - từ ai_core.py
✅ MLP Neural Network (pure Python, không cần thư viện) - từ taixiu_ai.py
✅ Ensemble trọng số động tự điều chỉnh - từ taixiu_ai.py
✅ Tự học online - càng dùng càng chính xác
"""
import math
import json
import os
from collections import deque, defaultdict

# Thử import numpy, nếu không có thì dùng pure Python
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

LABELS = ("T", "X")

def _clamp(val, lo, hi):
    return max(lo, min(hi, val))

def _sigmoid(x):
    if x > 500: return 1.0
    if x < -500: return 0.0
    return 1.0 / (1.0 + math.exp(-x))

# ═══════════════════════════════════════════
# 1. PATTERN ENGINE (23 dạng cầu)
# ═══════════════════════════════════════════
class PatternEngine:
    PATTERNS = [
        ("alt_TX", 2, lambda t: t[-1]!=t[-2] and t[-1]=="X", lambda t: t[-1]),
        ("alt_XT", 2, lambda t: t[-1]!=t[-2] and t[-1]=="T", lambda t: t[-1]),
        ("TTT", 3, lambda t: t[-1]==t[-2]==t[-3]=="T", lambda t: "X"),
        ("XXX", 3, lambda t: t[-1]==t[-2]==t[-3]=="X", lambda t: "T"),
        ("T_X_T", 3, lambda t: t[-1]=="T" and t[-2]=="X" and t[-3]=="T", lambda t: "T"),
        ("X_T_X", 3, lambda t: t[-1]=="X" and t[-2]=="T" and t[-3]=="X", lambda t: "X"),
        ("TTTT", 4, lambda t: all(x=="T" for x in t[-4:]), lambda t: "X"),
        ("XXXX", 4, lambda t: all(x=="X" for x in t[-4:]), lambda t: "T"),
        ("T_T_X_X", 4, lambda t: t[-1]==t[-2]=="X" and t[-3]==t[-4]=="T", lambda t: "X"),
        ("X_X_T_T", 4, lambda t: t[-1]==t[-2]=="T" and t[-3]==t[-4]=="X", lambda t: "T"),
        ("T_X_X_T", 4, lambda t: t[-1]=="T" and t[-2]==t[-3]=="X" and t[-4]=="T", lambda t: "T"),
        ("X_T_T_X", 4, lambda t: t[-1]=="X" and t[-2]==t[-3]=="T" and t[-4]=="X", lambda t: "X"),
        ("T_T_X_T", 4, lambda t: t[-1]=="T" and t[-2]=="X" and t[-3]=="T" and t[-4]=="T", lambda t: "T"),
        ("X_X_T_X", 4, lambda t: t[-1]=="X" and t[-2]=="T" and t[-3]=="X" and t[-4]=="X", lambda t: "X"),
        ("T_T_T_X", 4, lambda t: t[-1]=="X" and t[-2]==t[-3]==t[-4]=="T", lambda t: "X"),
        ("X_X_X_T", 4, lambda t: t[-1]=="T" and t[-2]==t[-3]==t[-4]=="X", lambda t: "T"),
        ("T_X_T_X_b", 4, lambda t: t[-1]=="T" and t[-2]=="X" and t[-3]=="X" and t[-4]=="T", lambda t: "T"),
        ("X_T_X_T_b", 4, lambda t: t[-1]=="X" and t[-2]=="T" and t[-3]=="T" and t[-4]=="X", lambda t: "X"),
        ("T_X_T_X_T", 5, lambda t: t[-1]=="T" and t[-2]=="X" and t[-3]=="T" and t[-4]=="X" and t[-5]=="T", lambda t: "X"),
        ("X_T_X_T_X", 5, lambda t: t[-1]=="X" and t[-2]=="T" and t[-3]=="X" and t[-4]=="T" and t[-5]=="X", lambda t: "T"),
        ("T_T_X_T_X", 5, lambda t: t[-1]=="X" and t[-2]=="T" and t[-3]=="X" and t[-4]=="T" and t[-5]=="T", lambda t: "X"),
        ("X_X_T_X_T", 5, lambda t: t[-1]=="T" and t[-2]=="X" and t[-3]=="T" and t[-4]=="X" and t[-5]=="X", lambda t: "T"),
        ("pair_break", 6, lambda t: t[-1]!=t[-2] and t[-3]==t[-4] and t[-5]==t[-6] and t[-3]!=t[-5], lambda t: t[-1]),
    ]
    
    def predict(self, hist_list):
        if len(hist_list) < 2:
            return "T", 0.5
        tail_len = len(hist_list)
        matched = []
        for pname, min_len, pred, label_func in self.PATTERNS:
            if tail_len < min_len:
                continue
            if not pred(hist_list):
                continue
            count = 0
            total_windows = max(0, tail_len - min_len + 1)
            for i in range(total_windows):
                window = hist_list[i:i+min_len]
                if pred(window):
                    count += 1
            rarity = 1.0 - (count / total_windows) if total_windows > 0 else 1.0
            matched.append((pname, label_func(hist_list), _clamp(rarity, 0.0, 1.0)))
        if not matched:
            return "T", 0.5
        best = max(matched, key=lambda x: x[2])
        return best[1], best[2]

# ═══════════════════════════════════════════
# 2. MARKOV ENGINE (order 1-5)
# ═══════════════════════════════════════════
class MarkovEngine:
    def __init__(self, max_order=5):
        self.max_order = max_order
        self.tables = {o: defaultdict(lambda: defaultdict(int)) for o in range(1, max_order+1)}
    
    def train(self, hist_list):
        for i in range(len(hist_list)):
            for order in range(1, self.max_order+1):
                if i < order:
                    continue
                state = tuple(hist_list[i-order:i])
                self.tables[order][state][hist_list[i]] += 1
    
    def update(self, label, hist_list):
        for order in range(1, self.max_order+1):
            if len(hist_list) <= order:
                continue
            state = tuple(hist_list[-(order+1):-1])
            self.tables[order][state][label] += 1
    
    def predict(self, hist_list):
        best_score = -1.0
        best_probs = {}
        for order in range(1, self.max_order+1):
            if len(hist_list) < order:
                continue
            state = tuple(hist_list[-order:])
            counts = self.tables[order][state]
            total_counts = sum(counts.values())
            if total_counts == 0:
                continue
            smoothed = total_counts + 2
            prob_T = (counts.get("T", 0) + 1) / smoothed
            prob_X = (counts.get("X", 0) + 1) / smoothed
            confidence = max(prob_T, prob_X)
            score = math.log(total_counts + 1) * confidence / math.sqrt(order)
            if score > best_score:
                best_score = score
                best_probs = {"T": prob_T, "X": prob_X}
        if not best_probs:
            return "T", 0.5
        if best_probs["T"] >= best_probs["X"]:
            return "T", best_probs["T"]
        return "X", best_probs["X"]

# ═══════════════════════════════════════════
# 3. STREAK ENGINE (cầu bệt)
# ═══════════════════════════════════════════
class StreakEngine:
    def __init__(self, window=20):
        self.window = window
    
    def predict(self, hist_list):
        if len(hist_list) < 5:
            return "T", 0.5
        w = hist_list[-self.window:] if len(hist_list) >= self.window else hist_list
        counts = {"T": w.count("T"), "X": w.count("X")}
        dominant = max(counts.values())
        ratio = dominant / len(w)
        break_prob = _clamp((ratio - 0.5) * 2.0, 0.0, 1.0)
        last = w[-1]
        if break_prob > 0.5:
            pred = "X" if last == "T" else "T"
            conf = break_prob
        else:
            pred = last
            conf = 0.5 + (0.5 - break_prob) * 0.4
        return pred, _clamp(conf, 0.0, 1.0)

# ═══════════════════════════════════════════
# 4. FREQUENCY ENGINE (đa khung)
# ═══════════════════════════════════════════
class FrequencyEngine:
    def __init__(self, windows=(10, 30, 50)):
        self.windows = windows
    
    def predict(self, hist_list):
        if len(hist_list) < 10:
            return "T", 0.5
        ratios = {}
        for w in self.windows:
            if len(hist_list) >= w:
                ratios[w] = hist_list[-w:].count("T") / w
            else:
                ratios[w] = hist_list.count("T") / len(hist_list)
        short, mid, long = ratios[10], ratios[30], ratios[50]
        momentum = None
        if short > mid > long: momentum = "T"
        elif short < mid < long: momentum = "X"
        reversion = None
        if abs(short - long) > 0.20:
            reversion = "X" if short > long else "T"
        pred = reversion if reversion else (momentum if momentum else hist_list[-1])
        conf = abs(short - 0.5) * 2.0
        return pred, _clamp(conf, 0.0, 1.0)

# ═══════════════════════════════════════════
# 5. MLP NEURAL NETWORK (pure Python)
# ═══════════════════════════════════════════
class MLPEngine:
    def __init__(self, input_size=12, hidden=16, lr=0.01):
        self.lr = lr
        import random
        self.W1 = [[random.uniform(-0.1, 0.1) for _ in range(hidden)] for _ in range(input_size)]
        self.b1 = [0.0] * hidden
        self.W2 = [random.uniform(-0.1, 0.1) for _ in range(hidden)]
        self.b2 = 0.0
        self.last_feats = None
    
    def _extract_features(self, hist_list):
        n = len(hist_list)
        nums = [1 if x == "T" else 0 for x in hist_list]
        feats = [0.0] * 12
        if n == 0:
            return feats
        feats[0] = sum(nums) / n  # ratio toàn bộ
        feats[1] = sum(nums[-10:]) / min(n, 10)
        feats[2] = sum(nums[-5:]) / min(n, 5)
        feats[3] = sum(nums[-3:]) / min(n, 3)
        current = nums[-1]
        streak = 0
        for v in reversed(nums):
            if v == current: streak += 1
            else: break
        feats[4] = min(streak / 10.0, 1.0)
        feats[5] = float(current)
        feats[6] = feats[0] - 0.5
        if n >= 2:
            switches = sum(1 for i in range(1, min(n, 10)) if nums[-i] != nums[-i-1])
            feats[7] = switches / min(n-1, 9)
        feats[8] = sum(nums[-20:]) / min(n, 20) if n >= 1 else 0.5
        feats[9] = abs(feats[1] - 0.5)
        feats[10] = 1.0 if n >= 2 and nums[-1] == nums[-2] else 0.0
        feats[11] = 1.0
        return feats
    
    def _forward(self, feats):
        hidden = []
        for j in range(len(self.b1)):
            z = self.b1[j]
            for i in range(len(feats)):
                z += feats[i] * self.W1[i][j]
            hidden.append(_sigmoid(z))
        out = self.b2
        for j in range(len(hidden)):
            out += hidden[j] * self.W2[j]
        return _sigmoid(out), hidden
    
    def predict(self, hist_list):
        feats = self._extract_features(hist_list)
        self.last_feats = feats
        prob_T, _ = self._forward(feats)
        prob_T = _clamp(prob_T, 0.05, 0.95)
        if prob_T >= 0.5:
            return "T", prob_T
        return "X", 1 - prob_T
    
    def train(self, actual_label):
        if self.last_feats is None:
            return
        y = 1.0 if actual_label == "T" else 0.0
        feats = self.last_feats
        prob_T, hidden = self._forward(feats)
        error = y - prob_T
        d_out = error * prob_T * (1 - prob_T)
        self.b2 += self.lr * d_out
        for j in range(len(self.W2)):
            self.W2[j] += self.lr * d_out * hidden[j]
        for j in range(len(self.b1)):
            d_h = d_out * self.W2[j] * hidden[j] * (1 - hidden[j])
            self.b1[j] += self.lr * d_h
            for i in range(len(feats)):
                self.W1[i][j] += self.lr * d_h * feats[i]
        self.last_feats = None

# ═══════════════════════════════════════════
# 🏆 AI PRO ENSEMBLE - KẾT HỢP TẤT CẢ
# ═══════════════════════════════════════════
class AIProEnsemble:
    def __init__(self):
        self.pattern = PatternEngine()
        self.markov = MarkovEngine(max_order=5)
        self.streak = StreakEngine(window=20)
        self.freq = FrequencyEngine()
        self.mlp = MLPEngine()
        self.weights = {"pattern": 0.25, "markov": 0.30, "streak": 0.15, "freq": 0.15, "mlp": 0.15}
        self.history = deque(maxlen=500)
        self.last_preds = None
    
    def update(self, label):
        """Cập nhật sau khi có kết quả thực tế - tự học"""
        hist_list = list(self.history)
        self.markov.update(label, hist_list)
        self.mlp.train(label)
        # Tự điều chỉnh weights: thành phần nào dự đoán đúng → tăng weight
        if self.last_preds:
            for name, (pred, conf) in self.last_preds.items():
                if pred == label:
                    self.weights[name] *= 1.05
                else:
                    self.weights[name] *= 0.95
            total = sum(self.weights.values())
            for k in self.weights:
                self.weights[k] /= total
        self.history.append(label)
        if len(self.history) >= 5:
            self.markov.train(list(self.history))
    
    def predict(self, hist_list=None):
        if hist_list is None:
            hist_list = list(self.history)
        if len(hist_list) < 2:
            return {"du_doan": "TÀI", "ti_le": 55.0}
        
        preds = {}
        preds["pattern"] = self.pattern.predict(hist_list)
        preds["markov"] = self.markov.predict(hist_list)
        preds["streak"] = self.streak.predict(hist_list)
        preds["freq"] = self.freq.predict(hist_list)
        preds["mlp"] = self.mlp.predict(hist_list)
        self.last_preds = preds
        
        # Ensemble: tổng hợp có trọng số
        score_T = 0.0
        score_X = 0.0
        for name, (pred, conf) in preds.items():
            w = self.weights[name]
            if pred == "T":
                score_T += w * conf
            else:
                score_X += w * conf
        
        total = score_T + score_X
        if total == 0:
            return {"du_doan": "TÀI", "ti_le": 55.0}
        
        prob_T = score_T / total
        if prob_T >= 0.5:
            du_doan = "TÀI"
            ti_le = round(55 + (prob_T - 0.5) * 80, 1)
        else:
            du_doan = "XỈU"
            ti_le = round(55 + (0.5 - prob_T) * 80, 1)
        ti_le = max(55.0, min(ti_le, 95.0))
        
        detail = " | ".join([f"{n[:3]}={p}({c:.2f})" for n, (p, c) in preds.items()])
        print(f"🧠 AI PRO: {du_doan} | {ti_le}% | {detail}")
        
        return {"du_doan": du_doan, "ti_le": ti_le}

# Singleton - dùng chung cho toàn bộ server
_ai_instance = None

def get_ai_engine():
    global _ai_instance
    if _ai_instance is None:
        _ai_instance = AIProEnsemble()
    return _ai_instance
