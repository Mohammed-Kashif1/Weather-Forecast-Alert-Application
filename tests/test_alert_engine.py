import pandas as pd
from src.alert_engine import generate_alerts

def test_current_and_forecast_alerts():
    current = {"temperature": 38, "humidity": 90}
    forecast = pd.DataFrame([{
        "datetime": "2026-01-01T00:00:00Z", "temperature": 36,
        "humidity": 80, "rain_probability": 80, "description": "thunderstorm"
    }])
    alerts = generate_alerts(current, forecast, 35, 85, 70)
    types = {a["type"] for a in alerts}
    assert "High temperature" in types
    assert "High humidity" in types
    assert "Rain probability" in types
    assert "Thunderstorm" in types
