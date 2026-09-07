import json
import re
from typing import List, Dict, Any, Optional
from rapidfuzz import fuzz

class MemoryBookMatcher:
    def __init__(self, data_path: Optional[str] = None, records: Optional[List[Dict[str, Any]]] = None):
        """
        Инициализация базы. Данные можно загрузить из JSON-файла 
        или передать напрямую списком.
        """
        if data_path:
            with open(data_path, "r", encoding="utf-8") as f:
                self.records = json.load(f)
        elif records is not None:
            self.records = records
        else:
            self.records = []

    @staticmethod
    def _extract_year(text: str) -> Optional[int]:
        """Извлекает 4-значный год войны (1941-1945)."""
        match = re.search(r'\b(194[1-5])\b', text)
        return int(match.group(1)) if match else None

    def _calculate_score(self, query: str, record: Dict[str, Any]) -> float:
        q_lower = query.lower()
        
        # 1. Год
        query_year = self._extract_year(query)
        year_bonus = 0.0
        if query_year:
            if query_year == record.get("year"):
                year_bonus = 20.0
            else:
                year_bonus = -15.0

        # Очистка запроса от года
        clean_query = re.sub(r'\b194[1-5]\b', '', q_lower).strip()

        # 2. ФИО
        fio = f"{record.get('last_name', '')} {record.get('first_name', '')} {record.get('middle_name', '')}".strip().lower()
        score_fio = fuzz.token_set_ratio(clean_query, fio)

        # 3. Локация
        location = record.get("location", "").lower()
        score_loc = fuzz.partial_ratio(clean_query, location)

        # Базовый расчет
        base_score = (score_fio * 0.5) + (score_loc * 0.3)
        final_score = base_score + year_bonus

        return max(0.0, min(100.0, round(final_score, 1)))

    def search(self, query: str, min_threshold: float = 50.0, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Основной метод поиска. Возвращает подходящие записи со статусом верификации.
        """
        results = []

        for rec in self.records:
            score = self._calculate_score(query, rec)

            if score >= min_threshold:
                # Определяем статус для фронтенда и краеведов
                if score >= 70.0:
                    status = "Высокое совпадение"
                else:
                    status = "Требуется верификация краеведом"

                results.append({
                    "soldier": rec,
                    "confidence": score,
                    "verification_status": status
                })

        # Сортировка по убыванию релевантности
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results[:limit]


# --- ПРОВЕРКА РАБОТЫ КЛАССА ---
if __name__ == "__main__":
    # Создаем экземпляр матчера, загружая данные из файла
    engine = MemoryBookMatcher(data_path="mock_data.json")

    # Тест 1: Неточный поисковый запрос
    query_1 = "Ивонов Иван 1943 Крупышино"
    print(f"Поиск по запросу: '{query_1}'\n")
    
    matches = engine.search(query_1)
    
    for m in matches:
        soldier = m["soldier"]
        print(f"[{m['confidence']}%] {soldier['last_name']} {soldier['first_name']} {soldier['middle_name']}")
        print(f"       Год: {soldier['year']} | Место: {soldier['location']}")
        print(f"       Статус: {m['verification_status']}\n")