def validate_inn(inn: str) -> bool:
    if not inn or not inn.isdigit():
        return False

    if len(inn) == 10:
        weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        control = sum(int(inn[i]) * weights[i] for i in range(9)) % 11 % 10
        return control == int(inn[9])

    if len(inn) == 12:
        w1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        w2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        c1 = sum(int(inn[i]) * w1[i] for i in range(10)) % 11 % 10
        c2 = sum(int(inn[i]) * w2[i] for i in range(11)) % 11 % 10
        return c1 == int(inn[10]) and c2 == int(inn[11])

    return False


def levenshtein(a: str, b: str) -> int:
    a, b = a.lower(), b.lower()
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n

    prev = list(range(m + 1))
    for i in range(1, n + 1):
        curr = [i] + [0] * m
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            curr[j] = min(
                prev[j] + 1,
                curr[j - 1] + 1,
                prev[j - 1] + cost,
            )
        prev = curr
    return prev[m]


# Мини-реестр ФНС (mock). В реальной системе — выгрузка ЕГРЮЛ.
FNS_REGISTRY = {
    "7707083893": "ООО Яндекс",
    "7707083894": "ПАО Сбербанк",
    "7710137066": "ООО Тинькофф",
    "7702070139": "АО ВТБ",
    "7707049388": "ООО МТС",
    "7710042545": "ПАО Ростелеком",
    "7722132803": "ООО КРОК",
    "7736050003": "АО Лаборатория Касперского",
    "7707082946": "ООО 1С",
    "7736050004": "ПАО Газпром",
}

def fuzzy_search(name: str, threshold: int = 5) -> float:
    """
    Ищет ближайшее название компании в реестре ФНС.
    Возвращает схожесть в диапазоне [0, 1]: 1 — точное совпадение.
    """
    if not name:
        return 0.0

    best = 0.0
    for registry_name in FNS_REGISTRY.values():
        dist = levenshtein(name, registry_name)
        max_len = max(len(name), len(registry_name))
        similarity = 1 - dist / max_len if max_len else 0.0
        best = max(best, similarity)
    return best


def check_inn(inn: str, company: str) -> dict:
    is_valid = validate_inn(inn)
    found_in_registry = inn in FNS_REGISTRY if is_valid else False
    similarity = fuzzy_search(company) if company else 0.0

    return {
        "inn_valid": int(is_valid),
        "found_in_registry": int(found_in_registry),
        "company_similarity": round(similarity, 3),
    }