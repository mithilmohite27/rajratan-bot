import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import os, json, re, requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIG ─────────────────────────────────────────
st.set_page_config(page_title="Rajratan AI Assistant", layout="wide")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS_FILE = os.getenv("GOOGLE_CREDS_JSON", "credentials.json")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ─── SESSION STATE ─────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Welcome! Example: Sold 50 brass to Patel rate 800"}
    ]

if "pending_data" not in st.session_state:
    st.session_state.pending_data = None

# ─── GOOGLE SHEETS ────────────────────────────────
def get_client():
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)

def get_sheet(name):
    return get_client().open_by_key(SHEET_ID).worksheet(name)

def write_to_sheet(sheet, data):
    ws = get_sheet(sheet)
    headers = ws.row_values(1)

    if not headers:
        headers = list(data.keys())
        ws.append_row(headers)

    row = [data.get(h, "") for h in headers]
    ws.append_row(row)

# ─── AI PARSER ────────────────────────────────────
def ai_parser_sync(message: str):
    today = datetime.today().strftime("%Y-%m-%d")

    fallback = {
        "intent": "unknown",
        "language": "en",
        "target_sheet": None,
        "extracted_data": {},
        "confirmation_message": "❓ Could not understand",
        "missing_fields": []
    }

    prompt = f"""
Extract business data from message (English/Hindi/Gujarati).
Reply ONLY JSON.

Today: {today}

JSON:
{{
"intent":"add_client_order|add_production|add_cashflow|unknown",
"language":"en|hi|gu",
"target_sheet":"Clients|Block_Stocks|Cashflow|null",
"extracted_data":{{}},
"confirmation_message":"short confirmation",
"missing_fields":[]
}}

Message: {message}
"""

    try:
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=15
        )

        res.raise_for_status()

        raw = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

        # Clean markdown
        raw = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()

        # Extract JSON
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return fallback

        parsed = json.loads(match.group())

        # Safety defaults
        parsed.setdefault("intent", "unknown")
        parsed.setdefault("language", "en")
        parsed.setdefault("target_sheet", None)
        parsed.setdefault("extracted_data", {})
        parsed.setdefault("confirmation_message", "Done")
        parsed.setdefault("missing_fields", [])

        return parsed

    except Exception as e:
        print("Parser Error:", e)
        return fallback

# ─── UI ───────────────────────────────────────────
st.title("🏗️ Rajratan AI Factory Assistant")

# Show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Type here...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    parsed = ai_parser_sync(user_input)

    st.session_state.pending_data = parsed

    with st.chat_message("assistant"):
        st.markdown(parsed["confirmation_message"])
        st.markdown("👉 Confirm?")

# ─── CONFIRMATION BUTTONS ─────────────────────────
if st.session_state.pending_data:
    col1, col2 = st.columns(2)

    if col1.button("✅ Yes"):
        data = st.session_state.pending_data

        try:
            if data["target_sheet"]:
                write_to_sheet(data["target_sheet"], data["extracted_data"])

            st.success("✅ Saved successfully")
            st.session_state.pending_data = None

            st.rerun()  # refresh UI

        except Exception as e:
            st.error(f"Error: {e}")

    if col2.button("❌ No"):
        st.warning("Cancelled")
        st.session_state.pending_data = None