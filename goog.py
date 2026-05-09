from __future__ import annotations

"""
FinAI — Python Banking Assistant
=================================
A conversational AI assistant that reads live data from your app and
can directly tell users their account info, transactions, spending
insights, budgets, and navigate your app — on demand, via tool-use.

HOW TO INTEGRATE
----------------
1. pip install anthropic

2. Replace the functions in AppDataLayer with calls to YOUR data source
   (database, REST API, ORM, etc.). The AI reads from these — no data
   is hardcoded inside the assistant itself.

3. Call  FinAI(data_layer).chat()  to start an interactive session, or
   use  FinAI(data_layer).ask(question)  to get a single answer.

EXAMPLE
-------
    data = AppDataLayer(user_id="u_123")   # connects to your DB / API
    ai   = FinAI(data)
    ai.chat()                              # starts interactive loop
"""

import json
import os
from typing import Any
from urllib.parse import urlencode

try:
    import anthropic
except ImportError:  # Allows app.py to import helper functions without Anthropic installed.
    anthropic = None


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"


def authorization_url(client_id: str, redirect_uri: str, state: str) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_CALENDAR_READONLY_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def authorization_code_payload(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict[str, str]:
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }


def refresh_token_payload(client_id: str, client_secret: str, refresh_token: str) -> dict[str, str]:
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }


def gemini_generate_url(api_key: str, model: str = DEFAULT_GEMINI_MODEL) -> str:
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?{urlencode({'key': api_key})}"


def gemini_payload(system_prompt: str, user_prompt: str) -> dict[str, object]:
    return {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 900},
    }


def extract_gemini_text(response: dict[str, object]) -> str:
    candidates = response.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return ""
    content = candidates[0].get("content") if isinstance(candidates[0], dict) else None
    if not isinstance(content, dict):
        return ""
    parts = content.get("parts")
    if not isinstance(parts, list):
        return ""
    return "\n".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)).strip()

# ─── APP DATA LAYER ───────────────────────────────────────────────────────────
# Replace each method body with a real query to your database or API.
# The AI never sees this class — it only sees the JSON returned by each tool.

class AppDataLayer:
    """
    Connects to your application's data source.
    Swap the mock return values with real DB queries or API calls.
    """

    def __init__(self, user_id: str = "demo_user"):
        self.user_id = user_id
        # e.g. self.db = MyDatabase(user_id)

    # ── Replace bodies below with real queries ────────────────────────────────

    def get_accounts(self) -> list[dict]:
        """Return all accounts for this user."""
        # Example real implementation:
        #   return self.db.query("SELECT * FROM accounts WHERE user_id = ?", self.user_id)
        return [
            {"id": "chk_4821", "label": "Checking",    "number": "••4821", "balance": 4218.50,  "type": "checking", "apy": None,  "limit": None},
            {"id": "sav_9203", "label": "Savings",     "number": "••9203", "balance": 12340.00, "type": "savings",  "apy": 2.1,   "limit": None},
            {"id": "cc_3391",  "label": "Credit Card", "number": "••3391", "balance": 847.30,   "type": "credit",   "apy": None,  "limit": 5000},
        ]

    def get_transactions(self, limit: int = 10, category: str | None = None) -> list[dict]:
        """Return recent transactions, optionally filtered by category."""
        # Example: return self.db.query("SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT ?", self.user_id, limit)
        all_tx = [
            {"id": "t1", "merchant": "Whole Foods",    "category": "Groceries",     "amount": -67.42,  "date": "2025-05-07"},
            {"id": "t2", "merchant": "Netflix",        "category": "Entertainment", "amount": -15.99,  "date": "2025-05-06"},
            {"id": "t3", "merchant": "Shell Gas",      "category": "Transport",     "amount": -54.00,  "date": "2025-05-05"},
            {"id": "t4", "merchant": "Amazon",         "category": "Shopping",      "amount": -129.99, "date": "2025-05-04"},
            {"id": "t5", "merchant": "Starbucks",      "category": "Food & Dining", "amount": -6.75,   "date": "2025-05-03"},
            {"id": "t6", "merchant": "Direct Deposit", "category": "Income",        "amount": 2800.00, "date": "2025-05-01"},
            {"id": "t7", "merchant": "Uber",           "category": "Transport",     "amount": -22.50,  "date": "2025-04-30"},
            {"id": "t8", "merchant": "Spotify",        "category": "Entertainment", "amount": -9.99,   "date": "2025-04-29"},
        ]
        if category:
            all_tx = [t for t in all_tx if t["category"].lower() == category.lower()]
        return all_tx[:limit]

    def get_spending_summary(self) -> dict[str, float]:
        """Return total spent per category (debits only)."""
        # Example: aggregate query grouping by category
        summary: dict[str, float] = {}
        for tx in self.get_transactions(limit=100):
            if tx["amount"] < 0:
                cat = tx["category"]
                summary[cat] = round(summary.get(cat, 0) + abs(tx["amount"]), 2)
        return summary

    def get_budgets(self) -> list[dict]:
        """Return budget limits and current spend for each category."""
        # Example: return self.db.query("SELECT * FROM budgets WHERE user_id = ?", self.user_id)
        return [
            {"category": "Groceries",     "limit": 300, "spent": 67.42},
            {"category": "Entertainment", "limit": 50,  "spent": 25.98},
            {"category": "Transport",     "limit": 150, "spent": 76.50},
            {"category": "Food & Dining", "limit": 200, "spent": 6.75},
        ]

    def get_cards(self) -> list[dict]:
        """Return the user's debit and credit cards."""
        return [
            {"id": "card_1", "label": "Visa Debit", "number": "••4821", "frozen": False, "limit": None},
            {"id": "card_2", "label": "Mastercard", "number": "••3391", "frozen": False, "limit": 5000},
        ]

    def navigate_to(self, screen: str) -> dict:
        """
        Hook for app navigation. In a web/mobile app, emit an event or
        call a callback here. In CLI mode we just report where we'd go.
        """
        # Example web app: requests.post(f"{APP_URL}/navigate", json={"screen": screen})
        print(f"\n  📍 [App] → Navigating to: {screen.upper()}\n")
        return {"navigated": True, "screen": screen}


