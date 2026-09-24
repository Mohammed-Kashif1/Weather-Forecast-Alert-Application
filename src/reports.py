"""Generate CSV, JSON, and plain-text weather reports."""
import json
from datetime import datetime
from pathlib import Path
from .config import OUTPUT_DIR

def generate_reports(weather_data, forecast_df, alerts, mode):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    city = "".join(c if c.isalnum() or c in "-_" else "_" for c in weather_data.get("city", "city"))
    base = OUTPUT_DIR / f"{city}_{stamp}"
    csv_path = base.with_suffix(".csv")
    json_path = base.with_suffix(".json")
    alerts_path = OUTPUT_DIR / f"{city}_{stamp}_alerts.txt"
    forecast_df.to_csv(csv_path, index=False)
    payload = {"city": weather_data.get("city"), "country": weather_data.get("country"),
               "mode": mode, "current": weather_data.get("current"),
               "forecast": forecast_df.astype(object).where(forecast_df.notna(), None).to_dict(orient="records"),
               "alerts": alerts}
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    lines = [f"Weather alerts for {weather_data.get('city')}", ""]
    lines += [f"- {a.get('type')}: {a.get('message')} (time: {a.get('time') or 'current'})" for a in alerts]
    if not alerts:
        lines.append("No configured alerts were triggered.")
    alerts_path.write_text("\n".join(lines), encoding="utf-8")
    return {"csv": csv_path, "json": json_path, "alerts": alerts_path}
