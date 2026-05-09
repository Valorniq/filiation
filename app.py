from __future__ import annotations

import calendar
import datetime as dt
import hashlib
import hmac
import html
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_env_file(Path(".env"))
load_env_file(Path(".env.local"))


APP_NAME = "Filiation"
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "3000"))
SECRET = os.environ.get("FILIATION_SECRET", "local-filiation-dev-secret").encode()
DATA_DIR = Path(os.environ.get("FILIATION_DATA_DIR", "data"))
USERS_FILE = DATA_DIR / "users.json"
API_TIMEOUT = float(os.environ.get("FILIATION_API_TIMEOUT", "8"))


class IntegrationError(Exception):
    pass


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def money(value: Any) -> str:
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0
    return f"${amount:,.2f}"


def pct(value: float, total: float) -> float:
    return 0 if total == 0 else max(0, min(100, value / total * 100))


def read_json_file(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return fallback


def write_json_file(path: Path, data: Any) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True))


def load_users() -> dict[str, dict[str, str]]:
    return read_json_file(USERS_FILE, {})


def save_users(users: dict[str, dict[str, str]]) -> None:
    write_json_file(USERS_FILE, users)


def user_id_for(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()[:16]


def default_profile(email: str, display_name: str = "") -> dict[str, str]:
    name = display_name or email.split("@")[0].replace(".", " ").title() or "Family Member"
    return {
        "uid": user_id_for(email),
        "email": email,
        "displayName": name,
        "photoURL": "",
        "familyCode": "",
        "birthday": "",
        "bio": "",
        "phoneNumber": "",
    }


def sign_cookie(uid: str) -> str:
    signature = hmac.new(SECRET, uid.encode(), hashlib.sha256).hexdigest()
    return f"{uid}.{signature}"


def verify_cookie(cookie_value: str | None) -> str | None:
    if not cookie_value or "." not in cookie_value:
        return None
    uid, signature = cookie_value.rsplit(".", 1)
    expected = hmac.new(SECRET, uid.encode(), hashlib.sha256).hexdigest()
    return uid if hmac.compare_digest(signature, expected) else None


def read_form(handler: BaseHTTPRequestHandler) -> dict[str, str]:
    length = int(handler.headers.get("Content-Length", "0"))
    body = handler.rfile.read(length).decode()
    return {key: values[0] for key, values in parse_qs(body).items()}


def parse_cookies(cookie_header: str | None) -> dict[str, str]:
    cookies: dict[str, str] = {}
    if not cookie_header:
        return cookies
    for part in cookie_header.split(";"):
        if "=" in part:
            key, value = part.strip().split("=", 1)
            cookies[key] = value
    return cookies


def http_json(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
) -> Any:
    body = None
    request_headers = {
        "Accept": "application/json",
        "User-Agent": "Filiation/1.0 (local integration client)",
        **(headers or {}),
    }
    if payload is not None:
        body = json.dumps(payload).encode()
        request_headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=request_headers, method=method)
    try:
        with urlopen(request, timeout=API_TIMEOUT) as response:
            return json.loads(response.read().decode() or "{}")
    except HTTPError as error:
        detail = error.read().decode(errors="replace")[:500]
        raise IntegrationError(f"{error.code} from {url}: {detail}") from error
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise IntegrationError(str(error)) from error


def integration_card(name: str, connected: bool, detail: str, error: str = "") -> str:
    status = "Connected" if connected and not error else "Error" if error else "Not configured"
    status_class = "success" if connected and not error else "danger" if error else ""
    message = error or detail
    return f"""
    <div class="integration-card">
      <div class="split"><strong>{esc(name)}</strong><span class="status {status_class}">{esc(status)}</span></div>
      <p>{esc(message)}</p>
    </div>
    """


def empty_state(title: str, detail: str, env_vars: list[str]) -> str:
    pills = "".join(f"<code>{esc(var)}</code>" for var in env_vars)
    return f"""
    <div class="empty-state">
      <h3>{esc(title)}</h3>
      <p>{esc(detail)}</p>
      <div class="env-pills">{pills}</div>
    </div>
    """


def card(content: str, class_name: str = "") -> str:
    return f'<section class="card {class_name}">{content}</section>'


def profile_image(profile: dict[str, str]) -> str:
    src = profile.get("photoURL", "")
    if src:
        return f'<img src="{esc(src)}" alt="Avatar">'
    initial = "".join(part[0] for part in profile.get("displayName", "F").split()[:2]).upper() or "F"
    return f'<span class="avatar-fallback">{esc(initial)}</span>'


def month_window() -> tuple[dt.date, dt.date]:
    today = dt.date.today()
    first = today.replace(day=1)
    last = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    return first, last


def iso_datetime(day: dt.date, end: bool = False) -> str:
    time = "23:59:59Z" if end else "00:00:00Z"
    return f"{day.isoformat()}T{time}"


def get_plaid() -> dict[str, Any]:
    client_id = env("PLAID_CLIENT_ID")
    secret = env("PLAID_SECRET")
    access_token = env("PLAID_ACCESS_TOKEN")
    if not (client_id and secret and access_token):
        return {"connected": False, "accounts": [], "transactions": [], "error": ""}

    plaid_env = env("PLAID_ENV", "sandbox").lower()
    hosts = {
        "sandbox": "https://sandbox.plaid.com",
        "development": "https://development.plaid.com",
        "production": "https://production.plaid.com",
    }
    host = hosts.get(plaid_env, hosts["sandbox"])
    base_payload = {"client_id": client_id, "secret": secret, "access_token": access_token}
    try:
        accounts_response = http_json(f"{host}/accounts/balance/get", "POST", payload=base_payload)
        tx_payload = {**base_payload, "count": int(env("PLAID_TRANSACTION_COUNT", "50"))}
        tx_response = http_json(f"{host}/transactions/sync", "POST", payload=tx_payload)
    except IntegrationError as error:
        return {"connected": True, "accounts": [], "transactions": [], "error": str(error)}
    return {
        "connected": True,
        "accounts": accounts_response.get("accounts", []),
        "transactions": tx_response.get("added", []),
        "error": "",
    }


