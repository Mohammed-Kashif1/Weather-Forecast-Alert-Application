"""Configurable weather alert generation."""
def generate_alerts(current, forecast_df, temp_threshold=35, humidity_threshold=85, rain_threshold=70):
    alerts = []
    def add(kind, message, when=None):
        alerts.append({"type": kind, "message": message, "time": str(when) if when is not None else None})
    temp = current.get("temperature")
    humidity = current.get("humidity")
    if temp is not None and float(temp) >= temp_threshold:
        add("High temperature", f"Current temperature {float(temp):.1f}°C meets/exceeds {temp_threshold:.1f}°C.")
    if humidity is not None and float(humidity) >= humidity_threshold:
        add("High humidity", f"Current humidity {float(humidity):.0f}% meets/exceeds {humidity_threshold:.0f}%.")
    if forecast_df is not None and not forecast_df.empty:
        for _, row in forecast_df.iterrows():
            when = row.get("datetime")
            t = row.get("temperature")
            h = row.get("humidity")
            rain = row.get("rain_probability")
            desc = str(row.get("description") or "").lower()
            if t is not None and t == t and float(t) >= temp_threshold:
                add("Forecast high temperature", f"Forecast temperature {float(t):.1f}°C meets/exceeds {temp_threshold:.1f}°C.", when)
            if h is not None and h == h and float(h) >= humidity_threshold:
                add("Forecast high humidity", f"Forecast humidity {float(h):.0f}% meets/exceeds {humidity_threshold:.0f}%.", when)
            if rain is not None and rain == rain and float(rain) >= rain_threshold:
                add("Rain probability", f"Rain probability {float(rain):.0f}% meets/exceeds {rain_threshold:.0f}%.", when)
            if any(word in desc for word in ("thunderstorm", "thunder")):
                add("Thunderstorm", f"Thunderstorm condition forecast: {desc}.", when)
    return alerts
