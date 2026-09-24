"""Standalone APScheduler worker for periodic weather checks."""
import argparse
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.config import ROOT_DIR, OUTPUT_DIR, DEFAULT_TEMP_THRESHOLD, DEFAULT_HUMIDITY_THRESHOLD, DEFAULT_RAIN_THRESHOLD
from src.weather_service import get_weather, WeatherError
from src.analysis import forecast_to_dataframe, calculate_summary
from src.alert_engine import generate_alerts
from src.database import initialize_database, save_weather, save_alerts
from src.reports import generate_reports
from src.notifications import send_email_alerts, email_is_configured, NotificationError

load_dotenv(ROOT_DIR / ".env")
LOG_PATH = OUTPUT_DIR / "scheduler.log"

def configure_logging():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(LOG_PATH, encoding="utf-8")],
        force=True,
    )

logger = logging.getLogger("weather_scheduler")

def run_weather_check(city, mode, temp_threshold, humidity_threshold, rain_threshold, send_email=False):
    logger.info("Starting check: city=%s mode=%s", city, mode)
    try:
        weather = get_weather(city, mode)
        forecast = forecast_to_dataframe(weather)
        alerts = generate_alerts(weather["current"], forecast, temp_threshold, humidity_threshold, rain_threshold)
        save_weather(weather["city"], mode, weather["current"])
        save_alerts(weather["city"], alerts)
        paths = generate_reports(weather, forecast, alerts, mode)
        logger.info("Summary: %s", calculate_summary(forecast))
        if alerts:
            for alert in alerts:
                logger.warning("ALERT | %s | %s", alert["type"], alert["message"])
        else:
            logger.info("No configured alerts triggered.")
        logger.info("Reports: %s", paths)
        if send_email and alerts:
            if not email_is_configured():
                logger.error("Email requested but SMTP configuration is incomplete.")
            else:
                try:
                    send_email_alerts(weather["city"], alerts)
                    logger.info("Alert email sent.")
                except NotificationError as exc:
                    logger.error("Email failed: %s", exc)
        return True
    except (WeatherError, OSError, ValueError, KeyError, TypeError):
        logger.exception("Weather check failed.")
        return False
    except Exception:
        logger.exception("Unexpected weather check failure.")
        return False

def parse_args():
    parser = argparse.ArgumentParser(description="Scheduled Weather Forecast & Alert Application")
    parser.add_argument("--city", default="Mumbai")
    parser.add_argument("--mode", choices=["simulation", "api"], default="simulation")
    parser.add_argument("--interval", type=int, default=60, help="Interval in minutes")
    parser.add_argument("--temp-threshold", type=float, default=DEFAULT_TEMP_THRESHOLD)
    parser.add_argument("--humidity-threshold", type=float, default=DEFAULT_HUMIDITY_THRESHOLD)
    parser.add_argument("--rain-threshold", type=float, default=DEFAULT_RAIN_THRESHOLD)
    parser.add_argument("--email", action="store_true", help="Send alert emails if configured")
    parser.add_argument("--run-once", action="store_true", help="Run one check and exit")
    return parser.parse_args()

def main():
    configure_logging()
    args = parse_args()
    if not args.city.strip():
        raise SystemExit("--city cannot be empty")
    if args.interval < 1:
        raise SystemExit("--interval must be >= 1 minute")
    if not -50 <= args.temp_threshold <= 70:
        raise SystemExit("--temp-threshold must be between -50 and 70")
    if not 0 <= args.humidity_threshold <= 100:
        raise SystemExit("--humidity-threshold must be between 0 and 100")
    if not 0 <= args.rain_threshold <= 100:
        raise SystemExit("--rain-threshold must be between 0 and 100")

    initialize_database()
    kwargs = dict(
        city=args.city.strip(), mode=args.mode,
        temp_threshold=args.temp_threshold,
        humidity_threshold=args.humidity_threshold,
        rain_threshold=args.rain_threshold,
        send_email=args.email,
    )
    if args.run_once:
        if not run_weather_check(**kwargs):
            raise SystemExit(1)
        return

    scheduler = BlockingScheduler(job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 300})
    scheduler.add_job(run_weather_check, IntervalTrigger(minutes=args.interval), kwargs=kwargs,
                      id="weather_monitor", name=f"Weather monitor: {args.city}", replace_existing=True)
    logger.info("Running initial check.")
    run_weather_check(**kwargs)
    logger.info("Scheduler active; checks every %s minute(s). Press Ctrl+C to stop.", args.interval)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
        if scheduler.running:
            scheduler.shutdown(wait=False)

if __name__ == "__main__":
    main()
