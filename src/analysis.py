"""Forecast normalization and summary statistics."""
import pandas as pd

FORECAST_COLUMNS = [
    "datetime", "temperature", "feels_like", "humidity",
    "description", "wind_speed", "rain_probability", "rain_mm"
]

def forecast_to_dataframe(weather_data):
    records = weather_data.get("forecast", [])
    df = pd.DataFrame(records)
    for column in FORECAST_COLUMNS:
        if column not in df.columns:
            df[column] = None
    df = df[FORECAST_COLUMNS].copy()
    if not df.empty:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce", utc=True)
        for column in ("temperature", "feels_like", "humidity", "wind_speed", "rain_probability", "rain_mm"):
            df[column] = pd.to_numeric(df[column], errors="coerce")
        df = df.sort_values("datetime").reset_index(drop=True)
    return df

def calculate_summary(forecast_df):
    if forecast_df is None or forecast_df.empty:
        return {"forecast_records": 0}
    def val(col, method):
        series = pd.to_numeric(forecast_df[col], errors="coerce").dropna()
        return float(getattr(series, method)()) if not series.empty else None
    return {
        "forecast_records": int(len(forecast_df)),
        "minimum_temperature": val("temperature", "min"),
        "maximum_temperature": val("temperature", "max"),
        "average_temperature": val("temperature", "mean"),
        "average_humidity": val("humidity", "mean"),
        "maximum_rain_probability": val("rain_probability", "max"),
        "total_forecast_rain_mm": val("rain_mm", "sum"),
    }

def get_hottest_forecast(forecast_df):
    if forecast_df is None or forecast_df.empty or forecast_df["temperature"].dropna().empty:
        return None
    return forecast_df.loc[forecast_df["temperature"].idxmax()].to_dict()
