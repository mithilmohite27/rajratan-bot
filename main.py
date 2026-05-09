import os, json, re
from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

app = FastAPI(title="Rajratan Enterprises - WhatsApp Bot")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS_FILE = os.getenv("GOOGLE_CREDS_JSON", "credentials.json")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "YOUR_SHEET_ID")

def get_sheet(sheet_name: str):
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    return sh.worksheet(sheet_name)

user_sessions: dict = {}

AFFIRMATIVE = {"yes", "ha", "haan", "han", "हाँ", "हा", "ہاں", "ok", "okay", "confirm", "हां"}
NEGATIVE = {"no", "na", "nahi", "naa", "नहीं", "ना", "نہیں", "cancel", "nope"}

# ─── Simulated LLM Parser ────────────────────────────────────────────────────

def simulated_llm_parser(message: str) -> dict:
    msg = message.lower().strip()

    if any(k in msg for k in ["client", "order", "brass", "delivery", "sale"]):
        qty = re.search(r"(\d+\.?\d*)\s*(brass|unit|qty|quantity)?", msg)
        rate = re.search(r"rate\s*[:\-]?\s*(\d+\.?\d*)", msg)
        client = re.search(r"(client|party|customer)\s*[:\-]?\s*([a-z\s]+)", msg)
        qty_val = float(qty.group(1)) if qty else 0.0
        rate_val = float(rate.group(1)) if rate else 0.0
        client_val = client.group(2).strip().title() if client else "Unknown"
        return {
            "language": "en",
            "intent": "add_client_order",
            "target_sheet": "Clients",
            "extracted_data": {
                "Date": datetime.today().strftime("%Y-%m-%d"),
                "Client_Name": client_val,
                "Qty_Brass": qty_val,
                "Rate_INR": rate_val,
                "Total_INR": round(qty_val * rate_val, 2),
                "Notes": message,
            },
            "confirmation_message": (
                f"📋 *New Client Order*\n"
                f"Client: {client_val}\n"
                f"Qty: {qty_val} Brass\n"
                f"Rate: ₹{rate_val}\n"
                f"Total: ₹{round(qty_val * rate_val, 2)}\n\n"
                f"Confirm? Reply *Yes* / *No*"
            ),
        }

    if any(k in msg for k in ["block", "paving", "stock", "blocks"]):
        opening = re.search(r"opening\s*[:\-]?\s*(\d+)", msg)
        new_in = re.search(r"(new|purchase|in)\s*[:\-]?\s*(\d+)", msg)
        sales = re.search(r"(sale|sold|out)\s*[:\-]?\s*(\d+)", msg)
        op = int(opening.group(1)) if opening else 0
        ni = int(new_in.group(2)) if new_in else 0
        sl = int(sales.group(2)) if sales else 0
        total = op + ni
        closing = total - sl
        return {
            "language": "en",
            "intent": "update_block_stock",
            "target_sheet": "Block_Stocks",
            "extracted_data": {
                "Date": datetime.today().strftime("%Y-%m-%d"),
                "Opening": op,
                "New_In": ni,
                "Total": total,
                "Sales": sl,
                "Closing": closing,
            },
            "confirmation_message": (
                f"📦 *Block Stock Update*\n"
                f"Opening: {op} | New: {ni}\n"
                f"Total: {total} | Sales: {sl}\n"
                f"Closing: {closing}\n\n"
                f"Confirm? Reply *Yes* / *No*"
            ),
        }

    if any(k in msg for k in ["cement", "bag", "sement"]):
        opening = re.search(r"opening\s*[:\-]?\s*(\d+)", msg)
        new_in = re.search(r"(new|purchase|in)\s*[:\-]?\s*(\d+)", msg)
        sales = re.search(r"(sale|sold|out)\s*[:\-]?\s*(\d+)", msg)
        op = int(opening.group(1)) if opening else 0
        ni = int(new_in.group(2)) if new_in else 0
        sl = int(sales.group(2)) if sales else 0
        total = op + ni
        closing = total - sl
        return {
            "language": "gu",
            "intent": "update_cement_stock",
            "target_sheet": "Cement_Stocks",
            "extracted_data": {
                "Date": datetime.today().strftime("%Y-%m-%d"),
                "Opening": op,
                "New_In": ni,
                "Total": total,
                "Sales": sl,
                "Closing": closing,
            },
            "confirmation_message": (
                f"🏗️ *સિમેન્ટ સ્ટોક અપડેટ*\n"
                f"ઓપનિંગ: {op} | નવો: {ni}\n"
                f"કુલ: {total} | વેચાણ: {sl}\n"
                f"ક્લોઝિંગ: {closing}\n\n"
                f"કન્ફર્મ કરો? *Ha* / *Na* જવાબ આપો"
            ),
        }

    if any(k in msg for k in ["chemical", "powder", "greet", "greut", "admix"]):
        qty = re.search(r"(\d+\.?\d*)\s*(ton|tonne|kg)?", msg)
        rate = re.search(r"rate\s*[:\-]?\s*(\d+\.?\d*)", msg)
        item = re.search(r"(chemical|powder|admix|greut|greet)\s*[:\-]?\s*([a-z0-9\s]+)?", msg)
        qty_val = float(qty.group(1)) if qty else 0.0
        rate_val = float(rate.group(1)) if rate else 0.0
        item_name = item.group(2).strip().title() if (item and item.group(2)) else "Chemical"
        return {
            "language": "hi",
            "intent": "add_chemical_entry",
            "target_sheet": "Greet_Powder_Chemical",
            "extracted_data": {
                "Date": datetime.today().strftime("%Y-%m-%d"),
                "Item_Name": item_name,
                "Qty_Ton": qty_val,
                "Rate_INR": rate_val,
                "Amount_INR": round(qty_val * rate_val, 2),
            },
            "confirmation_message": (
                f"🧪 *केमिकल/पाउडर एंट्री*\n"
                f"सामान: {item_name}\n"
                f"मात्रा: {qty_val} टन\n"
                f"रेट: ₹{rate_val}\n"
                f"राशि: ₹{round(qty_val * rate_val, 2)}\n\n"
                f"कन्फर्म करें? *Haan* / *Nahi* लिखें"
            ),
        }

    if any(k in msg for k in ["labour", "worker", "salary", "wages", "majoor"]):
        name = re.search(r"(name|worker|labour|majoor)\s*[:\-]?\s*([a-z\s]+)", msg)
        amount = re.search(r"(\d+\.?\d*)\s*(rs|rupee|inr|₹)?", msg)
        worker_name = name.group(2).strip().title() if name else "Worker"
        amount_val = float(amount.group(1)) if amount else 0.0
        return {
            "language": "en",
            "intent": "add_labour_salary",
            "target_sheet": "Labour_Salary",
            "extracted_data": {
                "Date": datetime.today().strftime("%Y-%m-%d"),
                "Worker_Name": worker_name,
                "Amount_INR": amount_val,
                "Notes": message,
            },
            "confirmation_message": (
                f"👷 *Labour Salary Entry*\n"
                f"Worker: {worker_name}\n"
                f"Amount: ₹{amount_val}\n\n"
                f"Confirm? Reply *Yes* / *No*"
            ),
        }

    if any(k in msg for k in ["cash", "payment", "expense", "receive", "paid", "fund"]):
        amount = re.search(r"(\d+\.?\d*)\s*(rs|rupee|inr|₹)?", msg)
        flow_type = "IN" if any(k in msg for k in ["receive", "received", "income", "in"]) else "OUT"
        amount_val = float(amount.group(1)) if amount else 0.0
        return {
            "language": "en",
            "intent": "add_cashflow",
            "target_sheet": "Cashflow",
            "extracted_data": {
                "Date": datetime.today().strftime("%Y-%m-%d"),
                "Type": flow_type,
                "Amount_INR": amount_val,
                "Description": message,
            },
            "confirmation_message": (
                f"💰 *Cashflow Entry*\n"
                f"Type: {flow_type}\n"
                f"Amount: ₹{amount_val}\n"
                f"Description: {message[:80]}\n\n"
                f"Confirm? Reply *Yes* / *No*"
            ),
        }

    if any(k in msg for k in ["production", "batch", "made", "manufactured", "banaya", "banavu"]):
        return {
            "language": "en",
            "intent": "add_production_note",
            "target_sheet": "Production_Notes",
            "extracted_data": {
                "Date": datetime.today().strftime("%Y-%m-%d"),
                "Note": message,
                "Recorded_By": "WhatsApp",
            },
            "confirmation_message": (
                f"🏭 *Production Note*\n{message}\n\n"
                f"Save this note? Reply *Yes* / *No*"
            ),
        }

    return {
        "language": "en",
        "intent": "unknown",
        "target_sheet": None,
        "extracted_data": {},
        "confirmation_message": (
            "❓ I couldn't understand your message.\n\n"
            "Try: 'Client order 50 brass rate 800'\n"
            "Or: 'Cement stock opening 200 new 100 sales 50'\n"
            "Or: 'Chemical lime powder 2 ton rate 15000'"
        ),
    }

