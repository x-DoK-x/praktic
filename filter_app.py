import os
import streamlit as st
import pandas as pd

from src.inn_checker import check_inn
from src.text_classifier import TextClassifier, keyword_score
from src.behavior_scorer import BehaviorScorer
from src.risk_aggregator import RiskAggregator
from src.decision_maker import DecisionMaker

st.set_page_config(
    page_title="Антиспам-фильтрация вакансий",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Система антиспам-фильтрации вакансий")
st.caption("MVP: мультифакторная проверка (ИНН + текст + поведение + жалобы)")


@st.cache_resource
def load_models():
    text_model = None
    agg = RiskAggregator()
    if os.path.exists("models/text_model_model.pkl"):
        text_model = TextClassifier.load("models/text_model")
    if os.path.exists("models/aggregator.pkl"):
        agg.load("models/aggregator.pkl")
    return text_model, agg


text_model, agg = load_models()
scorer = BehaviorScorer()
decider = DecisionMaker()

if text_model is None:
    st.warning(
        "Модели не найдены. Сначала запусти: "
        "`python generate_dataset.py && python train_models.py`"
    )

with st.sidebar:
    st.header("О системе")
    st.write(
        "Система вычисляет риск-скор вакансии (0–1) на основе:"
        "\n- валидности ИНН и совпадения с реестром ФНС;"
        "\n- вероятности спама по тексту (TF-IDF + SVM);"
        "\n- поведенческих признаков пользователя;"
        "\n- количества жалоб."
    )
    st.write("Пороги: <0.3 — публикация, >0.7 — блок.")

tab1, tab2 = st.tabs(["🔍 Проверка вакансии", "📊 Пакетная обработка"])

with tab1:
    with st.form("vacancy_form"):
        col1, col2 = st.columns(2)
        with col1:
            company = st.text_input("Название компании", "ООО Рога и Копыта")
            inn = st.text_input("ИНН", "7707083893")
            title = st.text_input("Заголовок вакансии", "Работа с высокой оплатой без опыта")
        with col2:
            age_days = st.number_input("Возраст аккаунта (дней)", 0, 3650, 15)
            posts_per_day = st.number_input("Публикаций в сутки", 0, 100, 25)
            complaints = st.number_input("Жалоб на вакансию", 0, 100, 5)
            ip_blacklisted = st.checkbox("IP в чёрном списке", value=True)

        description = st.text_area(
            "Описание вакансии",
            "СРОЧНО! Оплата 5000 руб/день. Без опыта, без вложений. "
            "Пишите в телеграм. Работа из дома, свободный график.",
            height=150,
        )
        requirements = st.text_area(
            "Требования",
            "Без опыта! Обучим всему за 1 день!",
            height=80,
        )

        submitted = st.form_submit_button("Проверить вакансию")

    if submitted:
        # 1. ИНН
        inn_info = check_inn(inn, company)

        # 2. Текст
        full_text = f"{title} {description} {requirements}"
        if text_model is not None:
            text_prob = text_model.predict_proba(full_text)
        else:
            text_prob = keyword_score(full_text)

        # 3. Поведение
        behavior = scorer.score({
            "age_days": age_days,
            "posts_per_day": posts_per_day,
            "ip_blacklisted": int(ip_blacklisted),
            "complaints": complaints,
        })
        complaints_norm = min(complaints / 10.0, 1.0)

        # 4. Ансамбль
        features = {
            "inn_valid": inn_info["inn_valid"],
            "text_prob": text_prob,
            "behavior_score": behavior,
            "complaints_norm": complaints_norm,
        }
        risk = agg.predict(features)
        decision = decider.decide(risk)

        st.divider()
        st.subheader("Результат проверки")

        c1, c2, c3 = st.columns(3)
        c1.metric("Риск-скор", f"{risk:.2f}")
        c2.metric("Решение", decision)
        c3.metric("ИНН валиден", "Да" if inn_info["inn_valid"] else "Нет")

        st.info(decider.explain(risk))

        st.subheader("Вклад признаков")
        chart_data = pd.DataFrame({
            "Признак": ["ИНН валиден", "Текст (спам-вероятность)",
                        "Поведение", "Жалобы (норм.)"],
            "Значение": [
                inn_info["inn_valid"],
                text_prob,
                behavior,
                complaints_norm,
            ],
        })
        st.bar_chart(chart_data.set_index("Признак"))

        st.subheader("Детали")
        st.json({
            "inn_check": inn_info,
            "text_prob": round(text_prob, 4),
            "behavior_score": behavior,
            "complaints_norm": round(complaints_norm, 4),
            "risk_score": round(risk, 4),
            "decision": decision,
        })

with tab2:
    st.write("Загрузи CSV с колонками: company, inn, title, description, "
             "requirements, age_days, posts_per_day, ip_blacklisted, complaints.")
    uploaded = st.file_uploader("CSV-файл", type=["csv"])

    if uploaded is not None and text_model is not None:
        df = pd.read_csv(uploaded)
        results = []
        for _, row in df.iterrows():
            inn_info = check_inn(str(row.get("inn", "")), str(row.get("company", "")))
            text = f"{row.get('title','')} {row.get('description','')} {row.get('requirements','')}"
            text_prob = text_model.predict_proba(text) if text.strip() else 0.0
            behavior = scorer.score({
                "age_days": row.get("age_days", 365),
                "posts_per_day": row.get("posts_per_day", 0),
                "ip_blacklisted": row.get("ip_blacklisted", 0),
                "complaints": row.get("complaints", 0),
            })
            complaints_norm = min(row.get("complaints", 0) / 10.0, 1.0)
            risk = agg.predict({
                "inn_valid": inn_info["inn_valid"],
                "text_prob": text_prob,
                "behavior_score": behavior,
                "complaints_norm": complaints_norm,
            })
            results.append({
                "company": row.get("company"),
                "risk_score": round(risk, 3),
                "decision": decider.decide(risk),
            })
        result_df = pd.DataFrame(results)
        st.dataframe(result_df)
        st.download_button(
            "Скачать результаты CSV",
            result_df.to_csv(index=False).encode("utf-8"),
            "results.csv",
            "text/csv",
        )