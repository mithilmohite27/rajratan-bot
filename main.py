import asyncio
import random
from dotenv import load_dotenv
load_dotenv()
import os, re, json, httpx
from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

app = FastAPI(title="Rajratan Enterprises - WhatsApp Bot")

# ─── Environment Variables & Setup ──────────────────────────────────────────
SCOPES    = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS_FILE      = os.getenv("GOOGLE_CREDS_JSON", "credentials.json")
SHEET_ID        = os.getenv("GOOGLE_SHEET_ID", "YOUR_SHEET_ID")
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY") 

def get_sheet(sheet_name: str):
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc    = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID).worksheet(sheet_name)

user_sessions: dict = {}

AFFIRMATIVE = {"yes","ha","haan","han","हाँ","हा","ہاں","ok","okay","confirm","हां","ho","ho jay"}
NEGATIVE    = {"no","na","nahi","naa","नहीं","ना","نہیں","cancel","nope","band karo"}

# ─── AI Parser with Retry Logic ───────────────────────────────────────────────

async def ai_parser(message: str) -> dict:
    today = datetime.today().strftime("%Y-%m-%d")
    
    # Updated fallback message to let you know it's a rate limit issue
    fallback = {
        "intent": "unknown", "language": "en",
        "target_sheet": None, "extracted_data": {},
        "confirmation_message": "⚠️ The AI system is currently busy or rate-limited. Please wait 30 seconds and try sending your message again.",
        "missing_fields": [],
    }
    
    prompt = f"""You are a data-entry bot for a concrete block factory in India.
Extract business data from the message (English/Hindi/Gujarati mixed is normal).
Reply ONLY with valid JSON, no markdown, no explanation.

Today: {today}

JSON shape:
{{"intent":"add_client_order|add_production|add_cement_purchase|add_chemical_entry|add_labour_salary|add_cashflow|unknown",
"language":"en|hi|gu","target_sheet":"Clients|Block_Stocks|Cement_Stocks|Greet_Powder_Chemical|Labour_Salary|Cashflow|null",
"extracted_data":{{}},"confirmation_message":"WhatsApp summary with emoji","missing_fields":[]}}

Rules:
- add_client_order: selling brass/blocks → {{Date,Client_Name,Qty_Brass,Rate_INR,Total_INR,Notes}}
- add_production: making blocks → {{Date,New_Stock,Block_Type,Note}}
- add_cement_purchase: buying cement → {{Date,New_In,Rate_INR,Amount_INR,Note}}
- add_chemical_entry: buying grit/powder/chemical → {{Date,Item_Name,Qty_Ton,Rate_INR,Amount_INR}}
- add_labour_salary: paying worker → {{Date,Worker_Name,Amount_INR,Notes}}
- add_cashflow: money in/out → {{Date,Type(IN or OUT),Amount_INR,Description}}
- IN: received/aavya/bheje. OUT: paid/diya/aapiya/diesel/repair
- Missing number → 0, add to missing_fields
- confirmation_message MUST ask for Yes/No confirmation in the same language.

Message: {message}"""

    max_retries = 4 # Increased to 4 retries
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={GEMINI_API_KEY}",
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                )
                
                # Check for rate limit BEFORE trying to parse
                if resp.status_code == 429:
                    if attempt < max_retries - 1:
                        # Exponential backoff + random jitter (e.g., 2 seconds + 0.4 seconds)
                        sleep_time = (2 ** attempt) + random.uniform(0.1, 1.5)
                        print(f"⚠️ Rate limited by Google (429). Retrying in {sleep_time:.2f} seconds...")
                        await asyncio.sleep(sleep_time)
                        continue
                    else:
                        print("❌ Max retries reached. Google is strictly blocking requests right now.")
                        return fallback # Return safely, DO NOT CRASH

                # If it's not a 429, check for other HTTP errors (500, etc.)
                resp.raise_for_status() 
                
                raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
                match = re.search(r"\{.*\}", raw, re.DOTALL)
                
                if not match:
                    return fallback
                    
                parsed = json.loads(match.group())
                for key in ("intent","language","target_sheet","extracted_data","confirmation_message","missing_fields"):
                    if key not in parsed:
                        parsed[key] = fallback[key]
                return parsed
                
        except httpx.HTTPStatusError as e:
            # Catching it here just in case it slips through
            if e.response.status_code == 429 and attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + random.uniform(0.1, 1.5)
                await asyncio.sleep(sleep_time)
                continue
            print(f"❌ HTTP Error: {e}")
            return fallback
            
        except Exception as e:
            print(f"❌ General Error in AI Parser: {e}")
            return fallback
            
    return fallback

# ─── Sheet Writers ────────────────────────────────────────────────────────────

