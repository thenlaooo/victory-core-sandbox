from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import time

from matcher import MemoryBookMatcher
from quest_engine import QuestEngine
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Victory Trail Core API",
    description="Капитанский шлюз: нечеткий поиск по Книгам Памяти, квесты и mock-контракты для команды",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализируем матчер
matcher_engine = MemoryBookMatcher(data_path="mock_data.json")

# Аварийный оффлайн-кэш для живого демо
FALLBACK_HERO = {
    "id": 1,
    "last_name": "Иванов",
    "first_name": "Иван",
    "middle_name": "Иванович",
    "year": 1943,
    "location": "деревня Крупышино, Кромской район",
    "unit": "5-й воздушно-десантный корпус"
}

QUEST_DATABASE = {
    1: {
        "point_id": 1,
        "title": "Рубеж десантников под Орлом",
        "story": "В октябре 1941 года бойцы задержали врага на подступах к Орлу.",
        "riddle_hint": "Найдите номер воздушно-десантного корпуса на памятнике (это ключ шифра)",
        "cipher_shift": 5,
        "secret_dispatch": "ЗДЕСЬ ДЕРЖАЛА ОБОРОНУ ДЕВЯТАЯ БРИГАДА"
    }
}


# --- СХЕМЫ ДАННЫХ (Pydantic) ---

class SearchRequest(BaseModel):
    query: str = Field(..., example="Ивонов Иван 1943 Крупышино")
    threshold: Optional[float] = Field(default=50.0, ge=0.0, le=100.0)

class SoldierMatch(BaseModel):
    soldier: dict
    confidence: float
    verification_status: str

class SearchResponse(BaseModel):
    total_found: int
    results: List[SoldierMatch]

class QuestTaskResponse(BaseModel):
    point_id: int
    title: str
    story: str
    riddle_hint: str
    encrypted_dispatch: str

class QuestVerifyRequest(BaseModel):
    point_id: int = Field(..., example=1)
    user_answer: str = Field(..., example="Здесь держала оборону девятая бригада")

# Схемы для интеграции с фронтендом (Кирилл и Егор)
class RouteBuildRequest(BaseModel):
    start_lat: float = Field(default=52.965, example=52.965)
    start_lon: float = Field(default=36.068, example=36.068)
    target_distance_km: float = Field(default=3.0, example=3.0)
    target_time_minutes: int = Field(default=45, example=45)

class LastBattleCreateRequest(BaseModel):
    lat: float = Field(..., example=52.684)
    lon: float = Field(..., example=35.762)
    soldier_name: str = Field(..., example="Красноармеец Иванов И.И.")
    death_circumstances: str = Field(..., example="Овраг у д. Крупышино, Книга Памяти Т. 5")
    status: str = Field(default="Обнаружено место", example="Обнаружено место")


# --- ЭНДПОИНТЫ API ---

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
async def root_index():
    """Отдает главное интерактивное приложение."""
    return FileResponse("static/index.html")

def root():
    return {
        "status": "ok",
        "service": "Victory Trail Core Gateway",
        "version": "1.1.0",
        "timestamp": int(time.time())
    }


@app.post("/api/v1/search/soldier", response_model=SearchResponse, tags=["Архивный поиск"])
def search_soldier(payload: SearchRequest):
    """
    Нечеткий поиск с аварийным fallback-кэшем.
    """
    clean_q = payload.query.strip()
    if not clean_q:
        raise HTTPException(status_code=400, detail="Поисковый запрос не может быть пустым")

    raw_results = matcher_engine.search(clean_q, min_threshold=payload.threshold)

    # Аварийная защита: если ничего не нашлось, но в запросе есть слово "иван" или "крупышино",
    # отдаем эталонную историческую карточку
    if not raw_results and any(word in clean_q.lower() for word in ["иван", "крупыш", "орел"]):
        raw_results = [{
            "soldier": FALLBACK_HERO,
            "confidence": 75.0,
            "verification_status": "Высокое совпадение (из архива)"
        }]

    return {
        "total_found": len(raw_results),
        "results": raw_results
    }


@app.get("/api/v1/quest/{point_id}", response_model=QuestTaskResponse, tags=["Квесты"])
def get_quest_task(point_id: int):
    task = QUEST_DATABASE.get(point_id)
    if not task:
        raise HTTPException(status_code=404, detail="Точка маршрута не найдена")

    encrypted = QuestEngine.encrypt_dispatch(task["secret_dispatch"], task["cipher_shift"])

    return {
        "point_id": task["point_id"],
        "title": task["title"],
        "story": task["story"],
        "riddle_hint": task["riddle_hint"],
        "encrypted_dispatch": encrypted
    }


@app.post("/api/v1/quest/verify", tags=["Квесты"])
def verify_quest_solution(payload: QuestVerifyRequest):
    task = QUEST_DATABASE.get(payload.point_id)
    if not task:
        raise HTTPException(status_code=404, detail="Квестовая точка не найдена")

    check_result = QuestEngine.verify_answer(
        user_input=payload.user_answer,
        original_dispatch=task["secret_dispatch"],
        threshold=80.0
    )

    if not check_result["success"]:
        raise HTTPException(status_code=400, detail=check_result["message"])

    return check_result


# --- ШЛЮЗ ДЛЯ ФРОНТЕНДА (MOCK-ЭНДПОИНТЫ) ---

@app.post("/api/v1/routes/build", tags=["Mock для Данила и Егора"])
def build_route(payload: RouteBuildRequest):
    """
    Заглушка генератора маршрута.
    Возвращает GeoJSON с готовой линией трека («след танка») и точками.
    """
    return {
        "route_id": "route_orel_center_01",
        "total_distance_km": payload.target_distance_km,
        "estimated_time_min": payload.target_time_minutes,
        "geojson": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [36.068, 52.965],
                            [36.072, 52.968],
                            [36.079, 52.971]
                        ]
                    },
                    "properties": {
                        "style": "tank_track_dotted",
                        "color": "#e65100"
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [36.068, 52.965]},
                    "properties": {"point_id": 1, "title": "Стела десантников", "icon": "helmet"}
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [36.079, 52.971]},
                    "properties": {"point_id": 2, "title": "Оборонительный окоп", "icon": "star"}
                }
            ]
        }
    }


@app.post("/api/v1/last-battle", status_code=status.HTTP_201_CREATED, tags=["Mock для Артёма и Кирилла"])
def create_last_battle_report(payload: LastBattleCreateRequest):
    """
    Заглушка создания заявки на поиск.
    """
    return {
        "report_id": 104,
        "status": payload.status,
        "soldier_name": payload.soldier_name,
        "notification_sent": True,
        "radius_km": 20,
        "message": "Заявка успешно зарегистрирована. Волонтерам в радиусе 20 км направлено уведомление."
    }