# База данных: список бойцов из Книги Памяти Орловской области
# В реальной базе поля могут быть неполными или содержать сокращения
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

from rapidfuzz import fuzz

def calculate_similarity(user_query: str, record: dict) -> float:
    """
    Вычисляет общий процент сходства пользовательского запроса с записью в базе.
    """
    # 1. Приводим всё к нижнему регистру, чтобы не зависеть от CapsLock и регистра
    query = user_query.lower().strip()
    fio = record["fio"].lower()
    location = record["location"].lower()
    year = str(record["year"])

    # 2. Считаем сходство только по ФИО (главный критерий)
    # Используем token_set_ratio, чтобы перестановка "Иван Иванов" не снижала оценку
    score_fio = fuzz.token_set_ratio(query, fio)

    # 3. Формируем полную строку записи для контекстного поиска
    # Например: "иванов иван иванович 1943 деревня крупышино, кромской район"
    full_context = f"{fio} {year} {location}"
    score_full = fuzz.token_set_ratio(query, full_context)

    # 4. Взвешенная формула:
    # 60% веса отдаем совпадению по ФИО, 40% — общему совпадению (место, год, часть)
    total_score = (score_fio * 0.6) + (score_full * 0.4)

    return round(total_score, 1)

def search_in_records(user_query: str, threshold: float = 60.0):
    """
    Проходит по всей базе и возвращает подходящие записи, отсортированные по уверенности.
    """
    matched_results = []

    for record in DB_RECORDS:
        score = calculate_similarity(user_query, record)
        
        # Если оценка выше порога, добавляем запись в выдачу
        if score >= threshold:
            matched_results.append({
                "record": record,
                "confidence": score
            })

    # Сортируем: записи с максимальным процентом сходства идут первыми
    matched_results.sort(key=lambda x: x["confidence"], reverse=True)
    return matched_results


# --- ТЕСТОВЫЙ ЗАПУСК ---
if __name__ == "__main__":
    # Ситуация 1: Пользователь ввел фамилию с ошибкой, перепутал порядок слов и указал год
    test_query_1 = "Ивонов Иван 1943 Крупышино"
    print(f"Поисковый запрос: '{test_query_1}'")
    
    results = search_in_records(test_query_1)
    
    if not results:
        print("Ничего не найдено.")
    else:
        for item in results:
            rec = item["record"]
            conf = item["confidence"]
            print(f"-> Найдено: {rec['fio']} ({rec['year']}), Место: {rec['location']}")
            print(f"   Уверенность алгоритма: {conf}%\n")