# ─── Sheet Writers ────────────────────────────────────────────────────────────

def write_to_sheet(target_sheet: str, data: dict):
    ws = get_sheet(target_sheet)
    headers = ws.row_values(1)
    if not headers:
        headers = list(data.keys())
        ws.append_row(headers)
    row = [data.get(h, "") for h in headers]
    ws.append_row(row)

def write_stocks_with_continuity(sheet_name: str, data: dict):
    ws = get_sheet(sheet_name)
    all_vals = ws.get_all_values()
    if len(all_vals) > 1:
        last_row = all_vals[-1]
        headers = all_vals[0]
        try:
            closing_idx = headers.index("Closing")
            prev_closing = float(last_row[closing_idx]) if last_row[closing_idx] else 0
            data["Opening"] = prev_closing
            ni = float(data.get("New_In", 0))
            sl = float(data.get("Sales", 0))
            data["Total"] = prev_closing + ni
            data["Closing"] = prev_closing + ni - sl
        except (ValueError, IndexError):
            pass
    write_to_sheet(sheet_name, data)

# ─── Webhook ──────────────────────────────────────────────────────────────────

@app.post("/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
):
    sender = From.strip()
    msg = Body.strip()
    resp = MessagingResponse()
    twiml_msg = resp.message()

    session = user_sessions.get(sender)

    if session and session.get("state") == "pending":
        normalized = msg.lower().strip()
        if normalized in AFFIRMATIVE:
            target = session["target_sheet"]
            data = session["extracted_data"]
            try:
                if target in ("Block_Stocks", "Cement_Stocks"):
                    write_stocks_with_continuity(target, data)
                else:
                    write_to_sheet(target, data)
                lang = session.get("language", "en")
                success_msgs = {
                    "en": f"✅ Data saved to *{target}* successfully!",
                    "gu": f"✅ ડેટા *{target}* માં સફળતાપૂર્વક સેવ થયો!",
                    "hi": f"✅ डेटा *{target}* में सफलतापूर्वक सेव हो गया!",
                }
                twiml_msg.body(success_msgs.get(lang, success_msgs["en"]))
            except Exception as e:
                twiml_msg.body(f"❌ Error saving data: {str(e)}\nPlease try again.")
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

    else:
        parsed = simulated_llm_parser(msg)
        if parsed["intent"] == "unknown" or not parsed["target_sheet"]:
            twiml_msg.body(parsed["confirmation_message"])
        else:
            user_sessions[sender] = {
                "state": "pending",
                "language": parsed["language"],
                "target_sheet": parsed["target_sheet"],
                "extracted_data": parsed["extracted_data"],
            }
            twiml_msg.body(parsed["confirmation_message"])

    return Response(content=str(resp), media_type="application/xml")

@app.get("/health")
def health():
    return {"status": "ok", "service": "Rajratan Enterprises Bot"}