def get_calendar_events() -> dict[str, Any]:
    calendar_id = env("GOOGLE_CALENDAR_ID", "primary")
    token = env("GOOGLE_CALENDAR_ACCESS_TOKEN")
    api_key = env("GOOGLE_CALENDAR_API_KEY")
    if not (token or api_key):
        return {"connected": False, "events": [], "error": ""}

    first, last = month_window()
    params = {
        "singleEvents": "true",
        "orderBy": "startTime",
        "timeMin": iso_datetime(first),
        "timeMax": iso_datetime(last, end=True),
    }
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if api_key:
        params["key"] = api_key
    url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events?{urlencode(params)}"
    try:
        response = http_json(url, headers=headers)
    except IntegrationError as error:
        return {"connected": True, "events": [], "error": str(error)}
    return {"connected": True, "events": response.get("items", []), "error": ""}


def get_generic_endpoint(name: str, url_var: str, token_var: str = "") -> dict[str, Any]:
    url = env(url_var)
    token = env(token_var) if token_var else ""
    if not url:
        return {"connected": False, "items": [], "error": ""}
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = http_json(url, headers=headers)
    except IntegrationError as error:
        return {"connected": True, "items": [], "error": f"{name}: {error}"}
    if isinstance(response, list):
        items = response
    else:
        items = response.get("items") or response.get("data") or response.get("results") or []
    return {"connected": True, "items": items if isinstance(items, list) else [], "error": ""}


def get_weather() -> dict[str, Any]:
    lat = env("FILIATION_LAT")
    lon = env("FILIATION_LON")
    if not (lat and lon):
        return {"connected": False, "period": None, "error": ""}
    try:
        points = http_json(f"https://api.weather.gov/points/{lat},{lon}")
        forecast_url = points.get("properties", {}).get("forecast")
        if not forecast_url:
            raise IntegrationError("National Weather Service did not return a forecast URL.")
        forecast = http_json(forecast_url)
    except IntegrationError as error:
        return {"connected": True, "period": None, "error": str(error)}
    periods = forecast.get("properties", {}).get("periods", [])
    return {"connected": True, "period": periods[0] if periods else None, "error": ""}


def all_integrations() -> dict[str, Any]:
    return {
        "plaid": get_plaid(),
        "calendar": get_calendar_events(),
        "school": get_generic_endpoint("School", "SCHOOL_EVENTS_URL", "SCHOOL_API_TOKEN"),
        "health": get_generic_endpoint("Health", "HEALTH_EVENTS_URL", "HEALTH_API_TOKEN"),
        "logistics": get_generic_endpoint("Logistics", "LOGISTICS_EVENTS_URL", "LOGISTICS_API_TOKEN"),
        "p2p": get_generic_endpoint("P2P", "P2P_REQUESTS_URL", "P2P_API_TOKEN"),
        "family": get_generic_endpoint("Family", "FAMILY_MEMBERS_URL", "FAMILY_API_TOKEN"),
        "weather": get_weather(),
    }


def finance_summary(plaid: dict[str, Any]) -> dict[str, Any]:
    accounts = plaid.get("accounts", [])
    transactions = plaid.get("transactions", [])
    liquidity = 0.0
    for account in accounts:
        balances = account.get("balances", {})
        liquidity += float(balances.get("current") or balances.get("available") or 0)

    income = 0.0
    expenses = 0.0
    categories: dict[str, float] = {}
    for tx in transactions:
        amount = float(tx.get("amount") or 0)
        category = (
            tx.get("personal_finance_category", {}).get("primary")
            or (tx.get("category") or ["Uncategorized"])[0]
            or "Uncategorized"
        )
        if amount < 0:
            income += abs(amount)
        else:
            expenses += amount
            categories[category] = categories.get(category, 0) + amount
    return {
        "liquidity": liquidity,
        "income": income,
        "expenses": expenses,
        "categories": categories,
        "accounts": accounts,
        "transactions": transactions,
    }


def event_start(event: dict[str, Any]) -> str:
    start = event.get("start", {})
    return start.get("dateTime") or start.get("date") or ""


def event_day(event: dict[str, Any]) -> int | None:
    raw = event_start(event)
    if not raw:
        return None
    try:
        return dt.date.fromisoformat(raw[:10]).day
    except ValueError:
        return None


