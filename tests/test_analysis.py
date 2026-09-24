import pandas as pd
from src.analysis import forecast_to_dataframe, calculate_summary, get_hottest_forecast

def test_forecast_dataframe_and_summary():
    data = {"forecast": [
        {"datetime": "2026-01-01T00:00:00+00:00", "temperature": 20, "humidity": 50},
        {"datetime": "2026-01-01T03:00:00+00:00", "temperature": 30, "humidity": 70},
    ]}
    df = forecast_to_dataframe(data)
    summary = calculate_summary(df)
    assert len(df) == 2
    assert summary["minimum_temperature"] == 20
    assert summary["maximum_temperature"] == 30
    assert get_hottest_forecast(df)["temperature"] == 30

def test_empty_summary():
    assert calculate_summary(pd.DataFrame()) == {"forecast_records": 0}
