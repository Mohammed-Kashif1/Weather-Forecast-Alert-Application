"""Matplotlib charts for forecasts and history."""
import pandas as pd
import matplotlib.pyplot as plt

def create_forecast_chart(forecast_df):
    if forecast_df is None or forecast_df.empty or forecast_df["temperature"].dropna().empty:
        return None
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(forecast_df["datetime"], forecast_df["temperature"], marker="o", label="Temperature (°C)")
    ax.set_title("Forecast temperature")
    ax.set_xlabel("Date/time (UTC)")
    ax.set_ylabel("Temperature (°C)")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    return fig

def create_history_chart(history_df):
    if history_df is None or history_df.empty or "temperature" not in history_df:
        return None
    df = history_df.copy()
    df["recorded_at"] = pd.to_datetime(df["recorded_at"], errors="coerce", utc=True)
    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
    df = df.dropna(subset=["recorded_at", "temperature"]).sort_values("recorded_at")
    if df.empty:
        return None
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["recorded_at"], df["temperature"], marker=".", label="Recorded temperature")
    ax.set_title("Saved temperature history")
    ax.set_xlabel("Recorded at (UTC)")
    ax.set_ylabel("Temperature (°C)")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    return fig
