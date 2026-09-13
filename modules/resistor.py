from .resistor_codes import decode_bands, format_ohms, TOLERANCE
import cv2
import numpy as np

# Nominal HSV centers for common resistor-band colors. Lighting strongly affects HSV,
# so ORBIT displays a confidence score and expects the resistor to be centered inside
# the on-screen inspection box under neutral white lighting.
COLOR_TABLE = {
    "black":  ((0, 0, 35), 0),
    "brown":  ((12, 170, 90), 1),
    "red":    ((0, 210, 180), 2),
    "orange": ((12, 230, 230), 3),
    "yellow": ((28, 220, 235), 4),
    "green":  ((60, 180, 145), 5),
    "blue":   ((110, 200, 170), 6),
    "violet": ((145, 150, 160), 7),
    "gray":   ((0, 20, 130), 8),
    "white":  ((0, 15, 235), 9),
}


def _hue_distance(a, b):
    d = abs(a - b)
    return min(d, 180 - d)


def classify_hsv(hsv):
    h, s, v = [float(x) for x in hsv]
    # Metallic tolerance bands are intentionally detected by low saturation/value rules.
    if 15 <= h <= 35 and 35 <= s <= 150 and 80 <= v <= 210:
        return "gold", 0.72
    if s < 35 and 120 <= v <= 210:
        return "silver", 0.65

    best = None
    best_score = 1e9
    for name, (center, _) in COLOR_TABLE.items():
        ch, cs, cv = center
        dh = _hue_distance(h, ch) / 25.0
        ds = abs(s - cs) / 110.0
        dv = abs(v - cv) / 120.0
        score = dh * dh + ds * ds + dv * dv
        if score < best_score:
            best_score = score
            best = name
    confidence = max(0.0, min(1.0, 1.0 - best_score / 6.0))
    return best, confidence


def _run_segments(labels):
    runs = []
    start = 0
    for i in range(1, len(labels) + 1):
        if i == len(labels) or labels[i] != labels[start]:
            runs.append((labels[start], start, i))
            start = i
    return runs


def analyze_resistor(frame, roi=None):
    """Experimental vision helper for a horizontally placed axial resistor.

    Method: crop ROI -> blur -> sample the horizontal center strip -> classify many
    HSV columns -> collapse equal-color runs -> keep likely narrow color-band runs.
    It is designed as a practical starting point, not a measurement instrument.
    """
    h, w = frame.shape[:2]
    if roi is None:
        x1, y1, x2, y2 = int(w*0.2), int(h*0.35), int(w*0.8), int(h*0.65)
    else:
        x1, y1, x2, y2 = roi
    x1,y1,x2,y2 = max(0,x1),max(0,y1),min(w,x2),min(h,y2)
    if x2-x1 < 10 or y2-y1 < 10:
        return {"ok": False, "reason": "Inspection area is too small"}
    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        return {"ok": False, "reason": "Invalid inspection area"}

    hsv = cv2.cvtColor(cv2.GaussianBlur(crop, (5, 5), 0), cv2.COLOR_BGR2HSV)
    sh, sw = hsv.shape[:2]
    strip = hsv[int(sh*0.42):int(sh*0.58), :, :]
    samples = []
    confs = []
    step = max(2, sw // 140)
    for x in range(0, sw, step):
        col = strip[:, x:min(x+step, sw), :]
        med = np.median(col.reshape(-1, 3), axis=0)
        name, conf = classify_hsv(med)
        samples.append(name)
        confs.append(conf)

    runs = _run_segments(samples)
    # A band should occupy a small but nontrivial fraction of the ROI.
    candidates = []
    for name, a, b in runs:
        width = b - a
        mean_conf = float(np.mean(confs[a:b])) if b > a else 0
        if name in COLOR_TABLE or name in ("gold", "silver"):
            if 2 <= width <= max(18, len(samples)//5) and mean_conf >= 0.35:
                candidates.append((name, a, b, mean_conf))

    # Deduplicate adjacent candidate runs with same label.
    merged = []
    for item in candidates:
        if merged and merged[-1][0] == item[0] and item[1] - merged[-1][2] <= 2:
            prev = merged[-1]
            merged[-1] = (prev[0], prev[1], item[2], (prev[3] + item[3]) / 2)
        else:
            merged.append(item)

    names = [m[0] for m in merged]
    # Try both orientations because tolerance band may be on either side.
    decoded = None
    used = None
    for seq in (names[:4], list(reversed(names[-4:])) if len(names) >= 4 else []):
        if len(seq) == 4 and seq[3] in TOLERANCE:
            val = decode_bands(seq)
            if val:
                decoded = val
                used = seq
                break

    annotated = frame.copy()
    cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 255, 255), 2)
    if decoded:
        value, tolerance = decoded
        text = f"{format_ohms(value)}  +/-{tolerance}%"
        cv2.putText(annotated, text, (x1, max(30, y1-12)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        return {
            "ok": True,
            "value_ohms": value,
            "tolerance_percent": tolerance,
            "bands": used,
            "confidence": round(float(np.mean([m[3] for m in merged[:4]])) if merged else 0, 2),
            "annotated": annotated,
        }

    return {
        "ok": False,
        "reason": "Could not confidently decode four bands. Center one resistor horizontally under white light.",
        "candidates": names,
        "annotated": annotated,
    }
