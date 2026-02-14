import math
from collections import defaultdict

def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0

def std(xs):
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    v = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return math.sqrt(v)

def zscore(x, m, s):
    return 0.0 if s == 0 else (x - m) / s

def detect_anomalies(events, min_events=8, threshold=2.5):
    """
    events: list of dicts {staff_id, amount, event_type, object_id, object_type, created_at}
    Simple z-score by staff within event_type.
    """
    grouped = defaultdict(list)
    for e in events:
        key = (e["event_type"], e.get("staff_id"))
        grouped[key].append(float(e.get("amount", 0.0)))

    anomalies = []
    for e in events:
        key = (e["event_type"], e.get("staff_id"))
        amounts = grouped[key]
        if len(amounts) < min_events:
            continue
        m = mean(amounts)
        s = std(amounts)
        score = zscore(float(e.get("amount", 0.0)), m, s)
        if abs(score) >= threshold:
            anomalies.append((e, score, m, s))
    return anomalies