# ─── TOOL DEFINITIONS ─────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "get_accounts",
        "description": (
            "Get all of the user's bank and credit accounts with current balances. "
            "Call this when the user asks about their balance, accounts, funds, or money."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_transactions",
        "description": (
            "Get the user's recent transactions. Call when asked about purchases, "
            "spending history, charges, or recent activity. Can filter by category."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit":    {"type": "integer", "description": "Max number of transactions to return (default 10)"},
                "category": {"type": "string",  "description": "Filter by category name, e.g. 'Groceries' (optional)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_spending_summary",
        "description": (
            "Get a breakdown of how much the user has spent per category. "
            "Call when asked about spending habits, patterns, where their money goes, or insights."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_budgets",
        "description": (
            "Get the user's budget limits and how much has been spent against each. "
            "Call when asked about budgets or whether they're on track."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_cards",
        "description": "Get the user's debit and credit cards and their status.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "navigate_to",
        "description": (
            "Navigate the app to a specific screen. Call when the user says "
            "'take me to', 'show me', 'open', or 'go to' a section of the app."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "screen": {
                    "type": "string",
                    "enum": ["dashboard", "transactions", "budgets", "cards", "transfer", "insights", "settings"],
                    "description": "The screen to navigate to",
                }
            },
            "required": ["screen"],
        },
    },
]

SYSTEM_PROMPT = """You are FinAI, a smart and friendly AI banking assistant.
You help users understand their finances, navigate the app, and get insights on their spending.

STRICT RULES:
- NEVER invent, guess, or assume any financial data. You have no memory of previous data between sessions.
- Always call the appropriate tool BEFORE quoting any number, balance, or transaction detail.
- When a user asks about balances, transactions, spending, budgets, or cards — call the tool first, then answer using its result.
- When a user says "take me to", "show me", "open", or "go to" a section — call navigate_to immediately, then confirm.
- Be concise, warm, and direct. Format currency with $. Use bullet points when listing data.
- You can answer follow-up questions using data already returned in this conversation without re-fetching.

App screens you can navigate to:
  dashboard    — account overview and balances
  transactions — full transaction history
  budgets      — budget limits and spend progress
  cards        — manage debit and credit cards
  transfer     — move money between accounts
  insights     — category spending breakdown
  settings     — app and account preferences"""


# ─── FINAI ASSISTANT ──────────────────────────────────────────────────────────

class FinAI:
    """
    FinAI — conversational banking assistant.

    Usage:
        data = AppDataLayer(user_id="u_123")
        ai   = FinAI(data)
        ai.chat()                    # interactive CLI loop
        reply = ai.ask("balance?")   # single programmatic call
    """

    def __init__(self, data_layer: AppDataLayer, api_key: str | None = None):
        self.data   = data_layer
        if anthropic is None:
            raise RuntimeError("Install the anthropic package to use FinAI directly.")
        self.client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.history: list[dict] = []   # conversation memory for multi-turn chat

    # ── Tool dispatcher — reads from your app's data layer ────────────────────

    def _run_tool(self, name: str, inputs: dict) -> Any:
        """Execute a tool call by reading from the app data layer."""
        if name == "get_accounts":
            return self.data.get_accounts()
        if name == "get_transactions":
            return self.data.get_transactions(
                limit=inputs.get("limit", 10),
                category=inputs.get("category"),
            )
        if name == "get_spending_summary":
            return self.data.get_spending_summary()
        if name == "get_budgets":
            return self.data.get_budgets()
        if name == "get_cards":
            return self.data.get_cards()
        if name == "navigate_to":
            return self.data.navigate_to(inputs["screen"])
        return {"error": f"Unknown tool: {name}"}

    # ── Agentic loop — handles multi-step tool use ────────────────────────────

    def _agent_loop(self, messages: list[dict]) -> str:
        """
        Run the agentic tool-use loop.
        Keeps calling Claude + executing tools until a final text reply is ready.
        """
        loop_messages = list(messages)

        for _ in range(8):   # safety cap on tool rounds
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=loop_messages,
            )

            tool_uses  = [b for b in response.content if b.type == "tool_use"]
            text_parts = [b for b in response.content if b.type == "text"]

            # Done — no more tools needed
            if response.stop_reason == "end_turn" or not tool_uses:
                return "\n".join(b.text for b in text_parts).strip() or "Done."

            # Show what tools are being called
            for tool in tool_uses:
                print(f"  🔍 Fetching {tool.name.replace('_', ' ')}…")

            # Execute all tool calls
            tool_results = []
            for tool in tool_uses:
                result = self._run_tool(tool.name, tool.input)
                tool_results.append({
                    "type":        "tool_result",
                    "tool_use_id": tool.id,
                    "content":     json.dumps(result),
                })

            # Append assistant message + results and continue loop
            loop_messages = [
                *loop_messages,
                {"role": "assistant", "content": response.content},
                {"role": "user",      "content": tool_results},
            ]

        return "I had trouble completing that request — please try again."

    # ── Public API ────────────────────────────────────────────────────────────

    def ask(self, question: str) -> str:
        """
        Ask a single question. Maintains conversation history for follow-ups.
        Returns the AI's reply as a string.
        """
        self.history.append({"role": "user", "content": question})
        reply = self._agent_loop(self.history)
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def reset(self):
        """Clear conversation history to start a fresh session."""
        self.history = []

    def chat(self):
        """
        Start an interactive terminal chat session.
        Type 'quit', 'exit', or 'bye' to stop.
        Type 'reset' to clear history.
        """
        print("\n" + "═" * 52)
        print("  ◆  FinAI — Banking Assistant")
        print("═" * 52)
        print("  Ask about your accounts, transactions,")
        print("  spending insights, budgets, or navigate")
        print("  your app. Type 'quit' to exit.\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nFinAI: Goodbye! 👋")
                break

            if not user_input:
                continue

            if user_input.lower() in {"quit", "exit", "bye"}:
                print("\nFinAI: Goodbye! 👋\n")
                break

            if user_input.lower() == "reset":
                self.reset()
                print("FinAI: Conversation cleared. Fresh start! ✨\n")
                continue

            print()   # breathing room before tool activity
            reply = self.ask(user_input)
            print(f"\nFinAI: {reply}\n")
            print("─" * 52)


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Swap AppDataLayer for one that reads from your real database or API
    data_layer = AppDataLayer(user_id="demo_user")
    assistant  = FinAI(data_layer)
    assistant.chat()
