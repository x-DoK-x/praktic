import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression


FEATURE_ORDER = ["inn_valid", "text_prob", "behavior_score", "complaints_norm"]


class RiskAggregator:
    def __init__(self):
        self.model = LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
        )
        self.fitted = False

    def _to_vector(self, features: dict) -> np.ndarray:
        return np.array([[features[k] for k in FEATURE_ORDER]])

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.fit(X, y)
        self.fitted = True

    def predict(self, features: dict) -> float:
        if not self.fitted:
            return self._heuristic(features)
        x = self._to_vector(features)
        return float(self.model.predict_proba(x)[0][1])

    @staticmethod
    def _heuristic(f: dict) -> float:
        score = (
            0.35 * (1 - f.get("inn_valid", 0)) +
            0.30 * f.get("text_prob", 0) +
            0.20 * f.get("behavior_score", 0) +
            0.15 * f.get("complaints_norm", 0)
        )
        return round(min(max(score, 0.0), 1.0), 4)

    def feature_importance(self) -> dict:
        if not self.fitted:
            return {}
        coefs = self.model.coef_[0]
        return {name: round(float(c), 3) for name, c in zip(FEATURE_ORDER, coefs)}

    def save(self, path: str = "models/aggregator.pkl"):
        joblib.dump(self.model, path)

    def load(self, path: str = "models/aggregator.pkl"):
        self.model = joblib.load(path)
        self.fitted = True