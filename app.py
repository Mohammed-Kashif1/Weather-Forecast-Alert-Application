"""Streamlit dashboard for the modular Weather Forecast & Alert Application."""
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.config import DEFAULT_TEMP_THRESHOLD, DEFAULT_HUMIDITY_THRESHOLD, DEFAULT_RAIN_THRESHOLD
from src.weather_service import get_weather, WeatherError
from src.analysis import forecast_to_dataframe, calculate_summary
from src.alert_engine import generate_alerts
from src.database import initialize_database, save_weather, save_alerts, get_weather_history, get_alert_history, clear_weather_history, clear_alert_history
from src.reports import generate_reports
from src.visualization import create_forecast_chart, create_history_chart
from src.notifications import send_email_alerts, email_is_configured, NotificationError

st.set_page_config(page_title="Weather Forecast & Alerts", page_icon="🌦️", layout="wide")
initialize_database()

def fetch_and_process(city, mode, temp_threshold, humidity_threshold, rain_threshold):
    weather = get_weather(city, mode)
    forecast = forecast_to_dataframe(weather)
    alerts = generate_alerts(weather["current"], forecast, temp_threshold, humidity_threshold, rain_threshold)
    save_weather(weather["city"], mode, weather["current"])
    save_alerts(weather["city"], alerts)
    reports = generate_reports(weather, forecast, alerts, mode)
    return {"weather": weather, "forecast": forecast, "alerts": alerts, "summary": calculate_summary(forecast), "reports": reports}

st.sidebar.title("⚙️ Settings")
mode = st.sidebar.selectbox("Data source", ["simulation", "api"], format_func=lambda x: "🧪 Simulation" if x == "simulation" else "🌐 Live API")
city = st.sidebar.text_input("City", "Mumbai").strip()
temp_threshold = st.sidebar.number_input("High temperature threshold (°C)", -50.0, 70.0, float(DEFAULT_TEMP_THRESHOLD), 1.0)
humidity_threshold = st.sidebar.slider("High humidity threshold (%)", 0, 100, int(DEFAULT_HUMIDITY_THRESHOLD))
rain_threshold = st.sidebar.slider("Rain probability threshold (%)", 0, 100, int(DEFAULT_RAIN_THRESHOLD))
fetch = st.sidebar.button("🌦️ Fetch weather", type="primary", use_container_width=True)

st.title("🌦️ Weather Forecast & Alert Application")
st.caption("Weather monitoring, configurable alerts, forecast analytics, and local history.")
if mode == "simulation":
    st.info("Simulation mode uses sample data; it is not a live forecast.")

if fetch:
    if not city:
        st.error("Please enter a city.")
    else:
        try:
            with st.spinner(f"Fetching weather for {city}..."):
                st.session_state["result"] = fetch_and_process(city, mode, temp_threshold, humidity_threshold, rain_threshold)
            st.success("Weather data loaded.")
        except (WeatherError, OSError, ValueError, KeyError) as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Unexpected error: {exc}")

result = st.session_state.get("result")
if not result:
    st.info("Choose a city and click **Fetch weather** to begin.")
    st.stop()

weather, forecast, alerts, summary, reports = result["weather"], result["forecast"], result["alerts"], result["summary"], result["reports"]
st.subheader(f"📍 {weather['city']}" + (f", {weather['country']}" if weather.get("country") else ""))
st.caption(f"Source: {mode} | Forecast times are shown in UTC.")

st.subheader("🌡️ Current conditions")
current = weather["current"]
cols = st.columns(4)
for col, label, key, suffix in zip(cols, ["Temperature", "Feels like", "Humidity", "Wind speed"], ["temperature", "feels_like", "humidity", "wind_speed"], ["°C", "°C", "%", " m/s"]):
    value = current.get(key)
    col.metric(label, "N/A" if value is None else f"{float(value):.1f}{suffix}")
st.write(f"**Condition:** {str(current.get('description', 'Unknown')).title()}")

st.divider()
st.subheader("📊 Forecast summary")
if summary.get("forecast_records", 0):
    cols = st.columns(4)
    metrics = [
        ("Forecast records", summary.get("forecast_records"), ""),
        ("Minimum temperature", summary.get("minimum_temperature"), "°C"),
        ("Maximum temperature", summary.get("maximum_temperature"), "°C"),
        ("Average humidity", summary.get("average_humidity"), "%"),
    ]
    for col, (label, value, suffix) in zip(cols, metrics):
        col.metric(label, "N/A" if value is None else f"{value:.1f}{suffix}" if isinstance(value, (int, float)) else str(value))
    st.write(f"Maximum rain probability: **{summary.get('maximum_rain_probability', 'N/A')}%** | Total forecast rain: **{summary.get('total_forecast_rain_mm', 'N/A')} mm**")
else:
    st.info("No forecast summary available.")

st.divider()
st.subheader("📅 Forecast details")
st.dataframe(forecast, use_container_width=True, hide_index=True)
fig = create_forecast_chart(forecast)
if fig is not None:
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

st.divider()
st.subheader("🚨 Weather alerts")
if alerts:
    st.warning(f"{len(alerts)} alert event(s) generated.")
    for alert in alerts:
        with st.container(border=True):
            st.markdown(f"**{alert['type']}**")
            st.write(alert["message"])
            if alert.get("time"):
                st.caption(f"Forecast time: {alert['time']}")
else:
    st.success("No configured weather alerts were triggered.")

st.divider()
st.subheader("📁 Reports")
download_cols = st.columns(3)
for col, key, label, mime in zip(download_cols, ["csv", "json", "alerts"], ["Forecast CSV", "JSON report", "Alert text"], ["text/csv", "application/json", "text/plain"]):
    path = Path(reports[key])
    col.download_button(f"⬇️ {label}", path.read_bytes(), file_name=path.name, mime=mime, use_container_width=True)

st.divider()
st.subheader("📧 Email alerts")
if not email_is_configured():
    st.info("Email is optional. Configure SMTP values in .env to enable it.")
elif alerts and st.button("Send current alerts by email"):
    try:
        send_email_alerts(weather["city"], alerts)
        st.success("Email sent.")
    except NotificationError as exc:
        st.error(str(exc))

st.divider()
st.subheader("🗄️ Saved history")
history = get_weather_history(weather["city"], 500)
if history.empty:
    st.info("No weather history saved yet.")
else:
    st.dataframe(history, use_container_width=True, hide_index=True)
    fig = create_history_chart(history)
    if fig is not None:
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    st.download_button("Download weather history CSV", history.to_csv(index=False).encode(), file_name=f"{weather['city']}_history.csv", mime="text/csv")
alerts_history = get_alert_history(weather["city"], 500)
with st.expander("Alert history"):
    st.dataframe(alerts_history, use_container_width=True, hide_index=True)
with st.expander("⚠️ Clear saved history"):
    confirm = st.checkbox(f"Confirm deletion for {weather['city']}")
    if st.button("Delete city history", disabled=not confirm):
        clear_weather_history(weather["city"])
        clear_alert_history(weather["city"])
        st.success("History deleted.")
        st.rerun()

st.divider()