def write_to_sheet(target_sheet: str, data: dict):
    ws      = get_sheet(target_sheet)
    headers = ws.row_values(1)
    if not headers:
        headers = list(data.keys())
        ws.append_row(headers)
    row = [data.get(h, "") for h in headers]
    ws.append_row(row)

def write_stocks_with_continuity(sheet_name: str, data: dict):
    ws       = get_sheet(sheet_name)
    all_vals = ws.get_all_values()
    if len(all_vals) > 1:
        last_row = all_vals[-1]
        headers  = all_vals[0]
        try:
            closing_idx = headers.index("Closing")
            try:
                prev_closing = float(last_row[closing_idx])
            except (ValueError, TypeError):
                prev_closing = 0.0
            data["Opening"] = prev_closing
            ni = float(data.get("New_In", 0))
            sl = float(data.get("Sales", 0))
            data["Total"]   = prev_closing + ni
            data["Closing"] = prev_closing + ni - sl
        except (ValueError, IndexError):
            pass
    write_to_sheet(sheet_name, data)

def write_production_to_block_stocks(data: dict):
    ws       = get_sheet("Block_Stocks")
    all_vals = ws.get_all_values()
    prev_closing = 0.0
    if len(all_vals) > 1:
        last_row = all_vals[-1]
        headers  = all_vals[0]
        try:
            closing_idx  = headers.index("Closing")
            prev_closing = float(last_row[closing_idx]) if last_row[closing_idx] else 0.0
        except (ValueError, IndexError):
            pass
    data["Opening"] = prev_closing
    ni = float(data.get("New_Stock", 0))
    data["New_In"]  = ni
    data["Total"]   = prev_closing + ni
    data["Closing"] = prev_closing + ni
    write_to_sheet("Block_Stocks", data)

# ─── Webhook ──────────────────────────────────────────────────────────────────

@app.post("/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
):
    sender    = From.strip()
    msg       = Body.strip()
    resp      = MessagingResponse()
    twiml_msg = resp.message()
    session   = user_sessions.get(sender)

    # 1. User is replying to a confirmation message
    if session and session.get("state") == "pending":
        normalized = msg.lower().strip()

        if normalized in AFFIRMATIVE:
            target = session["target_sheet"]
            data   = session["extracted_data"]
            intent = session.get("intent", "")
            try:
                if intent == "add_production":
                    write_production_to_block_stocks(data)
                elif target in ("Block_Stocks", "Cement_Stocks") and "Opening" in data:
                    write_stocks_with_continuity(target, data)
                else:
                    write_to_sheet(target, data)

                lang = session.get("language", "en")
                success_msgs = {
                    "en": f"✅ Saved to *{target}* successfully!",
                    "gu": f"✅ *{target}* માં સફળતાપૂર્વક સેવ થયો!",
                    "hi": f"✅ *{target}* में सफलतापूर्वक सेव हो गया!",
                }
                twiml_msg.body(success_msgs.get(lang, success_msgs["en"]))
            except Exception as e:
                twiml_msg.body(f"❌ Error saving: {str(e)}\nPlease try again.")
            del user_sessions[sender]

        elif normalized in NEGATIVE:
            lang = session.get("language", "en")
            cancel_msgs = {
                "en": "❌ Entry cancelled. Send a new message to start over.",
                "gu": "❌ એન્ટ્રી રદ કરી. નવો સંદેશ મોકલો.",
                "hi": "❌ एंट्री रद्द की गई। नया संदेश भेजें।",
            }
            twiml_msg.body(cancel_msgs.get(lang, cancel_msgs["en"]))
            del user_sessions[sender]

        else:
            twiml_msg.body(
                "⚠️ Please reply with *Yes* to confirm or *No* to cancel.\n"
                "| ✅ Yes / Ha / Haan  |  ❌ No / Na / Nahi |"
            )

    # 2. User is sending a brand new message
    else:
        parsed = await ai_parser(msg)

        if parsed.get("missing_fields"):
            # Don't store session — ask user to resend with complete info
            twiml_msg.body(parsed["confirmation_message"])

        elif parsed["intent"] == "unknown" or not parsed["target_sheet"]:
            twiml_msg.body(parsed["confirmation_message"])

        else:
            # Store session waiting for user's YES/NO
            user_sessions[sender] = {
                "state":          "pending",
                "language":       parsed["language"],
                "intent":         parsed["intent"],
                "target_sheet":   parsed["target_sheet"],
                "extracted_data": parsed["extracted_data"],
            }
            twiml_msg.body(parsed["confirmation_message"])

    return Response(content=str(resp), media_type="application/xml")

@app.get("/health")
def health():
    return {"status": "ok", "service": "Rajratan Enterprises Bot"}