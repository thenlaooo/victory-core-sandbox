from rapidfuzz import fuzz

class QuestEngine:
    RU_ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"

    @classmethod
    def encrypt_dispatch(cls, text: str, shift: int) -> str:
        """
        Шифрует штабную радиограмму сдвигом по алфавиту (Шифр Цезаря).
        Знаки препинания и пробелы остаются на месте.
        """
        encrypted_chars = []
        for char in text.upper():
            if char in cls.RU_ALPHABET:
                idx = cls.RU_ALPHABET.index(char)
                new_idx = (idx + shift) % len(cls.RU_ALPHABET)
                encrypted_chars.append(cls.RU_ALPHABET[new_idx])
            else:
                encrypted_chars.append(char)
        return "".join(encrypted_chars)

    @classmethod
    def decrypt_dispatch(cls, encrypted_text: str, shift: int) -> str:
        """Расшифровывает радиограмму обратным сдвигом."""
        return cls.encrypt_dispatch(encrypted_text, -shift)

    @staticmethod
    def verify_answer(user_input: str, original_dispatch: str, threshold: float = 85.0) -> dict[str, any]:
        """
        Проверяет правильность ответа пользователя.
        Устойчив к регистру, знакам препинания и мелким опечаткам.
        """
        # Убираем знаки препинания, оставляем только буквы и цифры
        clean_user = "".join(ch for ch in user_input.lower() if ch.isalnum())
        clean_orig = "".join(ch for ch in original_dispatch.lower() if ch.isalnum())

        if not clean_user:
            return {
                "success": False,
                "score": 0.0,
                "message": "Ответ пуст. Попробуйте расшифровать радиограмму!"
            }

        # Сравниваем сходство ответа с оригиналом
        similarity = fuzz.ratio(clean_user, clean_orig)

        if similarity >= threshold:
            return {
                "success": True,
                "score": round(similarity, 1),
                "message": "Радиограмма расшифрована верно! Маршрут открыт.",
                "bonus_points": 50
            }
        else:
            return {
                "success": False,
                "score": round(similarity, 1),
                "message": "Сообщение расшифровано неточно. Проверьте ключ шифра на стеле!"
            }


# --- ТЕСТ КВЕСТ-ДВИЖКА ---
if __name__ == "__main__":
    # Секретный приказ для точки «Оборонительный рубеж»
    original_text = "ЗДЕСЬ ДЕРЖАЛА ОБОРОНУ ДЕВЯТАЯ БРИГАДА"
    key_shift = 5  # Номер 5-го десантного корпуса

    # 1. Генерируем шифровку для экрана приложения
    cipher_text = QuestEngine.encrypt_dispatch(original_text, key_shift)
    print("Зашифрованная радиограмма на экране:")
    print(cipher_text)
    print("-" * 50)

    # 2. Пользователь ввел ответ с мелкой опечаткой (пропустил букву)
    child_answer = "Здесь держала оборону девятая бригад"
    
    result = QuestEngine.verify_answer(child_answer, original_text)
    print(f"Ответ ребенка: '{child_answer}'")
    print(f"Результат: {result['message']}")
    print(f"Сходство: {result['score']}% | Успех: {result['success']}")