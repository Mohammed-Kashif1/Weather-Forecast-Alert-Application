from src.weather_service import get_weather

def test_simulation_returns_expected_structure():
    data = get_weather("Test City", "simulation")
    assert data["city"] == "Test City"
    assert "temperature" in data["current"]
    assert len(data["forecast"]) > 0
