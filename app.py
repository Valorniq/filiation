from __future__ import annotations

import hashlib
import hmac
import html
import json
import os
import secrets
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


APP_NAME = "Filiation"
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "3000"))
SECRET = os.environ.get("FILIATION_SECRET", "local-filiation-dev-secret").encode()
DATA_DIR = Path(os.environ.get("FILIATION_DATA_DIR", "data"))
USERS_FILE = DATA_DIR / "users.json"


FINANCE_CATEGORIES = [
    {"name": "Utilities", "value": 450, "color": "#6366f1"},
    {"name": "Subscriptions", "value": 120, "color": "#f59e0b"},
    {"name": "Food", "value": 800, "color": "#10b981"},
    {"name": "Entertainment", "value": 200, "color": "#ec4899"},
    {"name": "Taxes", "value": 1500, "color": "#f43f5e"},
    {"name": "Housing", "value": 2200, "color": "#8b5cf6"},
]

TRANSACTIONS = [
    {"name": "Whole Foods", "category": "Food", "amount": -142.50, "date": "Today, 2:45 PM", "status": "completed"},
    {"name": "Netflix", "category": "Subscriptions", "amount": -15.99, "date": "Yesterday", "status": "completed"},
    {"name": "IRS Quarterly", "category": "Taxes", "amount": -1500.00, "date": "Oct 24, 2023", "status": "pending"},
    {"name": "PGE Utilities", "category": "Utilities", "amount": -210.15, "date": "Oct 22, 2023", "status": "completed"},
]

LINKED_ACCOUNTS = [
    {"bank": "Chase Bank", "name": "Premium Checking", "balance": 12450.80, "last_sync": "10m ago"},
    {"bank": "American Express", "name": "Gold Card", "balance": -2140.12, "last_sync": "1h ago"},
]

P2P_REQUESTS = [
    {"type": "Financial", "from": "Maddie", "amount": "$25.00", "note": "Dinner sync"},
    {"type": "Logistics", "from": "Leo", "amount": "", "note": "Pick up at School"},
]


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def load_users() -> dict[str, dict[str, str]]:
    if not USERS_FILE.exists():
        return {}
    try:
        return json.loads(USERS_FILE.read_text())
    except json.JSONDecodeError:
        return {}


