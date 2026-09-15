def normalize(x: float, min_val: float, max_val: float) -> float:
    if max_val == min_val:
        return 0.0
    return max(0.0, min(1.0, (x - min_val) / (max_val - min_val)))


class BehaviorScorer:
    """
    Вычисляет поведенческий скор в диапазоне [0, 1].
    """
    WEIGHTS = {
        "age": 0.25,          # молодой аккаунт — подозрительно
        "frequency": 0.30,    # много публикаций в сутки
        "ip": 0.20,           # IP в чёрном списке
        "complaints": 0.25,   # жалобы
    }

    def score(self, features: dict) -> float:
        age_days = features.get("age_days", 365)
        posts_per_day = features.get("posts_per_day", 0)
        ip_blacklisted = features.get("ip_blacklisted", 0)
        complaints = features.get("complaints", 0)

        age_score = 1.0 - normalize(age_days, 0, 365)       # молодой = 1
        freq_score = normalize(posts_per_day, 0, 30)         # много = 1
        ip_score = float(ip_blacklisted)                     # 0 или 1
        comp_score = normalize(complaints, 0, 10)            # много = 1

        total = (
            self.WEIGHTS["age"] * age_score +
            self.WEIGHTS["frequency"] * freq_score +
            self.WEIGHTS["ip"] * ip_score +
            self.WEIGHTS["complaints"] * comp_score
        )
        return round(min(total, 1.0), 4)