def item_text(item: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        value = item.get(key)
        if value is not None:
            return str(value)
    return default


def layout(title: str, body: str, profile: dict[str, str] | None = None, active: str = "") -> str:
    if profile is None:
        return document(title, body)

    first_name = profile.get("displayName", "Member").split()[0]
    nav = [
        ("/", "Home", "H"),
        ("/calendar", "Calendar", "C"),
        ("/finance", "Finance", "F"),
        ("/logistics", "Logistics", "L"),
        ("/sync", "Sync", "S"),
        ("/settings", "Settings", "G"),
    ]
    links = "\n".join(
        f'<a class="nav-item {"active" if path == active else ""}" href="{path}"><span>{icon}</span>{label}</a>'
        for path, label, icon in nav
    )
    family = get_generic_endpoint("Family", "FAMILY_MEMBERS_URL", "FAMILY_API_TOKEN")
    family_count = len(family.get("items", [])) if family.get("connected") and not family.get("error") else 0
    chat_content = (
        empty_state("Family chat not connected", "Set FAMILY_MEMBERS_URL or wire a messaging endpoint to populate this panel.", ["FAMILY_MEMBERS_URL"])
        if family_count == 0
        else f'<p class="muted-copy">{family_count} family profiles connected.</p>'
    )
    shell = f"""
    <div class="app-shell">
      <aside class="sidebar">
        <a class="brand" href="/"><span class="brand-mark">R</span><strong>{APP_NAME}</strong></a>
        <nav class="nav-list">{links}</nav>
        <form action="/logout" method="post"><button class="nav-item danger" type="submit"><span>O</span>Logout</button></form>
        <div class="family-pill"><strong>{family_count} connected family profiles</strong></div>
      </aside>
      <main class="main">
        <header class="topbar">
          <div class="user-chip">
            {profile_image(profile)}
            <div><strong>Good morning, {esc(first_name)}</strong><small>API integrations live when configured</small></div>
          </div>
          <a class="button primary small" href="/sync">Integration Status</a>
        </header>
        <div class="content">{body}</div>
      </main>
      <aside class="chat">
        <div class="chat-head"><strong>Family Panel</strong><span></span></div>
        {chat_content}
      </aside>
      <nav class="mobile-nav">{links}</nav>
    </div>
    """
    return document(title, shell)


def document(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} | {APP_NAME}</title>
  <style>{CSS}</style>
</head>
<body>{body}<script>{JS}</script></body>
</html>"""


def auth_page(mode: str = "login") -> str:
    is_register = mode == "register"
    heading = "Connect your family's real systems." if is_register else "Access your integration hub."
    subcopy = "Create a local admin profile, then connect provider APIs through environment variables."
    action = "Create Identity" if is_register else "Access Hub"
    button = "Sign Up" if is_register else "Sign In"
    body = f"""
    <main class="auth-page">
      <section class="auth-copy">
        <a class="brand" href="/auth"><span class="brand-mark">R</span><strong>{APP_NAME}</strong></a>
        <h1>{heading}</h1>
        <p>{subcopy}</p>
        <div class="feature-row"><span>Plaid</span><span>Google Calendar</span><span>School APIs</span><span>Weather.gov</span></div>
      </section>
      <section class="auth-card">
        <div class="mode-tabs"><a class="{"active" if not is_register else ""}" href="/auth">Login</a><a class="{"active" if is_register else ""}" href="/auth?mode=register">Register</a></div>
        <div class="auth-grid">
          <form method="post" action="/login" class="form-stack">
            <input type="hidden" name="mode" value="{esc(mode)}">
            <h2>{action}</h2>
            <p class="muted-copy">This local account protects the dashboard. Provider credentials stay in server-side environment variables.</p>
            <label>Email Address<input name="email" type="email" placeholder="admin@example.com" required></label>
            <label>Display Name<input name="displayName" placeholder="Admin"></label>
            <button class="button primary" type="submit">{button}</button>
          </form>
          <div class="onboarding">
            <h2>Connect APIs</h2>
            <p>Use the environment variables in the README to enable live data. Until then, pages show empty states.</p>
            <div class="env-pills"><code>PLAID_ACCESS_TOKEN</code><code>GOOGLE_CALENDAR_ACCESS_TOKEN</code><code>SCHOOL_EVENTS_URL</code></div>
          </div>
        </div>
      </section>
    </main>
    """
    return document("Authentication", body)


def home_page(profile: dict[str, str]) -> str:
    first_name = profile.get("displayName", "Family").split()[0]
    integrations = all_integrations()
    summary = finance_summary(integrations["plaid"])
    events = integrations["calendar"].get("events", [])
    school_items = integrations["school"].get("items", [])
    logistics_items = integrations["logistics"].get("items", [])
    weather = integrations["weather"]

    focus = events[:1] or school_items[:1] or logistics_items[:1]
    if focus:
        item = focus[0]
        title = item_text(item, "summary", "title", "name", "subject", default="Connected item")
        detail = item_text(item, "description", "body", "note", "status", default="Pulled from a configured provider.")
        focus_card = f'<span class="eyebrow">Live Focus</span><h2>{esc(title)}</h2><p>{esc(detail)}</p><div class="button-row"><a class="button light" href="/calendar">Open Calendar</a></div>'
    else:
        focus_card = empty_state(
            "No live focus item",
            "Connect Google Calendar, school, or logistics endpoints to populate the dashboard focus card.",
            ["GOOGLE_CALENDAR_ACCESS_TOKEN", "SCHOOL_EVENTS_URL", "LOGISTICS_EVENTS_URL"],
        )

    alerts = "".join(
        f'<div class="alert-row"><span class="round-icon">A</span><div><strong>{esc(item_text(item, "title", "summary", "name", default="Alert"))}</strong><small>{esc(item_text(item, "description", "status", "note", default="No detail supplied"))}</small></div></div>'
        for item in (school_items + logistics_items)[:4]
    ) or empty_state("No live alerts", "Configure school or logistics APIs to show operational alerts.", ["SCHOOL_EVENTS_URL", "LOGISTICS_EVENTS_URL"])

    if weather.get("period"):
        period = weather["period"]
        weather_html = f'<div class="weather">{esc(period.get("temperature"))} {esc(period.get("temperatureUnit"))}</div><p>{esc(period.get("shortForecast"))}</p>'
    else:
        weather_html = empty_state("Weather not connected", "Set coordinates to use the National Weather Service API.", ["FILIATION_LAT", "FILIATION_LON"])

    connected_count = sum(1 for data in integrations.values() if data.get("connected") and not data.get("error"))
    body = f"""
    <header class="page-title"><h1>Good morning, {esc(first_name)}.</h1><p>Live data appears only from configured API integrations.</p></header>
    <div class="dashboard-grid">
      {card(focus_card, 'hero span-3')}
      {card(f'<div class="split"><span class="round-icon">W</span><span class="status {"success" if integrations["plaid"].get("connected") and not integrations["plaid"].get("error") else ""}">Plaid</span></div><h3>Liquidity</h3><p class="metric">{money(summary["liquidity"])}</p><hr><div class="split"><small>Expenses</small><strong>{money(summary["expenses"])}</strong></div>')}
      {card('<h3>Logistics & Alerts</h3>' + alerts, 'span-2')}
      {card(weather_html, 'center')}
      {card(f'<h3>API Status</h3><div class="sync-cloud">{connected_count}/{len(integrations)}</div><a class="button muted" href="/sync">Manage</a>', 'center')}
    </div>
    """
    return layout("Home", body, profile, "/")


def finance_page(profile: dict[str, str]) -> str:
    plaid = get_plaid()
    summary = finance_summary(plaid)
    categories = summary["categories"]
    total_category = sum(categories.values())
    slices = "".join(
        f'<li><span style="width:{pct(value, total_category):.1f}%"></span><div>{esc(name)}<strong>{money(value)}</strong></div></li>'
        for name, value in sorted(categories.items(), key=lambda item: item[1], reverse=True)
    ) or empty_state("No transaction categories", "Connect Plaid and sync transactions to build the burn profile.", ["PLAID_CLIENT_ID", "PLAID_SECRET", "PLAID_ACCESS_TOKEN"])
    transactions = "".join(
        f'<div class="list-row"><div><strong>{esc(tx.get("name", "Transaction"))}</strong><small>{esc(tx.get("date", ""))}</small></div><div class="amount">{money(tx.get("amount"))}</div></div>'
        for tx in summary["transactions"][:12]
    ) or empty_state("No transactions", "Plaid returned no transactions or is not configured.", ["PLAID_ACCESS_TOKEN"])
    accounts = "".join(
        f'<div class="vault"><small>{esc(account.get("official_name") or account.get("subtype") or "Account")}</small><strong>{esc(account.get("name", "Linked account"))}</strong><p>{money(account.get("balances", {}).get("current"))}</p><small>{esc(account.get("mask", ""))}</small></div>'
        for account in summary["accounts"]
    ) or empty_state("No linked accounts", "Create and supply a Plaid access token for a real institution or sandbox item.", ["PLAID_ACCESS_TOKEN"])

    body = f"""
    <header class="page-title row-title"><div><h1>Finance Center</h1><p>Backed by Plaid when credentials are configured.</p></div><a class="button primary" href="/sync">Connection Status</a></header>
    <div class="grid-12">
      {card(f'<span class="eyebrow">Collective Liquidity</span><p class="big-number">{money(summary["liquidity"])}</p><div class="stats"><span>Income <b>{money(summary["income"])}</b></span><span>Expenses <b>{money(summary["expenses"])}</b></span><span>Linked Accounts <b>{len(summary["accounts"])}</b></span></div>{integration_card("Plaid", plaid.get("connected", False), "Configured via Plaid API.", plaid.get("error", ""))}', 'col-8')}
      {card('<h3>Burn Profile</h3><ul class="bar-list">' + slices + '</ul>', 'col-4')}
      {card('<div class="split"><h3>Sync Feed</h3><span class="status">Live</span></div>' + transactions, 'col-8')}
      {card('<h3>External Vaults</h3>' + accounts, 'col-4')}
    </div>
    """
    return layout("Finance", body, profile, "/finance")


def logistics_page(profile: dict[str, str]) -> str:
    school = get_generic_endpoint("School", "SCHOOL_EVENTS_URL", "SCHOOL_API_TOKEN")
    health = get_generic_endpoint("Health", "HEALTH_EVENTS_URL", "HEALTH_API_TOKEN")
    logistics = get_generic_endpoint("Logistics", "LOGISTICS_EVENTS_URL", "LOGISTICS_API_TOKEN")
    school_items = school.get("items", [])
    logistics_items = logistics.get("items", [])

    timeline = "".join(
        f'<div class="timeline-item"><span></span><div><small>{esc(item_text(item, "source", "type", default="API"))}</small><h3>{esc(item_text(item, "title", "summary", "name", default="School item"))}</h3><p>{esc(item_text(item, "description", "status", "note", default="No detail supplied"))}</p></div></div>'
        for item in school_items[:10]
    ) or empty_state("No school operations", "Point SCHOOL_EVENTS_URL at a JSON endpoint returning items/data/results.", ["SCHOOL_EVENTS_URL", "SCHOOL_API_TOKEN"])
    health_items = "".join(
        f'<div class="info-box"><strong>{esc(item_text(item, "title", "summary", "name", default="Health item"))}</strong><p>{esc(item_text(item, "description", "status", "note", default=""))}</p></div>'
        for item in health.get("items", [])[:5]
    ) or empty_state("No health data", "Configure a health endpoint to populate this panel.", ["HEALTH_EVENTS_URL"])
    logistic_cards = "".join(
        card(f'<small>{esc(item_text(item, "time", "date", "status", default="Live item"))}</small><h3>{esc(item_text(item, "title", "summary", "name", default="Logistics item"))}</h3><p>{esc(item_text(item, "description", "note", "location", default=""))}</p>', "mini-card")
        for item in logistics_items[:8]
    ) or empty_state("No daily logistics", "Connect a logistics JSON API endpoint.", ["LOGISTICS_EVENTS_URL"])

    body = f"""
    <header class="page-title"><h1>Logistics Hub</h1><p>School, health, and operations panels now read from configured APIs.</p></header>
    <div class="grid-12">
      {card(f'<div class="split"><h2>School Operations</h2><span class="status">Live API</span></div><div class="timeline">{timeline}</div>', 'col-8')}
      <div class="col-4 stack">
        {card('<h3>Health Status</h3>' + health_items)}
        {card(integration_card("School API", school.get("connected", False), "School endpoint configured.", school.get("error", "")) + integration_card("Logistics API", logistics.get("connected", False), "Logistics endpoint configured.", logistics.get("error", "")), 'dark')}
      </div>
      <section class="col-12"><div class="row-title"><div><h2>Daily Logistics</h2><p>Transport and coverage from your configured source.</p></div></div><div class="mini-grid">{logistic_cards}</div></section>
    </div>
    """
    return layout("Logistics", body, profile, "/logistics")


def calendar_page(profile: dict[str, str]) -> str:
    calendar_data = get_calendar_events()
    events = calendar_data.get("events", [])
    first, _ = month_window()
    days_in_month = calendar.monthrange(first.year, first.month)[1]
    offset = (first.weekday() + 1) % 7
    by_day: dict[int, list[dict[str, Any]]] = {}
    for event in events:
        day = event_day(event)
        if day:
            by_day.setdefault(day, []).append(event)

    cells = ['<div class="calendar-cell empty"></div>' for _ in range(offset)]
    today = dt.date.today()
    for day in range(1, days_in_month + 1):
        classes = "calendar-cell today" if first.year == today.year and first.month == today.month and day == today.day else "calendar-cell"
        event_labels = "".join(f'<small>{esc(event.get("summary", "Event"))}</small>' for event in by_day.get(day, [])[:2])
        cells.append(f'<div class="{classes}"><strong>{day}</strong>{event_labels}</div>')

    upcoming = "".join(
        card(f'<small>{esc(event_start(event))}</small><h3>{esc(event.get("summary", "Calendar event"))}</h3><p>{esc(event.get("location", ""))}</p>', "")
        for event in events[:4]
    ) or empty_state("No calendar events", "Connect Google Calendar to populate this month.", ["GOOGLE_CALENDAR_ACCESS_TOKEN", "GOOGLE_CALENDAR_API_KEY"])

    body = f"""
    <header class="page-title row-title"><div><h1>{esc(first.strftime("%B %Y"))}</h1><p>{len(events)} live events loaded</p></div>{integration_card("Google Calendar", calendar_data.get("connected", False), "Calendar API configured.", calendar_data.get("error", ""))}</header>
    <section class="calendar-grid">
      {"".join(f"<b>{day}</b>" for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"])}
      {"".join(cells)}
    </section>
    <section class="focus">
      <div class="split"><h2>Upcoming Events</h2><span class="status">Live</span></div>
      <div class="grid-12"><div class="col-12 mini-grid">{upcoming}</div></div>
    </section>
    """
    return layout("Calendar", body, profile, "/calendar")


def sync_page(profile: dict[str, str]) -> str:
    integrations = all_integrations()
    cards = "".join(
        integration_card(label, data.get("connected", False), detail, data.get("error", ""))
        for label, detail, data in [
            ("Plaid", "Bank balances and transactions.", integrations["plaid"]),
            ("Google Calendar", "Family calendar events.", integrations["calendar"]),
            ("School", "School operations endpoint.", integrations["school"]),
            ("Health", "Health events endpoint.", integrations["health"]),
            ("Logistics", "Daily logistics endpoint.", integrations["logistics"]),
            ("P2P", "Request relay endpoint.", integrations["p2p"]),
            ("Family", "Family member directory endpoint.", integrations["family"]),
            ("Weather.gov", "National Weather Service forecast.", integrations["weather"]),
        ]
    )
    p2p_items = integrations["p2p"].get("items", [])
    requests = "".join(
        f'<div class="list-row"><div class="request-icon">R</div><div><strong>{esc(item_text(req, "from", "sender", "name", default="Request"))}</strong><small>{esc(item_text(req, "note", "description", "status", default=""))}</small></div><div><strong>{esc(item_text(req, "amount", "value", default=""))}</strong></div></div>'
        for req in p2p_items[:10]
    ) or empty_state("No P2P requests", "Connect P2P_REQUESTS_URL to display request relay items.", ["P2P_REQUESTS_URL"])
    connected_count = sum(1 for data in integrations.values() if data.get("connected") and not data.get("error"))

    body = f"""
    <header class="page-title row-title"><div><h1>Sync Engine</h1><p>API connection health and live request relay.</p></div><button id="syncButton" class="button primary">Refresh Page Data</button></header>
    <div class="grid-12">
      {card(f'<h2>Integration Health</h2><div class="node-grid"><span>Connected <b>{connected_count}</b><small>of {len(integrations)}</small></span><span>Data Source <b>API</b><small>No demo records</small></span><span>Storage <b>Local</b><small>Profiles only</small></span></div>', 'dark col-8')}
      {card('<h3>Configured Providers</h3>' + cards, 'col-4')}
      {card('<div class="split"><h2>P2P Request Relay</h2><span class="status">Live API</span></div>' + requests, 'col-12')}
    </div>
    """
    return layout("Sync", body, profile, "/sync")


def settings_page(profile: dict[str, str], saved: bool = False) -> str:
    notice = '<div class="success-inline">Profile saved.</div>' if saved else ""
    body = f"""
    <header class="page-title"><h1>Profile</h1><p>Local dashboard identity. API credentials are configured outside the app as environment variables.</p></header>
    <div class="grid-12 settings-grid">
      <aside class="col-4 stack">
        {card(f'<div class="profile-photo">{profile_image(profile)}</div><h2>{esc(profile.get("displayName"))}</h2><p>Local session account</p>')}
        {card('<h3>Push Alerts</h3><p>Browser notifications stay local to this device.</p><button id="notifyButton" class="button primary full">Setup Notifications</button>', 'dark')}
      </aside>
      <form class="col-8 card form-stack" method="post" action="/settings">
        <h2>Core Identity</h2>
        <div class="field-grid">
          <label>Display Name<input name="displayName" value="{esc(profile.get("displayName"))}"></label>
          <label>Email Address<input value="{esc(profile.get("email"))}" disabled></label>
          <label>Birthday<input name="birthday" type="date" value="{esc(profile.get("birthday"))}"></label>
          <label>Phone Number<input name="phoneNumber" value="{esc(profile.get("phoneNumber"))}" placeholder="+1 (555) 000-0000"></label>
        </div>
        <label>About Me<textarea name="bio" placeholder="Optional local profile note">{esc(profile.get("bio"))}</textarea></label>
        <label>Profile Image URL<input name="photoURL" value="{esc(profile.get("photoURL"))}" placeholder="https://..."></label>
        <div class="split">{notice}<button class="button primary" type="submit">Update Profile</button></div>
      </form>
    </div>
    """
    return layout("Settings", body, profile, "/settings")


CSS = r"""
:root{--primary:#4f46e5;--primary-2:#6366f1;--secondary:#10b981;--danger:#e11d48;--base:#f1f5f9;--low:#f8fafc;--ink:#0f172a}
*{box-sizing:border-box}body{margin:0;background:var(--base);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:inherit;text-decoration:none}button,input,textarea{font:inherit}button{cursor:pointer}code{background:#eef2ff;color:#4338ca;border-radius:.5rem;padding:.3rem .45rem;font-size:.72rem}
.app-shell{min-height:100vh;display:grid;grid-template-columns:16rem minmax(0,1fr)20rem}.sidebar,.chat,.topbar{background:white;border-color:#e2e8f0}.sidebar{position:sticky;top:0;height:100vh;padding:1.5rem;border-right:1px solid #e2e8f0}.brand{display:flex;align-items:center;gap:.75rem;margin-bottom:2rem;font-size:1.5rem}.brand-mark{display:grid;place-items:center;width:2.5rem;height:2.5rem;border-radius:.85rem;background:var(--primary);color:white;font-weight:900}.nav-list{display:flex;flex-direction:column;gap:.25rem}.nav-item{width:100%;border:0;background:transparent;display:flex;align-items:center;gap:.75rem;padding:.75rem 1rem;border-radius:.85rem;color:#475569;font-weight:800}.nav-item.active,.nav-item:hover{background:#eef2ff;color:var(--primary)}.nav-item.danger{color:var(--danger);margin-top:1rem}.family-pill{margin-top:2rem;padding:1rem;border-radius:1rem;background:#f8fafc;color:#64748b;font-size:.75rem}.main{min-width:0}.topbar{height:4rem;position:sticky;top:0;z-index:2;border-bottom:1px solid #e2e8f0;display:flex;align-items:center;justify-content:space-between;padding:0 2rem}.user-chip{display:flex;align-items:center;gap:.75rem}.user-chip img,.avatar-fallback{width:2.5rem;height:2.5rem;object-fit:cover;border-radius:999px}.avatar-fallback{display:grid;place-items:center;background:#eef2ff;color:var(--primary);font-weight:950}.user-chip small{display:block;color:var(--secondary);font-size:.65rem;text-transform:uppercase;font-weight:900;letter-spacing:.08em}.content{padding:2rem;max-width:88rem}.chat{position:sticky;top:0;height:100vh;border-left:1px solid #e2e8f0;padding:2rem;display:flex;flex-direction:column;gap:1rem}.chat-head{display:flex;justify-content:space-between}.chat-head span{width:.5rem;height:.5rem;background:var(--secondary);border-radius:999px}.mobile-nav{display:none}
.page-title{margin-bottom:2rem}.page-title h1{font-size:clamp(2.35rem,5vw,4rem);line-height:.96;margin:.2rem 0;font-weight:950;letter-spacing:0}.page-title p,.muted-copy{font-size:1.05rem;color:#64748b;font-weight:650}.row-title,.split{display:flex;align-items:center;justify-content:space-between;gap:1rem}.button-row{display:flex;gap:.75rem;flex-wrap:wrap}.button{border:0;border-radius:1rem;padding:.9rem 1.25rem;font-weight:900;transition:.2s;display:inline-block}.button.primary{background:var(--primary);color:white;box-shadow:0 12px 28px rgba(79,70,229,.22)}.button.light{background:white;color:var(--primary)}.button.ghost{background:rgba(255,255,255,.18);color:white}.button.muted{background:#f1f5f9;color:#64748b}.button.dark{background:#0f172a;color:white}.button.small{padding:.55rem .9rem;font-size:.8rem}.button.full{width:100%;text-align:center}.card{background:white;border:1px solid #e2e8f0;border-radius:1.5rem;padding:2rem;box-shadow:0 1px 3px rgba(15,23,42,.08)}.dashboard-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1.5rem}.grid-12{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:1.5rem}.span-3{grid-column:span 3}.span-2{grid-column:span 2}.col-4{grid-column:span 4}.col-8{grid-column:span 8}.col-12{grid-column:span 12}.stack{display:flex;flex-direction:column;gap:1.5rem}.hero{background:linear-gradient(135deg,var(--primary),var(--primary-2));color:white;min-height:18rem;display:flex;flex-direction:column;justify-content:space-between;overflow:hidden}.hero h2{font-size:clamp(2rem,4vw,3.25rem);line-height:1.05;margin:.75rem 0}.hero p{color:rgba(255,255,255,.76)}.eyebrow,.status{display:inline-block;border-radius:999px;background:rgba(79,70,229,.1);color:var(--primary);font-size:.65rem;text-transform:uppercase;letter-spacing:.14em;font-weight:950;padding:.4rem .7rem}.status.success{background:#ecfdf5;color:#059669}.status.danger{background:#fff1f2;color:var(--danger)}.hero .eyebrow{background:rgba(255,255,255,.2);color:white}.metric,.big-number{font-size:3.2rem;font-weight:950;margin:.6rem 0}.round-icon,.request-icon{display:grid;place-items:center;width:3rem;height:3rem;border-radius:1rem;background:#eef2ff;color:var(--primary);font-weight:950}.alert-row,.list-row{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:1rem;border-radius:1rem;background:#f8fafc;margin-top:.75rem}.alert-row small,.list-row small,.vault small,.mini-card small{display:block;color:#94a3b8;font-size:.7rem;text-transform:uppercase;font-weight:900;letter-spacing:.08em}.center{text-align:center}.weather,.sync-cloud{font-size:2.8rem;font-weight:950}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;border-top:1px solid #e2e8f0;margin-top:2rem;padding-top:2rem}.stats span{color:#94a3b8;text-transform:uppercase;font-size:.7rem;font-weight:900}.stats b{display:block;color:var(--ink);font-size:1.4rem;text-transform:none}.info-box,.success-box,.empty-state{padding:1rem;border-radius:1rem;background:#eef2ff;color:#4338ca;font-weight:750}.empty-state{background:#f8fafc;color:#64748b;border:1px dashed #cbd5e1}.empty-state h3{margin:.1rem 0;color:#334155}.env-pills{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.75rem}.integration-card{background:#f8fafc;border:1px solid #e2e8f0;border-radius:1rem;padding:1rem;margin:.75rem 0}.integration-card p{color:#64748b;font-size:.85rem;margin:.5rem 0 0}.vault{background:#f8fafc;border-radius:1rem;padding:1rem;margin-top:1rem}.vault p{font-size:1.4rem;font-weight:950;margin:.5rem 0}.dark{background:#0f172a;color:white}.dark p{color:rgba(255,255,255,.68)}.dark .integration-card{background:rgba(255,255,255,.08);border-color:rgba(255,255,255,.12)}.timeline-item{display:flex;gap:1rem;margin:1.25rem 0}.timeline-item>span{width:1rem;height:1rem;background:var(--primary);border-radius:999px;margin-top:.35rem;box-shadow:0 0 0 .25rem white}.timeline-item small{color:var(--primary);font-size:.7rem;text-transform:uppercase;font-weight:950;letter-spacing:.08em}.timeline-item h3{margin:.15rem 0}.timeline-item p{color:#64748b;margin:.25rem 0}.mini-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1rem}.mini-card{background:#f8fafc}.calendar-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:1rem;margin-bottom:2rem}.calendar-grid>b{text-align:center;color:#94a3b8;text-transform:uppercase;font-size:.7rem;letter-spacing:.16em}.calendar-cell{min-height:7rem;border-radius:1.2rem;background:white;border:1px solid #e2e8f0;padding:1rem}.calendar-cell.today{background:var(--primary);color:white}.calendar-cell.empty{background:rgba(248,250,252,.6);border:0}.calendar-cell small{display:block;margin-top:.6rem;color:#047857;background:#ecfdf5;border-radius:.5rem;padding:.25rem;font-size:.65rem;font-weight:900}.bar-list{list-style:none;padding:0;margin:1rem 0}.bar-list li{margin:.85rem 0}.bar-list span{display:block;height:.5rem;min-width:.3rem;background:var(--primary);border-radius:999px;margin-bottom:.35rem}.bar-list div{display:flex;justify-content:space-between;gap:.75rem;color:#64748b;font-weight:800}.node-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin:2rem 0}.node-grid span{color:rgba(255,255,255,.45);font-size:.7rem;text-transform:uppercase;font-weight:900}.node-grid b{display:block;color:white;font-size:2rem;text-transform:none}.node-grid small{display:block;color:#34d399}.profile-photo{display:grid;place-items:center}.profile-photo img,.profile-photo .avatar-fallback{width:8rem;height:8rem;border-radius:999px}.settings-grid label,.auth-card label{display:flex;flex-direction:column;gap:.45rem;color:#64748b;text-transform:uppercase;letter-spacing:.08em;font-size:.7rem;font-weight:950}.settings-grid input,.settings-grid textarea,.auth-card input{border:0;background:#f8fafc;border-radius:1rem;padding:1rem;color:var(--ink);text-transform:none;letter-spacing:0}.settings-grid textarea{min-height:8rem;resize:vertical}.field-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.success-inline{color:#059669;font-weight:900}.auth-page{min-height:100vh;display:grid;grid-template-columns:1fr 1.35fr;gap:4rem;align-items:center;padding:4rem;max-width:90rem;margin:auto}.auth-copy h1{font-size:clamp(3rem,7vw,5.4rem);line-height:.9;margin:3rem 0 1.5rem;font-weight:950}.auth-copy p{font-size:1.2rem;color:#64748b;max-width:34rem}.feature-row{display:flex;gap:1rem;flex-wrap:wrap;margin-top:3rem}.feature-row span{background:white;border-radius:1rem;padding:1rem;font-weight:900}.auth-card{background:white;border-radius:2rem;padding:2rem;box-shadow:0 12px 36px rgba(15,23,42,.1)}.mode-tabs{display:inline-flex;background:#f8fafc;border-radius:999px;padding:.35rem;margin-bottom:2rem}.mode-tabs a{padding:.8rem 2rem;border-radius:999px;font-weight:950;color:#94a3b8}.mode-tabs a.active{background:white;color:var(--primary);box-shadow:0 1px 3px rgba(15,23,42,.12)}.auth-grid{display:grid;grid-template-columns:1fr 1fr;gap:2rem}.form-stack{display:flex;flex-direction:column;gap:1rem}.onboarding{background:#f8fafc;border-radius:1.5rem;padding:1.5rem}
@media(max-width:1200px){.app-shell{grid-template-columns:16rem minmax(0,1fr)}.chat{display:none}.dashboard-grid{grid-template-columns:repeat(2,1fr)}.span-3,.span-2{grid-column:span 2}}@media(max-width:760px){.app-shell{display:block}.sidebar{display:none}.topbar{padding:0 1rem}.content{padding:1rem 1rem 6rem}.mobile-nav{display:flex;position:fixed;bottom:0;left:0;right:0;background:white;border-top:1px solid #e2e8f0;justify-content:space-around;padding:.5rem;z-index:5}.mobile-nav .nav-item{font-size:.7rem;flex-direction:column;gap:.2rem;padding:.45rem}.dashboard-grid,.grid-12,.auth-page,.auth-grid,.field-grid,.mini-grid{grid-template-columns:1fr}.col-4,.col-8,.col-12,.span-3,.span-2{grid-column:auto}.row-title,.split{align-items:flex-start;flex-direction:column}.calendar-grid{gap:.35rem}.calendar-cell{min-height:5rem;padding:.5rem;border-radius:.8rem}.auth-page{padding:1rem}.auth-copy h1{margin:1.5rem 0;font-size:3rem}.node-grid,.stats{grid-template-columns:1fr}}
"""


JS = r"""
const syncButton = document.getElementById("syncButton");
if (syncButton) {
  syncButton.addEventListener("click", () => {
    syncButton.disabled = true;
    syncButton.textContent = "Refreshing...";
    window.location.reload();
  });
}
const notifyButton = document.getElementById("notifyButton");
if (notifyButton) {
  notifyButton.addEventListener("click", async () => {
    if (!("Notification" in window)) {
      notifyButton.textContent = "Notifications Unsupported";
      return;
    }
    const permission = await Notification.requestPermission();
    notifyButton.textContent = permission === "granted" ? "Enabled on Device" : "Permission Denied";
    if (permission === "granted") {
      new Notification("Filiation notifications enabled", { body: "Browser alerts are now enabled for this device." });
    }
  });
}
"""


class FiliationHandler(BaseHTTPRequestHandler):
    def current_profile(self) -> dict[str, str] | None:
        cookies = parse_cookies(self.headers.get("Cookie"))
        uid = verify_cookie(cookies.get("filiation_session"))
        return load_users().get(uid) if uid else None

    def redirect(self, location: str, extra_headers: dict[str, str] | None = None) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", location)
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()

    def send_html(self, body: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def require_profile(self) -> dict[str, str] | None:
        profile = self.current_profile()
        if profile is None:
            self.redirect("/auth")
            return None
        return profile

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)

        if path == "/auth":
            self.send_html(auth_page(query.get("mode", ["login"])[0]))
            return

        profile = self.require_profile()
        if not profile:
            return

        routes = {
            "/": home_page,
            "/finance": finance_page,
            "/logistics": logistics_page,
            "/calendar": calendar_page,
            "/sync": sync_page,
            "/settings": settings_page,
        }
        page = routes.get(path)
        if not page:
            self.redirect("/")
            return
        self.send_html(page(profile))

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/login":
            data = read_form(self)
            email = data.get("email", "").strip().lower()
            if not email:
                self.redirect("/auth")
                return
            uid = user_id_for(email)
            users = load_users()
            if uid not in users:
                users[uid] = default_profile(email, data.get("displayName", ""))
            elif data.get("displayName"):
                users[uid]["displayName"] = data["displayName"]
            save_users(users)
            self.redirect("/", {"Set-Cookie": f"filiation_session={sign_cookie(uid)}; HttpOnly; SameSite=Lax; Path=/"})
            return

        if path == "/logout":
            self.redirect("/auth", {"Set-Cookie": "filiation_session=; Max-Age=0; Path=/"})
            return

        if path == "/settings":
            profile = self.require_profile()
            if not profile:
                return
            data = read_form(self)
            users = load_users()
            uid = profile["uid"]
            for key in ["displayName", "birthday", "bio", "phoneNumber", "photoURL"]:
                users[uid][key] = data.get(key, "")
            save_users(users)
            self.send_html(settings_page(users[uid], saved=True))
            return

        self.redirect("/")

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), FiliationHandler)
    print(f"{APP_NAME} Python app running at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
