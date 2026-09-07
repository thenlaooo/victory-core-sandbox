from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_healthcheck():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_fuzzy_search_success():
    response = client.post(
        "/api/v1/search/soldier",
        json={"query": "Ивонов Иван 1943 Крупышино", "threshold": 50}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] > 0
    assert data["results"][0]["confidence"] >= 70.0
    assert data["results"][0]["soldier"]["last_name"] == "Иванов"

def test_quest_flow():
    # 1. Получение квеста
    task_res = client.get("/api/v1/quest/1")
    assert task_res.status_code == 200
    assert "encrypted_dispatch" in task_res.json()

    # 2. Успешная валидация с опечаткой
    verify_res = client.post(
        "/api/v1/quest/verify",
        json={"point_id": 1, "user_answer": "Здесь держала оборону девятая бригад"}
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["success"] is True

def test_mock_endpoints():
    # Проверка маршрута для Егора
    route_res = client.post("/api/v1/routes/build", json={"start_lat": 52.965, "start_lon": 36.068})
    assert route_res.status_code == 200
    assert route_res.json()["geojson"]["type"] == "FeatureCollection"

    # Проверка отчета для Кирилла
    battle_res = client.post("/api/v1/last-battle", json={
        "lat": 52.684,
        "lon": 35.762,
        "soldier_name": "Красноармеец Иванов",
        "death_circumstances": "Крупышино"
    })
    assert battle_res.status_code == 201
    assert battle_res.json()["notification_sent"] is True

if __name__ == "__main__":
    test_healthcheck()
    test_fuzzy_search_success()
    test_quest_flow()
    test_mock_endpoints()
    print("\n ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО (API ГОТОВО К СДАЧЕ)")