import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix,
)

from src.text_classifier import TextClassifier, keyword_score
from src.inn_checker import check_inn
from src.behavior_scorer import BehaviorScorer
from src.risk_aggregator import RiskAggregator, FEATURE_ORDER
from src.decision_maker import DecisionMaker


def build_features(df: pd.DataFrame, text_model: TextClassifier) -> np.ndarray:
    scorer = BehaviorScorer()
    rows = []
    for _, row in df.iterrows():
        inn_info = check_inn(str(row["inn"]), row["company"])
        text = f"{row['title']} {row['description']} {row['requirements']}"
        text_prob = text_model.predict_proba(text) if text.strip() else 0.0
        behavior = scorer.score({
            "age_days": row["age_days"],
            "posts_per_day": row["posts_per_day"],
            "ip_blacklisted": row["ip_blacklisted"],
            "complaints": row["complaints"],
        })
        complaints_norm = min(row["complaints"] / 10.0, 1.0)
        rows.append([
            inn_info["inn_valid"],
            text_prob,
            behavior,
            complaints_norm,
        ])
    return np.array(rows)


def evaluate(name: str, y_true, y_pred, y_proba=None):
    print(f"\n=== {name} ===")
    print(f"Accuracy : {accuracy_score(y_true, y_pred):.4f}")
    print(f"Precision: {precision_score(y_true, y_pred, zero_division=0):.4f}")
    print(f"Recall   : {recall_score(y_true, y_pred, zero_division=0):.4f}")
    print(f"F1       : {f1_score(y_true, y_pred, zero_division=0):.4f}")
    if y_proba is not None:
        print(f"ROC-AUC  : {roc_auc_score(y_true, y_proba):.4f}")
    print("Confusion matrix:")
    print(confusion_matrix(y_true, y_pred))


def main():
    os.makedirs("models", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    print("Загрузка датасета...")
    df = pd.read_csv("data/vacancies.csv")
    df["text"] = df["title"].fillna("") + " " + df["description"].fillna("") + " " + df["requirements"].fillna("")

    X_train_text, X_test_text, y_train, y_test = train_test_split(
        df["text"].tolist(), df["label"].tolist(),
        test_size=0.2, random_state=42, stratify=df["label"],
    )
    train_df = df.loc[df.index[:len(X_train_text)]].copy()
    test_df = df.loc[df.index[len(X_train_text):]].copy()

    idx_train, idx_test = train_test_split(
        df.index, test_size=0.2, random_state=42, stratify=df["label"]
    )
    train_df = df.loc[idx_train].reset_index(drop=True)
    test_df = df.loc[idx_test].reset_index(drop=True)
    y_train = train_df["label"].values
    y_test = test_df["label"].values

    print(f"Train: {len(train_df)}, Test: {len(test_df)}")


    print("\nОбучение текстового классификатора (SVM)...")
    text_model = TextClassifier(model_type="svm")
    text_model.fit(train_df["text"].tolist(), y_train)

    text_proba_test = np.array([text_model.predict_proba(t) for t in test_df["text"]])
    evaluate(
        "Текстовый классификатор (SVM)",
        y_test,
        (text_proba_test > 0.5).astype(int),
        text_proba_test,
    )


    print("\nСборка признаков для ансамбля...")
    X_train = build_features(train_df, text_model)
    X_test = build_features(test_df, text_model)


    print("\nОбучение ансамбля (логистическая регрессия)...")
    agg = RiskAggregator()
    agg.fit(X_train, y_train)

    y_proba = np.array([agg.predict(dict(zip(FEATURE_ORDER, row))) for row in X_test])
    evaluate(
        "Ансамбль (LR)",
        y_test,
        (y_proba > 0.5).astype(int),
        y_proba,
    )

    print("\nВеса признаков в ансамбле:")
    for k, v in agg.feature_importance().items():
        print(f"  {k}: {v}")


    text_model.save("models/text_model")
    agg.save("models/aggregator.pkl")
    print("\nМодели сохранены в models/")


    cm = confusion_matrix(y_test, (y_proba > 0.5).astype(int))
    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=["Норма", "Спам"],
                yticklabels=["Норма", "Спам"])
    plt.xlabel("Предсказано")
    plt.ylabel("Истина")
    plt.title("Confusion matrix — ансамбль")
    plt.tight_layout()
    plt.savefig("reports/confusion_matrix.png", dpi=150)
    print("Матрица ошибок сохранена: reports/confusion_matrix.png")


if __name__ == "__main__":
    main()