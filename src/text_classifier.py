import re
import joblib
import pymorphy2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

morph = pymorphy2.MorphAnalyzer()

# Слова-маркеры спама для быстрого rule-based сигнала
SPAM_KEYWORDS = [
    "срочно", "без опыта", "оплата сразу", "ежедневно",
    "телеграм", "whatsapp", "звоните", "пишите",
    "высокий доход", "легкие деньги", "работа мечты",
    "без вложений", "свободный график", "подработка",
]


def preprocess(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"[^а-яёa-z0-9\s]", " ", text)
    words = text.split()
    lemmas = []
    for w in words:
        if len(w) < 3:
            continue
        try:
            lemmas.append(morph.parse(w)[0].normal_form)
        except Exception:
            lemmas.append(w)
    return " ".join(lemmas)


def keyword_score(text: str) -> float:
    """Доля спам-слов в тексте (0-1)."""
    if not text:
        return 0.0
    text_lower = text.lower()
    hits = sum(1 for kw in SPAM_KEYWORDS if kw in text_lower)
    return min(hits / 5.0, 1.0)


class TextClassifier:
    def __init__(self, model_type: str = "svm"):
        self.model_type = model_type
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            min_df=2,
        )
        if model_type == "nb":
            self.model = MultinomialNB()
        else:
            base = LinearSVC(class_weight="balanced", max_iter=2000)
            self.model = CalibratedClassifierCV(base, cv=3)

    def fit(self, texts, labels):
        processed = [preprocess(t) for t in texts]
        X = self.vectorizer.fit_transform(processed)
        self.model.fit(X, labels)

    def predict_proba(self, text: str) -> float:
        processed = preprocess(text)
        X = self.vectorizer.transform([processed])
        proba = self.model.predict_proba(X)[0]
        # Индекс класса 1 (спам)
        return float(proba[1]) if len(proba) > 1 else float(proba[0])

    def save(self, path_prefix: str = "models/text_model"):
        joblib.dump(self.vectorizer, f"{path_prefix}_vectorizer.pkl")
        joblib.dump(self.model, f"{path_prefix}_model.pkl")

    @classmethod
    def load(cls, path_prefix: str = "models/text_model"):
        obj = cls.__new__(cls)
        obj.vectorizer = joblib.load(f"{path_prefix}_vectorizer.pkl")
        obj.model = joblib.load(f"{path_prefix}_model.pkl")
        obj.model_type = "loaded"
        return obj