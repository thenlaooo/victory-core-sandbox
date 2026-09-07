import re
from rapidfuzz import fuzz

DB_RECORDS = [
    {
        "id": 1,
        "fio": "Иванов Иван Иванович",
        "year": 1943,
        "location": "деревня Крупышино, Кромской район",
        "unit": "5-й воздушно-десантный корпус"
    },
    {
        "id": 2,
        "fio": "Смирнов Петр Сергеевич",
        "year": 1941,
        "location": "город Орел, оборонительный рубеж",
        "unit": "201-я воздушно-десантная бригада"
    },
    {
        "id": 3,
        "fio": "Иванников Илья Петрович",
        "year": 1943,
        "location": "село Семенково",
        "unit": "41-й стрелковый полк"
    }
]

def extract_year(text: str):
    """Находит первое 4-значное число, похожее на год войны (1941-1945)."""
    match = re.search(r'\b(194[1-5])\b', text)
    return int(match.group(1)) if match else None

def smart_similarity(query: str, record: dict) -> float:
    q_lower = query.lower()
    
    # 1. Проверяем год
    query_year = extract_year(query)
    year_bonus = 0.0
    if query_year:
        if query_year == record["year"]:
            year_bonus = 20.0  # Год совпал — солидный бонус
        else:
            year_bonus = -15.0 # Год не совпал — штраф (это другой бой/человек)

    # 2. Очищаем запрос от года, чтобы он не мешал сравнению слов
    clean_query = re.sub(r'\b194[1-5]\b', '', q_lower).strip()

    # 3. Считаем сходство по ФИО
    score_fio = fuzz.token_set_ratio(clean_query, record["fio"].lower())

    # 4. Считаем сходство по месту гибели/захоронения
    score_loc = fuzz.partial_ratio(clean_query, record["location"].lower())

    # Итоговый расчет с весами:
    # 50% ФИО + 30% локация + бонус/штраф за год
    base_score = (score_fio * 0.5) + (score_loc * 0.3)
    final_score = base_score + year_bonus

    # Ограничиваем диапазон от 0 до 100
    return max(0.0, min(100.0, round(final_score, 1)))

if __name__ == "__main__":
    test_query = "Ивонов Иван 1943 Крупышино"
    print(f"Запрос: {test_query}\n" + "-" * 40)
    
    for rec in DB_RECORDS:
        score = smart_similarity(test_query, rec)
        print(f"[{score}%] {rec['fio']} | Год: {rec['year']} | Место: {rec['location']}")