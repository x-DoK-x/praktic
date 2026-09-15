"""
Класс 0 — нормальная вакансия, класс 1 — спам/фейк.
"""
import random
import pandas as pd
import os

random.seed(42)

NORMAL_COMPANIES = [
    "ООО Яндекс", "ПАО Сбербанк", "ООО Тинькофф", "АО ВТБ",
    "ООО МТС", "ПАО Ростелеком", "ООО КРОК", "АО Лаборатория Касперского",
    "ООО 1С", "ПАО Газпром", "ООО Skillbox", "АО Альфа-Банк",
]

SPAM_COMPANIES = [
    "ООО Рога и Копыта", "ИП Иванов", "ООО Быстрые Деньги",
    "ООО Золотая Жила", "ИП Петров А.А.", "ООО Лёгкий Заработок",
    "ООО Работа Мечты", "ИП Сидоров", "ООО Деньги Сразу",
]

NORMAL_TITLES = [
    "Python-разработчик", "Аналитик данных", "Frontend-разработчик",
    "Менеджер проектов", "QA-инженер", "Системный администратор",
    "Data Scientist", "Backend-разработчик", "DevOps-инженер",
    "Бизнес-аналитик", "Product Manager", "Технический писатель",
]

SPAM_TITLES = [
    "Работа с высокой оплатой без опыта", "Заработок из дома 100000 руб/день",
    "Срочно! Набор сотрудников", "Свободный график, оплата сразу",
    "Простая работа на дому", "Набор менеджеров без опыта",
    "Работа мечты — 200000 руб/неделю", "Подработка для всех",
    "Требуются люди, оплата ежедневно",
]

NORMAL_DESCRIPTIONS = [
    "Ищем опытного специалиста для работы над продуктом. Требования: опыт от 3 лет, знание Python, Django, PostgreSQL. Обязанности: разработка новых модулей, code review, участие в архитектурных решениях. Условия: ДМС, гибкий график, офис в центре.",
    "Присоединяйтесь к команде аналитиков. Требования: SQL, Python, понимание статистики. Обязанности: построение отчётов, анализ метрик, A/B тесты. Условия: официальное трудоустройство, обучение, карьерный рост.",
    "Мы ищем frontend-разработчика с опытом React. Требования: React, TypeScript, Redux, опыт коммерческой разработки от 2 лет. Обязанности: разработка интерфейсов, интеграция с API. Условия: удалёнка, ДМС, оплата по итогам собеседования.",
    "Требуется системный администратор. Обязанности: поддержка серверов Linux, настройка сети, резервное копирование. Требования: опыт работы от 2 лет, знание Windows Server, Linux. Условия: полный день, соцпакет.",
    "Ищем DevOps-инженера. Требования: Docker, Kubernetes, CI/CD, опыт работы с облаками. Обязанности: автоматизация деплоя, мониторинг, поддержка инфраструктуры. Условия: удалёнка, оплата 200000-250000 руб.",
]

SPAM_DESCRIPTIONS = [
    "СРОЧНО! Требуются люди для简单 работы. Оплата 5000 руб/день. Без опыта, без вложений. Писать в телеграм @easy_money. Работа из дома, свободный график. Звоните прямо сейчас!",
    "Заработок от 100000 рублей в неделю! Никакого опыта не нужно. Обучим бесплатно. Оплата ежедневно. Пишите в WhatsApp. Количество мест ограничено!",
    "Работа мечты! Гибкий график, высокая оплата, без начальников. Требуются люди с 18 лет. Оплата сразу после смены. Подробности в личные сообщения.",
    "Набор сотрудников для удалённой работы. Оплата 3000 руб за 2 часа. Никаких навыков не требуется. Срочно! Пишите в Telegram. Работа из любой точки мира.",
    "Свободная подработка! Оплата ежедневно 2000-5000 руб. Без опыта и вложений. Быстрое оформление. Звоните с 9 до 21. Количество мест ограничено.",
]

NORMAL_REQUIREMENTS = [
    "Опыт от 3 лет, профильное образование, знание английского.",
    "Высшее образование, опыт работы от 2 лет, аналитическое мышление.",
    "Портфолио, опыт коммерческой разработки, знание Git.",
    "Опыт администрирования Linux, знание сетей, ответственность.",
    "Опыт работы с Docker, Kubernetes, понимание CI/CD.",
]

SPAM_REQUIREMENTS = [
    "Без опыта! Обучим всему за 1 день!",
    "Никаких навыков не требуется!",
    "Возраст от 18 лет, наличие телефона.",
    "Ответственность, желание зарабатывать, без опыта.",
    "Срочно! Наличие свободного времени.",
]


def generate_inn(valid: bool) -> str:
    digits = [random.randint(1, 9)] + [random.randint(0, 9) for _ in range(8)]
    if valid:
        weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        control = sum(d * w for d, w in zip(digits, weights)) % 11 % 10
        digits.append(control)
    else:
        digits.append(random.randint(0, 9))
    return "".join(map(str, digits))


def generate_row(label: int) -> dict:
    if label == 0:  # норма
        company = random.choice(NORMAL_COMPANIES)
        title = random.choice(NORMAL_TITLES)
        description = random.choice(NORMAL_DESCRIPTIONS)
        requirements = random.choice(NORMAL_REQUIREMENTS)
        inn = generate_inn(valid=True)
        age_days = random.randint(180, 3650)
        posts_per_day = random.randint(0, 5)
        ip_blacklisted = 0
        complaints = 0
    else:  # спам
        company = random.choice(SPAM_COMPANIES)
        title = random.choice(SPAM_TITLES)
        description = random.choice(SPAM_DESCRIPTIONS)
        requirements = random.choice(SPAM_REQUIREMENTS)
        inn = generate_inn(valid=random.random() > 0.7)
        age_days = random.randint(0, 60)
        posts_per_day = random.randint(10, 50)
        ip_blacklisted = random.choice([0, 1, 1])
        complaints = random.randint(2, 10)

    return {
        "company": company,
        "inn": inn,
        "title": title,
        "description": description,
        "requirements": requirements,
        "age_days": age_days,
        "posts_per_day": posts_per_day,
        "ip_blacklisted": ip_blacklisted,
        "complaints": complaints,
        "label": label,
    }


def main():
    os.makedirs("data", exist_ok=True)
    rows = [generate_row(0) for _ in range(900)] + [generate_row(1) for _ in range(300)]
    random.shuffle(rows)
    df = pd.DataFrame(rows)
    df.to_csv("data/vacancies.csv", index=False, encoding="utf-8")
    print(f"Сохранено {len(df)} записей в data/vacancies.csv")
    print(df["label"].value_counts())


if __name__ == "__main__":
    main()