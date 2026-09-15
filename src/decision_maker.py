class DecisionMaker:
    def __init__(self, low: float = 0.3, high: float = 0.7):
        self.low = low
        self.high = high

    def decide(self, score: float) -> str:
        if score < self.low:
            return "publish"
        if score > self.high:
            return "block"
        return "manual_review"

    def explain(self, score: float) -> str:
        if score < self.low:
            return "Вакансия безопасна, публикуется автоматически."
        if score > self.high:
            return "Высокий риск спама — автоматическая блокировка."
        return "Средний риск — отправлено на ручную модерацию."