def save_users(users: dict[str, dict[str, str]]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    USERS_FILE.write_text(json.dumps(users, indent=2, sort_keys=True))


def user_id_for(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()[:16]


def default_profile(email: str, display_name: str = "") -> dict[str, str]:
    name = display_name or email.split("@")[0].replace(".", " ").title() or "Family Member"
    return {
        "uid": user_id_for(email),
        "email": email,
        "displayName": name,
        "photoURL": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&q=80&w=200",
        "familyCode": "F-294-88X",
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
    if hmac.compare_digest(signature, expected):
        return uid
    return None


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


def card(content: str, class_name: str = "") -> str:
    return f'<section class="card {class_name}">{content}</section>'


def initials(name: str) -> str:
    parts = [part[0] for part in name.split() if part]
    return "".join(parts[:2]).upper() or "F"


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
    shell = f"""
    <div class="app-shell">
      <aside class="sidebar">
        <a class="brand" href="/"><span class="brand-mark">R</span><strong>{APP_NAME}</strong></a>
        <nav class="nav-list">{links}</nav>
        <form action="/logout" method="post"><button class="nav-item danger" type="submit"><span>O</span>Logout</button></form>
        <div class="family-pill"><span class="avatar-stack"></span><strong>Family (5)</strong></div>
      </aside>
      <main class="main">
        <header class="topbar">
          <div class="user-chip">
            <img src="{esc(profile.get("photoURL"))}" alt="Avatar">
            <div><strong>Good morning, {esc(first_name)}</strong><small>Sanctuary Sync Active</small></div>
          </div>
          <button class="button primary small" type="button">Add Quick Event</button>
        </header>
        <div class="content">{body}</div>
      </main>
      <aside class="chat">
        <div class="chat-head"><strong>Family Chat</strong><span></span></div>
        <div class="bubble">Maya, Dad, pizza night tonight?<small>9:41 AM</small></div>
        <div class="bubble mine">Absolutely. 6pm!<small>10:02 AM</small></div>
        <div class="bubble">Sarah, Soccer practice at 5:30.<small>11:15 AM</small></div>
        <input class="chat-input" placeholder="Send message..." aria-label="Send message">
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
    heading = "Establish your family's encrypted hub." if is_register else "Secure your family's digital sanctuary."
    subcopy = (
        "Start your journey today. One click to secure shared visibility."
        if is_register
        else "Connect, sync, and protect your home with an encrypted collective hub."
    )
    switch_label = "Login" if is_register else "Register"
    switch_href = "/auth" if is_register else "/auth?mode=register"
    action = "Create Identity" if is_register else "Access Hub"
    button = "Sign Up" if is_register else "Sign In"
    body = f"""
    <main class="auth-page">
      <section class="auth-copy">
        <a class="brand" href="/auth"><span class="brand-mark">R</span><strong>{APP_NAME}</strong></a>
        <h1>{heading}</h1>
        <p>{subcopy}</p>
        <div class="feature-row"><span>End-to-End Encryption</span><span>Shared Legacy Hub</span></div>
      </section>
      <section class="auth-card">
        <div class="mode-tabs"><a class="{"active" if not is_register else ""}" href="/auth">Login</a><a class="{"active" if is_register else ""}" href="/auth?mode=register">Register</a></div>
        <div class="auth-grid">
          <form method="post" action="/login" class="form-stack">
            <input type="hidden" name="mode" value="{esc(mode)}">
            <h2>{action}</h2>
            <p class="muted">Enter a local profile to run the translated Python version.</p>
            <label>Email Address<input name="email" type="email" placeholder="sarah@filiation.com" required></label>
            <label>Display Name<input name="displayName" placeholder="Sarah Miller"></label>
            <button class="button primary" type="submit">{button}</button>
            <p class="notice">The original Firebase Google sign-in is represented here as local session auth so the Python app works without external services.</p>
          </form>
          <div class="onboarding">
            <h2>Onboarding</h2>
            <p>Syncing your presence.</p>
            <label>Join Family Code<input value="F-294-88X" readonly></label>
            <div class="info-box">Joining a family code automatically syncs your shared calendar and logistics hub.</div>
          </div>
        </div>
        <footer><span>(c) 2026 Filiation Systems. Locally Encrypted.</span><a href="{switch_href}">{switch_label}</a></footer>
      </section>
    </main>
    """
    return document("Authentication", body)


def home_page(profile: dict[str, str]) -> str:
    first_name = profile.get("displayName", "Family").split()[0]
    alerts = "".join(
        f'<div class="alert-row"><span class="round-icon">{icon}</span><div><strong>{title}</strong><small>{desc}</small></div><b>></b></div>'
        for icon, title, desc in [
            ("B", "Schoology update", "Math 101: New assignment posted"),
            ("A", "Infinite Campus alert", "Missing attendance: Period 4"),
        ]
    )
    body = f"""
    <header class="page-title"><h1>Good morning, {esc(first_name)}.</h1><p>Everything is in sync across the sanctuary.</p></header>
    <div class="dashboard-grid">
      {card('<span class="eyebrow">Active Focus</span><h2>School Deadline &<br>Health Checkup today</h2><div class="button-row"><button class="button light">View Schedule</button><button class="button ghost">Dismiss</button></div>', 'hero span-3')}
      {card('<div class="split"><span class="round-icon">W</span><span class="status">Live</span></div><h3>Burn Rate</h3><p class="metric">$142<small>/day</small></p><hr><div class="split"><small>P2P Request</small><strong class="green">+$45.00</strong></div>')}
      {card('<h3>Logistics & Alerts</h3>' + alerts, 'span-2')}
      {card('<div class="weather">72 deg</div><p>Perfect day for a family walk</p>', 'center')}
      {card('<h3>Cloud Status</h3><div class="sync-cloud">100%</div><button class="button muted">Manage Storage</button>', 'center')}
    </div>
    """
    return layout("Home", body, profile, "/")


def finance_page(profile: dict[str, str]) -> str:
    slices = "".join(
        f'<li><span style="background:{item["color"]}"></span>{item["name"]}<strong>${item["value"]}</strong></li>'
        for item in FINANCE_CATEGORIES
    )
    transactions = "".join(
        f'<div class="list-row"><div><strong>{t["name"]}</strong><small>{t["category"]} - {t["date"]}</small></div><div class="amount">{"+" if t["amount"] > 0 else ""}{t["amount"]:.2f}<small>{t["status"]}</small></div></div>'
        for t in TRANSACTIONS
    )
    accounts = "".join(
        f'<div class="vault"><small>{a["bank"]}</small><strong>{a["name"]}</strong><p>${a["balance"]:,.2f}</p><small>Synced {a["last_sync"]}</small></div>'
        for a in LINKED_ACCOUNTS
    )
    body = f"""
    <header class="page-title row-title"><div><h1>Finance Center</h1><p>Holistic view of your family's economic sanctuary.</p></div><div class="button-row"><button class="button light">Link Bank</button><button class="button primary">Request Funds</button></div></header>
    <div class="grid-12">
      {card('<span class="eyebrow">Collective Liquidity</span><p class="big-number">$42,892.20</p><div class="stats"><span>Income <b>$12,400</b></span><span>Expenses <b>$5,270</b></span><span>Synced Banks <b>4 Institutions</b></span></div><div class="info-box">Vault Encryption Active - External API Keys localized</div>', 'col-8')}
      {card('<h3>Burn Profile</h3><div class="donut"></div><ul class="legend">' + slices + '</ul>', 'col-4')}
      {card('<div class="split"><h3>Sync Feed</h3><a>View Ledger</a></div>' + transactions, 'col-8')}
      {card('<h3>External Vaults</h3>' + accounts + '<button class="button muted full">Expand Sanctuary</button>', 'col-4')}
    </div>
    """
    return layout("Finance", body, profile, "/finance")


def logistics_page(profile: dict[str, str]) -> str:
    timeline = "".join(
        f'<div class="timeline-item"><span></span><div><small>{status}</small><h3>{title}</h3><p>{desc}</p>{actions}</div></div>'
        for status, title, desc, actions in [
            ("Infinite Campus - Now", "Quarter 3 Progress Report Available", "Grade updates for Leo and Maya are now visible in the portal.", '<div class="button-row"><button class="button primary small">Sign Portal</button><button class="button muted small">Details</button></div>'),
            ("Schoology - 2h ago", "Missing Assignment: AP History", "Maya has an overdue project: Industrial Revolution Analysis.", ""),
            ("Calendar - Tomorrow", "Early Dismissal: Faculty Planning", "Both schools dismissing at 12:30 PM. Activities are cancelled.", ""),
        ]
    )
    logistics = "".join(
        f'{card(f"<small>{label}</small><h3>{title}</h3><p>{status}</p>", "mini-card")}'
        for label, title, status in [
            ("Leo - 3:30 PM", "Bus Route #14", "On Schedule"),
            ("Maya - 5:15 PM", "Dad Pick-up", "Soccer Field 3"),
            ("Groceries - Pending", "Target Drive-up", "Expires in 2h"),
            ("Create", "New Logistic Item", "Add coverage"),
        ]
    )
    body = f"""
    <header class="page-title"><h1>Logistics Hub</h1><p>Centralized command for school, health, and family operations.</p></header>
    <div class="grid-12">
      {card('<div class="split"><h2>School Operations</h2><span class="status">2 New Alerts</span></div><div class="timeline">' + timeline + '</div>', 'col-8')}
      <div class="col-4 stack">
        {card('<h3>Health Status</h3><div class="info-box">Leo: Tdap booster due by Sep 1st</div><div class="success-box">Maya: Approved for Soccer Season</div>')}
        {card('<h3>Security Hub</h3><p>Manage emergency contacts and child location permissions.</p><button class="button light full">Audit Permissions</button>', 'dark')}
      </div>
      <section class="col-12"><div class="row-title"><div><h2>Daily Logistics</h2><p>Transport and after-school coverage for today.</p></div></div><div class="mini-grid">' + logistics + '</div></section>
    </div>
    """
    return layout("Logistics", body, profile, "/logistics")


def calendar_page(profile: dict[str, str]) -> str:
    offset = 2
    cells = ['<div class="calendar-cell empty"></div>' for _ in range(offset)]
    for day in range(1, 32):
        classes = "calendar-cell today" if day == 3 else "calendar-cell"
        dots = ("<span></span>" if day % 4 == 0 else "") + ("<span class='green-dot'></span>" if day % 7 == 0 else "")
        event = "<small>Soccer Practice</small>" if day == 5 else ""
        cells.append(f'<div class="{classes}"><strong>{day}</strong><div class="dots">{dots}</div>{event}</div>')
    body = f"""
    <header class="page-title row-title"><div><h1>October 2024</h1><p>3 events scheduled for today</p></div><div class="filters"><span>All Members</span><span>Sarah</span><span>David</span><span>Leo</span></div></header>
    <section class="calendar-grid">
      {"".join(f"<b>{day}</b>" for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"])}
      {"".join(cells)}
    </section>
    <section class="focus">
      <div class="split"><h2>Today's Focus</h2><a>View All</a></div>
      <div class="grid-12">
        {card('<span class="eyebrow">Urgent</span><h2>School Fundraising Gala</h2><p>The annual primary school event starts at 6:30 PM. Everyone needs to be dressed and ready by 6:00 PM.</p><strong>Whole Family Attending</strong>', 'hero col-8')}
        <div class="col-4 stack">
          {card('<small>6:00 AM</small><h3>Leo Meal Prep</h3><p>Dairy-free lunchbox for trip</p><span class="status">Completed</span>')}
          {card('<small>4:00 PM</small><h3>Grocery Run</h3><p>Pickup Sarah medicine</p><button class="button muted full">Mark as Done</button>')}
        </div>
      </div>
    </section>
    """
    return layout("Calendar", body, profile, "/calendar")


def sync_page(profile: dict[str, str]) -> str:
    requests = "".join(
        f'<div class="list-row"><div class="request-icon">{req["type"][0]}</div><div><strong>{req["from"]}</strong><small>{req["note"]}</small></div><div><strong>{req["amount"]}</strong><button class="button dark small">Settle</button></div></div>'
        for req in P2P_REQUESTS
    )
    body = f"""
    <header class="page-title row-title"><div><h1>Sync Engine</h1><p>Global family presence & P2P relay.</p></div><button id="syncButton" class="button primary">Manual Sanctuary Sync</button></header>
    <div class="grid-12">
      {card('<h2>Live Sanctuary Map</h2><div class="node-grid"><span>Active Nodes <b>3</b><small>Online</small></span><span>Encryption <b>AES-256</b><small>Hardened</small></span><span>P2P Latency <b>14ms</b><small>Optimized</small></span></div><div class="bars">' + ''.join('<i></i>' for _ in range(24)) + '</div>', 'dark col-8')}
      {card('<h3>Linked Hardware</h3><div class="info-box">Sarah iPhone - Filiation Node Active</div><div class="info-box">Fili-Hub Node 1 - Primary Relay</div><div class="info-box muted-box">Leo Android - Disconnected</div>', 'col-4')}
      {card('<h2>API Vault</h2><p>Securely store credentials for Plaid, Schoology, and Insurance portals. Keys stay on your family nodes.</p><div class="button-row"><button class="button dark">Manage Keys</button><button class="button muted">Clear Cache</button></div>', 'col-12')}
      {card('<div class="split"><h2>P2P Request Relay</h2><span class="status">2 Pending Handshakes</span></div>' + requests + '<button class="button muted full">Broadcast New Collective Request</button>', 'col-12')}
    </div>
    """
    return layout("Sync", body, profile, "/sync")


def settings_page(profile: dict[str, str], saved: bool = False) -> str:
    notice = '<div class="success-inline">Sanctuary Synced!</div>' if saved else ""
    body = f"""
    <header class="page-title"><h1>Sanctuary Profile</h1><p>Manage your digital presence and privacy settings.</p></header>
    <div class="grid-12 settings-grid">
      <aside class="col-4 stack">
        {card(f'<img class="profile-photo" src="{esc(profile.get("photoURL"))}" alt="Profile"><h2>{esc(profile.get("displayName"))}</h2><p>Locally Encrypted</p>')}
        {card('<h3>Push Alerts</h3><p>Enable notifications to receive instant updates.</p><button id="notifyButton" class="button primary full">Setup Notifications</button>', 'dark')}
      </aside>
      <form class="col-8 card form-stack" method="post" action="/settings">
        <h2>Core Identity</h2>
        <div class="field-grid">
          <label>Display Name<input name="displayName" value="{esc(profile.get("displayName"))}"></label>
          <label>Email Address<input value="{esc(profile.get("email"))}" disabled></label>
          <label>Birthday<input name="birthday" type="date" value="{esc(profile.get("birthday"))}"></label>
          <label>Phone Number<input name="phoneNumber" value="{esc(profile.get("phoneNumber"))}" placeholder="+1 (555) 000-0000"></label>
        </div>
        <label>About Me<textarea name="bio" placeholder="Share a short bio with your family...">{esc(profile.get("bio"))}</textarea></label>
        <label>Profile Image URL<input name="photoURL" value="{esc(profile.get("photoURL"))}" placeholder="https://..."></label>
        <div class="split">{notice}<button class="button primary" type="submit">Update Profile</button></div>
      </form>
    </div>
    """
    return layout("Settings", body, profile, "/settings")


CSS = r"""
:root{--primary:#4f46e5;--primary-2:#6366f1;--secondary:#10b981;--tertiary:#f97316;--base:#f1f5f9;--low:#f8fafc;--variant:#e2e8f0;--ink:#0f172a;--muted:#64748b}
*{box-sizing:border-box}body{margin:0;background:var(--base);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:inherit;text-decoration:none}button,input,textarea{font:inherit}button{cursor:pointer}
.app-shell{min-height:100vh;display:grid;grid-template-columns:16rem minmax(0,1fr)20rem}.sidebar,.chat,.topbar{background:white;border-color:#e2e8f0}.sidebar{position:sticky;top:0;height:100vh;padding:1.5rem;border-right:1px solid #e2e8f0}.brand{display:flex;align-items:center;gap:.75rem;margin-bottom:2rem;font-size:1.5rem}.brand-mark{display:grid;place-items:center;width:2.5rem;height:2.5rem;border-radius:.85rem;background:var(--primary);color:white;font-weight:900}.nav-list{display:flex;flex-direction:column;gap:.25rem}.nav-item{width:100%;border:0;background:transparent;display:flex;align-items:center;gap:.75rem;padding:.75rem 1rem;border-radius:.85rem;color:#475569;font-weight:800}.nav-item.active,.nav-item:hover{background:#eef2ff;color:var(--primary)}.nav-item.danger{color:#e11d48;margin-top:1rem}.family-pill{margin-top:2rem;padding:1rem;border-radius:1rem;background:#f8fafc;color:#94a3b8;font-size:.7rem;text-transform:uppercase;letter-spacing:.08em}.main{min-width:0}.topbar{height:4rem;position:sticky;top:0;z-index:2;border-bottom:1px solid #e2e8f0;display:flex;align-items:center;justify-content:space-between;padding:0 2rem}.user-chip{display:flex;align-items:center;gap:.75rem}.user-chip img{width:2.5rem;height:2.5rem;object-fit:cover;border-radius:999px}.user-chip small,.bubble small{display:block;color:var(--secondary);font-size:.65rem;text-transform:uppercase;font-weight:900;letter-spacing:.08em}.content{padding:2rem;max-width:88rem}.chat{position:sticky;top:0;height:100vh;border-left:1px solid #e2e8f0;padding:2rem;display:flex;flex-direction:column;gap:1rem}.chat-head{display:flex;justify-content:space-between}.chat-head span{width:.5rem;height:.5rem;background:var(--secondary);border-radius:999px}.bubble{max-width:85%;background:var(--low);border-radius:1.2rem 1.2rem 1.2rem .25rem;padding:1rem;font-size:.9rem}.bubble.mine{align-self:flex-end;background:var(--primary);color:white;border-radius:1.2rem 1.2rem .25rem 1.2rem}.chat-input{margin-top:auto;border:0;background:#f8fafc;border-radius:.85rem;padding:1rem}.mobile-nav{display:none}
.page-title{margin-bottom:2rem}.page-title h1{font-size:clamp(2.4rem,5vw,4rem);line-height:.95;margin:.2rem 0;font-weight:950;letter-spacing:0}.page-title p{font-size:1.15rem;color:#64748b;font-weight:650}.row-title,.split{display:flex;align-items:center;justify-content:space-between;gap:1rem}.button-row{display:flex;gap:.75rem;flex-wrap:wrap}.button{border:0;border-radius:1rem;padding:.9rem 1.25rem;font-weight:900;transition:.2s}.button.primary{background:var(--primary);color:white;box-shadow:0 12px 28px rgba(79,70,229,.22)}.button.light{background:white;color:var(--primary)}.button.ghost{background:rgba(255,255,255,.18);color:white}.button.muted{background:#f1f5f9;color:#64748b}.button.dark{background:#0f172a;color:white}.button.small{padding:.55rem .9rem;font-size:.8rem}.button.full{width:100%}.card{background:white;border:1px solid #e2e8f0;border-radius:1.5rem;padding:2rem;box-shadow:0 1px 3px rgba(15,23,42,.08)}.dashboard-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1.5rem}.grid-12{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:1.5rem}.span-3{grid-column:span 3}.span-2{grid-column:span 2}.col-4{grid-column:span 4}.col-8{grid-column:span 8}.col-12{grid-column:span 12}.stack{display:flex;flex-direction:column;gap:1.5rem}.hero{background:linear-gradient(135deg,var(--primary),var(--primary-2));color:white;min-height:18rem;display:flex;flex-direction:column;justify-content:space-between;overflow:hidden}.hero h2{font-size:clamp(2rem,4vw,3.25rem);line-height:1.05;margin:.75rem 0}.eyebrow,.status{display:inline-block;border-radius:999px;background:rgba(79,70,229,.1);color:var(--primary);font-size:.65rem;text-transform:uppercase;letter-spacing:.14em;font-weight:950;padding:.4rem .7rem}.hero .eyebrow{background:rgba(255,255,255,.2);color:white}.metric,.big-number{font-size:3.4rem;font-weight:950;margin:.6rem 0}.metric small{font-size:1rem;color:#94a3b8}.green{color:var(--secondary)}.round-icon,.request-icon{display:grid;place-items:center;width:3rem;height:3rem;border-radius:1rem;background:#eef2ff;color:var(--primary);font-weight:950}.alert-row,.list-row{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:1rem;border-radius:1rem;background:#f8fafc;margin-top:.75rem}.alert-row div,.list-row div{min-width:0}.alert-row small,.list-row small,.vault small,.mini-card small{display:block;color:#94a3b8;font-size:.7rem;text-transform:uppercase;font-weight:900;letter-spacing:.08em}.center{text-align:center}.weather,.sync-cloud{font-size:2.8rem;font-weight:950}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;border-top:1px solid #e2e8f0;margin-top:2rem;padding-top:2rem}.stats span{color:#94a3b8;text-transform:uppercase;font-size:.7rem;font-weight:900}.stats b{display:block;color:var(--ink);font-size:1.5rem;text-transform:none}.info-box,.success-box{padding:1rem;border-radius:1rem;background:#eef2ff;color:#4338ca;font-weight:750}.success-box{background:#ecfdf5;color:#059669}.muted-box{background:#f1f5f9;color:#64748b}.donut{width:10rem;height:10rem;border-radius:999px;margin:1rem auto;background:conic-gradient(#6366f1 0 14%,#f59e0b 14% 18%,#10b981 18% 43%,#ec4899 43% 49%,#f43f5e 49% 76%,#8b5cf6 76%)}.legend{list-style:none;padding:0;margin:1rem 0 0}.legend li{display:flex;align-items:center;justify-content:space-between;gap:.5rem;margin:.45rem 0;font-size:.8rem;font-weight:800;color:#64748b}.legend li span{width:.5rem;height:.5rem;border-radius:999px}.amount{text-align:right;font-weight:950}.amount small{color:var(--secondary)}.vault{background:#f8fafc;border-radius:1rem;padding:1rem;margin-top:1rem}.vault p{font-size:1.4rem;font-weight:950;margin:.5rem 0}.dark{background:#0f172a;color:white}.dark p{color:rgba(255,255,255,.68)}.timeline{position:relative}.timeline-item{display:flex;gap:1rem;margin:1.25rem 0}.timeline-item>span{width:1rem;height:1rem;background:var(--primary);border-radius:999px;margin-top:.35rem;box-shadow:0 0 0 .25rem white}.timeline-item small{color:var(--primary);font-size:.7rem;text-transform:uppercase;font-weight:950;letter-spacing:.08em}.timeline-item h3{margin:.15rem 0}.timeline-item p{color:#64748b;margin:.25rem 0}.mini-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1rem}.mini-card{background:#f8fafc}.calendar-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:1rem;margin-bottom:2rem}.calendar-grid>b{text-align:center;color:#94a3b8;text-transform:uppercase;font-size:.7rem;letter-spacing:.16em}.calendar-cell{aspect-ratio:1;border-radius:1.2rem;background:white;border:1px solid #e2e8f0;padding:1rem}.calendar-cell.today{background:var(--primary);color:white;transform:scale(1.04)}.calendar-cell.empty{background:rgba(248,250,252,.6);border:0}.calendar-cell small{display:block;margin-top:.6rem;color:var(--secondary);background:#ecfdf5;border-radius:.5rem;padding:.25rem;font-size:.65rem;font-weight:900}.dots span{display:inline-block;width:.4rem;height:.4rem;background:var(--primary);border-radius:999px;margin-right:.25rem}.today .dots span{background:white}.green-dot{background:var(--secondary)!important}.filters{display:flex;gap:.5rem;flex-wrap:wrap}.filters span{background:white;border-radius:999px;padding:.75rem 1rem;font-weight:900;color:#64748b}.node-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin:2rem 0}.node-grid span{color:rgba(255,255,255,.45);font-size:.7rem;text-transform:uppercase;font-weight:900}.node-grid b{display:block;color:white;font-size:2rem;text-transform:none}.node-grid small{display:block;color:#34d399}.bars{display:flex;align-items:end;gap:.25rem;height:3rem}.bars i{flex:1;border-radius:999px;background:rgba(16,185,129,.55);height:1rem;animation:pulse 1s infinite alternate}.bars i:nth-child(3n){height:2rem}.profile-photo{width:8rem;height:8rem;border-radius:999px;object-fit:cover;display:block;margin:auto}.settings-grid label,.auth-card label{display:flex;flex-direction:column;gap:.45rem;color:#64748b;text-transform:uppercase;letter-spacing:.08em;font-size:.7rem;font-weight:950}.settings-grid input,.settings-grid textarea,.auth-card input{border:0;background:#f8fafc;border-radius:1rem;padding:1rem;color:var(--ink);text-transform:none;letter-spacing:0}.settings-grid textarea{min-height:8rem;resize:vertical}.field-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.success-inline{color:#059669;font-weight:900}.auth-page{min-height:100vh;display:grid;grid-template-columns:1fr 1.35fr;gap:4rem;align-items:center;padding:4rem;max-width:90rem;margin:auto}.auth-copy h1{font-size:clamp(3rem,7vw,5.4rem);line-height:.9;margin:3rem 0 1.5rem;font-weight:950}.auth-copy p{font-size:1.2rem;color:#64748b;max-width:34rem}.feature-row{display:flex;gap:1rem;flex-wrap:wrap;margin-top:3rem}.feature-row span{background:white;border-radius:1rem;padding:1rem;font-weight:900}.auth-card{background:white;border-radius:2rem;padding:2rem;box-shadow:0 12px 36px rgba(15,23,42,.1)}.mode-tabs{display:inline-flex;background:#f8fafc;border-radius:999px;padding:.35rem;margin-bottom:2rem}.mode-tabs a{padding:.8rem 2rem;border-radius:999px;font-weight:950;color:#94a3b8}.mode-tabs a.active{background:white;color:var(--primary);box-shadow:0 1px 3px rgba(15,23,42,.12)}.auth-grid{display:grid;grid-template-columns:1fr 1fr;gap:2rem}.form-stack{display:flex;flex-direction:column;gap:1rem}.notice{font-size:.7rem;color:#818cf8;text-transform:uppercase;font-weight:900;text-align:center}.onboarding{background:#f8fafc;border-radius:1.5rem;padding:1.5rem}.auth-card footer{border-top:1px solid #e2e8f0;margin-top:2rem;padding-top:1rem;display:flex;justify-content:space-between;color:#94a3b8;font-size:.75rem;font-weight:900;text-transform:uppercase}
@keyframes pulse{to{height:2.6rem}}@media(max-width:1200px){.app-shell{grid-template-columns:16rem minmax(0,1fr)}.chat{display:none}.dashboard-grid{grid-template-columns:repeat(2,1fr)}.span-3,.span-2{grid-column:span 2}}@media(max-width:760px){.app-shell{display:block}.sidebar{display:none}.topbar{padding:0 1rem}.content{padding:1rem 1rem 6rem}.mobile-nav{display:flex;position:fixed;bottom:0;left:0;right:0;background:white;border-top:1px solid #e2e8f0;justify-content:space-around;padding:.5rem;z-index:5}.mobile-nav .nav-item{font-size:.7rem;flex-direction:column;gap:.2rem;padding:.45rem}.dashboard-grid,.grid-12,.auth-page,.auth-grid,.field-grid,.mini-grid{grid-template-columns:1fr}.col-4,.col-8,.col-12,.span-3,.span-2{grid-column:auto}.row-title,.split{align-items:flex-start;flex-direction:column}.calendar-grid{gap:.35rem}.calendar-cell{padding:.5rem;border-radius:.8rem}.auth-page{padding:1rem}.auth-copy h1{margin:1.5rem 0;font-size:3rem}.node-grid,.stats{grid-template-columns:1fr}}
"""


JS = r"""
const syncButton = document.getElementById("syncButton");
if (syncButton) {
  syncButton.addEventListener("click", () => {
    syncButton.disabled = true;
    syncButton.textContent = "Relaying Nodes...";
    setTimeout(() => {
      syncButton.textContent = "Nodes Aligned";
      if ("Notification" in window && Notification.permission === "granted") {
        new Notification("Sanctuary Sync Complete", { body: "All family nodes have been updated." });
      }
      setTimeout(() => {
        syncButton.disabled = false;
        syncButton.textContent = "Manual Sanctuary Sync";
      }, 1800);
    }, 1400);
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
      new Notification("Sanctuary Synced", { body: "You will now receive family alerts on this device." });
    }
  });
}
"""


class FiliationHandler(BaseHTTPRequestHandler):
    def current_profile(self) -> dict[str, str] | None:
        cookies = parse_cookies(self.headers.get("Cookie"))
        uid = verify_cookie(cookies.get("filiation_session"))
        if not uid:
            return None
        users = load_users()
        return users.get(uid)

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
