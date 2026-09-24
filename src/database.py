"""SQLite persistence for weather snapshots and alert events."""
import json
import sqlite3
from datetime import datetime, timezone
from .config import DATABASE_PATH

def _connect():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    with _connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS weather_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, city TEXT NOT NULL, mode TEXT NOT NULL,
            recorded_at TEXT NOT NULL, temperature REAL, feels_like REAL, humidity REAL,
            description TEXT, wind_speed REAL, payload_json TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS alert_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, city TEXT NOT NULL, recorded_at TEXT NOT NULL,
            alert_type TEXT, message TEXT, event_time TEXT
        )""")

def save_weather(city, mode, current):
    with _connect() as conn:
        conn.execute("""INSERT INTO weather_history
            (city, mode, recorded_at, temperature, feels_like, humidity, description, wind_speed, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (city, mode, datetime.now(timezone.utc).isoformat(),
             current.get("temperature"), current.get("feels_like"), current.get("humidity"),
             current.get("description"), current.get("wind_speed"), json.dumps(current, default=str)))

def save_alerts(city, alerts):
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.executemany("""INSERT INTO alert_history
            (city, recorded_at, alert_type, message, event_time) VALUES (?, ?, ?, ?, ?)""",
            [(city, now, a.get("type"), a.get("message"), a.get("time")) for a in alerts])

def get_weather_history(city=None, limit=500):
    query = "SELECT * FROM weather_history"
    params = []
    if city:
        query += " WHERE lower(city)=lower(?)"
        params.append(city)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(int(limit))
    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    import pandas as pd
    return pd.DataFrame([dict(r) for r in rows])

def get_alert_history(city=None, limit=500):
    query = "SELECT * FROM alert_history"
    params = []
    if city:
        query += " WHERE lower(city)=lower(?)"
        params.append(city)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(int(limit))
    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    import pandas as pd
    return pd.DataFrame([dict(r) for r in rows])

def clear_weather_history(city):
    with _connect() as conn:
        cur = conn.execute("DELETE FROM weather_history WHERE lower(city)=lower(?)", (city,))
        return cur.rowcount

def clear_alert_history(city):
    with _connect() as conn:
        cur = conn.execute("DELETE FROM alert_history WHERE lower(city)=lower(?)", (city,))
        return cur.rowcount
