from dotenv import load_dotenv
load_dotenv()
import os, re
from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

app = FastAPI(title="Rajratan Enterprises - WhatsApp Bot")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS_FILE = os.getenv("GOOGLE_CREDS_JSON", "credentials.json")
SHEET_ID  = os.getenv("GOOGLE_SHEET_ID", "YOUR_SHEET_ID")

def get_sheet(sheet_name: str):
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc    = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID).worksheet(sheet_name)

user_sessions: dict = {}

AFFIRMATIVE = {"yes","ha","haan","han","हाँ","हा","ہاں","ok","okay","confirm","हां","ho","ho jay"}
NEGATIVE    = {"no","na","nahi","naa","नहीं","ना","نہیں","cancel","nope","band karo"}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _has_word(msg: str, *words) -> bool:
    return any(re.search(rf"\b{re.escape(w)}\b", msg) for w in words)

def _first_number(msg: str) -> float:
    """Return the first standalone number found (ignores 60mm-style combos)."""
    m = re.search(r"(?<![a-z])(\d[\d,]*\.?\d*)(?!\s*mm\b)", msg)
    if m:
        return float(m.group(1).replace(",", ""))
    return 0.0

def _all_numbers(msg: str) -> list[float]:
    """All standalone numbers, stripping commas and ignoring NNmm patterns."""
    return [
        float(n.replace(",", ""))
        for n in re.findall(r"(?<![a-z])(\d[\d,]*\.?\d*)(?!\s*mm\b)", msg)
    ]

def _extract_rate(msg: str) -> float:
    """
    Try explicit 'rate X' pattern first, then fall back to the LAST number
    (rates are almost always mentioned after quantities in trade messages).
    """
    m = re.search(
        r"(?:rate|bhav|bhav chhe|ke rate|ke hisaab|per ton|per bag|lagayo)\s*[:\-]?\s*"
        r"(?:rs\.?|rupee|inr|₹)?\s*(\d[\d,]*\.?\d*)",
        msg,
    )
    if m:
        return float(m.group(1).replace(",", ""))
    nums = _all_numbers(msg)
    return nums[-1] if len(nums) >= 2 else 0.0   # last num = rate when 2+ nums present

def _extract_qty(msg: str) -> float:
    """First standalone number = quantity."""
    return _first_number(msg)

def _extract_client(msg: str) -> str:
    patterns = [
        r"(?:to|ko|ne|thi|from)\s+([A-Za-z][A-Za-z\s]{2,30?)(?:\s+at|\s+ke|\s+no|\s+na|\s+,|$)",
        r"(?:client|party|customer|traders?|builders?|enterprises?)\s*[:\-]?\s*([A-Za-z][A-Za-z\s]{2,25})",
    ]
    for p in patterns:
        m = re.search(p, msg, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            # strip trailing noise words
            name = re.sub(r"\s*(ko|ne|thi|to|at|ke|no|na)\s*$", "", name, flags=re.IGNORECASE)
            if len(name) > 2:
                return name.title()
    return "Unknown"

def _extract_block_qty(msg: str) -> float:
    """
    For production: look for the number that comes BEFORE 'block/blocks/60mm'.
    Falls back to first number.
    """
    m = re.search(r"(\d[\d,]*)\s*(?:60mm|80mm|40mm|paver|block)", msg, re.IGNORECASE)
    if m:
        return float(m.group(1).replace(",", ""))
    return _first_number(msg)

def _stock_fields(msg: str):
    op_m = re.search(r"\bopening\s*[:\-]?\s*(?P<n>[\d,]+)", msg)
    ni_m = re.search(r"\b(?:new|purchase|kharida|aavyu|liya)\s*[:\-]?\s*(?P<n>[\d,]+)", msg)
    sl_m = re.search(r"\b(?:sales?|sold|out|bheja|diya|aapiyu)\s*[:\-]?\s*(?P<n>[\d,]+)", msg)
    op = int(op_m.group("n").replace(",","")) if op_m else 0
    ni = int(ni_m.group("n").replace(",","")) if ni_m else 0
    sl = int(sl_m.group("n").replace(",","")) if sl_m else 0
    return op, ni, sl

def _detect_language(msg: str) -> str:
    if re.search(r"[\u0900-\u097F]", msg):   return "hi"
    if re.search(r"[\u0A80-\u0AFF]", msg):   return "gu"
    gu_words = {"chhe","aapiyu","aavyu","banavya","aaje","bhav","paghar","aapiya","thi"}
    hi_words = {"aaj","kal","kiya","diya","bheja","liya","maal","banaye","rupaye","hisaab"}
    tokens   = set(msg.lower().split())
    if tokens & gu_words: return "gu"
    if tokens & hi_words: return "hi"
    return "en"

def _missing_field_message(field: str, lang: str) -> str:
    msgs = {
        "rate": {
            "en": "⚠️ I got the quantity but couldn't find the *rate/price*. Please reply with the rate (e.g. 'Rate 800').",
            "hi": "⚠️ मात्रा मिली पर *रेट* नहीं मिला। कृपया रेट बताएं (जैसे 'Rate 800')।",
            "gu": "⚠️ Qty મળ્યો પણ *ભાવ* ન મળ્યો. કૃપા કરીને ભાવ જણાવો (દા.ત. 'Rate 800').",
        },
        "qty": {
            "en": "⚠️ I couldn't find the *quantity*. Please reply with qty (e.g. '50 brass').",
            "hi": "⚠️ *मात्रा* नहीं मिली। कृपया मात्रा बताएं (जैसे '50 brass')।",
            "gu": "⚠️ *Qty* ન મળ્યો. કૃપા કરીને qty જણાવો (દા.ત. '50 brass').",
        },
    }
    return msgs.get(field, {}).get(lang, msgs[field]["en"])

# ─── Parser ───────────────────────────────────────────────────────────────────

def simulated_llm_parser(message: str) -> dict:
    msg  = message.lower().strip()
    lang = _detect_language(msg)
    today = datetime.today().strftime("%Y-%m-%d")

    # keyword sets
    CLIENT_KW     = {"client","order","brass","delivery","party","customer","traders","builders",
                     "sold","sell","dispatch","dispatched","bheja","maal bheja","aapiyu",
                     "maal","supply","supplied"}
    PRODUCTION_KW = {"production","batch","manufactured","banaye","banaya","banavya","banavu",
                     "factory","blocks made","block banaye","block banavya","block bana"}
    CEMENT_KW     = {"cement","bag","sement","bags"}
    CHEMICAL_KW   = {"chemical","powder","greet","greut","admix","grit","chemicals"}
    PURCHASE_KW   = {"bought","purchase","kharida","aavyu","liya","mangaya","order kiya",
                     "purchase kiya","kharidya"}
    LABOUR_KW     = {"labour","worker","salary","wages","majoor","paghar","mazdoor"}
    CASH_IN_KW    = {"received","receive","aavya","aavyu","bheje","mile","income","advance",
                     "payment received","aaya paisa"}
    CASH_OUT_KW   = {"paid","diya","aapiya","expense","diesel","repair","repairing","kharch",
                     "kharcha","aapi didho","diye","cash diye","unloading"}
    CASHFLOW_KW   = CASH_IN_KW | CASH_OUT_KW | {"cash","payment","fund"}
    BLOCK_KW      = {"block","paving","blocks","60mm","80mm","paver","pavers"}

    tokens = set(msg.split())

    # ── helper: does msg contain words from a set? ────────────────────────────
    def has(*kw_sets):
        combined = set().union(*kw_sets)
        return bool(tokens & combined) or any(k in msg for k in combined if " " in k)

    # ── 1. Daily Block Production ─────────────────────────────────────────────
    # Must check BEFORE client-order because "block" appears in both.
    # Production = block keyword + manufacturing verb, NO client/sale verb.
    is_production = has(PRODUCTION_KW) or (
        has(BLOCK_KW) and not has(CLIENT_KW - BLOCK_KW) and not has(CASH_OUT_KW)
    )
    is_sale_of_blocks = has(CLIENT_KW) and has(BLOCK_KW)

    if is_production and not is_sale_of_blocks:
        qty_val = _extract_block_qty(msg)
        block_type_m = re.search(r"(\d+\s*mm|paver|paving)", msg, re.IGNORECASE)
        block_type   = block_type_m.group(1).upper() if block_type_m else "Standard"
        return {
            "language": lang,
            "intent":   "add_production",
            "target_sheet": "Block_Stocks",
            "extracted_data": {
                "Date": today,
                "New_Stock": qty_val,
                "Block_Type": block_type,
                "Note": message,
            },
            "confirmation_message": (
                f"🏭 *Block Production*\n"
                f"Qty: {int(qty_val)} blocks ({block_type})\n\n"
                f"Confirm? Reply *Yes* / *No*"
            ),
            "missing_fields": [],
        }

    # ── 2. Block / Paving Stock (opening-new-sales format) ───────────────────
    if has(BLOCK_KW) and re.search(r"\bopening\b", msg):
        op, ni, sl = _stock_fields(msg)
        total   = op + ni
        closing = total - sl
        return {
            "language": lang,
            "intent":   "update_block_stock",
            "target_sheet": "Block_Stocks",
            "extracted_data": {
                "Date": today, "Opening": op, "New_In": ni,
                "Total": total, "Sales": sl, "Closing": closing,
            },
            "confirmation_message": (
                f"📦 *Block Stock Update*\n"
                f"Opening: {op} | New: {ni}\n"
                f"Total: {total} | Sales: {sl}\n"
                f"Closing: {closing}\n\nConfirm? Reply *Yes* / *No*"
            ),
            "missing_fields": [],
        }

    # ── 3. Cement stock / purchase ────────────────────────────────────────────
    if has(CEMENT_KW):
        if re.search(r"\bopening\b", msg):
            op, ni, sl = _stock_fields(msg)
            total   = op + ni
            closing = total - sl
            return {
                "language": lang,
                "intent":   "update_cement_stock",
                "target_sheet": "Cement_Stocks",
                "extracted_data": {
                    "Date": today, "Opening": op, "New_In": ni,
                    "Total": total, "Sales": sl, "Closing": closing,
                },
                "confirmation_message": (
                    f"🏗️ *Cement Stock Update*\n"
                    f"Opening: {op} | New: {ni}\n"
                    f"Total: {total} | Sales: {sl}\n"
                    f"Closing: {closing}\n\nConfirm? Reply *Yes* / *No*"
                ),
                "missing_fields": [],
            }
        else:
            # Purchase entry
            qty_val  = _extract_qty(msg)
            rate_val = _extract_rate(msg)
            missing  = []
            if rate_val == 0.0: missing.append("rate")
            return {
                "language": lang,
                "intent":   "add_cement_purchase",
                "target_sheet": "Cement_Stocks",
                "extracted_data": {
                    "Date": today,
                    "New_In": qty_val,
                    "Rate_INR": rate_val,
                    "Amount_INR": round(qty_val * rate_val, 2),
                    "Note": message,
                },
                "confirmation_message": (
                    f"🏗️ *Cement Purchase*\n"
                    f"Qty: {qty_val} tons/bags\n"
                    f"Rate: ₹{rate_val}\n"
                    f"Amount: ₹{round(qty_val * rate_val, 2)}\n\n"
                    f"Confirm? Reply *Yes* / *No*"
                ) if not missing else _missing_field_message("rate", lang),
                "missing_fields": missing,
            }

    # ── 4. Chemical / Grit / Powder purchase ─────────────────────────────────
    if has(CHEMICAL_KW) or (has(PURCHASE_KW) and not has(CEMENT_KW | CLIENT_KW)):
        qty_val  = _extract_qty(msg)
        rate_val = _extract_rate(msg)
        item_m   = re.search(
            r"\b(?:chemical|powder|admix|greut|greet|grit)\s*[:\-]?\s*(?P<name>[a-z0-9 ]+)?",
            msg,
        )
        item_name = (
            item_m.group("name").strip().title()
            if (item_m and item_m.group("name")) else "Material"
        )
        missing = []
        if rate_val == 0.0: missing.append("rate")
        return {
            "language": lang,
            "intent":   "add_chemical_entry",
            "target_sheet": "Greet_Powder_Chemical",
            "extracted_data": {
                "Date": today, "Item_Name": item_name,
                "Qty_Ton": qty_val, "Rate_INR": rate_val,
                "Amount_INR": round(qty_val * rate_val, 2),
            },
            "confirmation_message": (
                f"🧪 *Material Purchase*\n"
                f"Item: {item_name}\n"
                f"Qty: {qty_val} ton\n"
                f"Rate: ₹{rate_val}\n"
                f"Amount: ₹{round(qty_val * rate_val, 2)}\n\n"
                f"Confirm? Reply *Yes* / *No*"
            ) if not missing else _missing_field_message("rate", lang),
            "missing_fields": missing,
        }

    # ── 5. Client Order / Sale (brass or blocks) ──────────────────────────────
    if has(CLIENT_KW):
        qty_val    = _extract_qty(msg)
        rate_val   = _extract_rate(msg)
        client_val = _extract_client(message)   # use original case
        missing    = []
        if rate_val == 0.0:
            missing.append("rate")
        if qty_val == 0.0:
            missing.append("qty")

        if missing:
            return {
                "language": lang,
                "intent":   "add_client_order",
                "target_sheet": "Clients",
                "extracted_data": {},
                "confirmation_message": _missing_field_message(missing[0], lang),
                "missing_fields": missing,
            }

        total_val = round(qty_val * rate_val, 2)
        return {
            "language": lang,
            "intent":   "add_client_order",
            "target_sheet": "Clients",
            "extracted_data": {
                "Date": today, "Client_Name": client_val,
                "Qty_Brass": qty_val, "Rate_INR": rate_val,
                "Total_INR": total_val, "Notes": message,
            },
            "confirmation_message": (
                f"📋 *Client Order / Sale*\n"
                f"Client: {client_val}\n"
                f"Qty: {qty_val} | Rate: ₹{rate_val}\n"
                f"Total: ₹{total_val}\n\n"
                f"Confirm? Reply *Yes* / *No*"
            ),
            "missing_fields": [],
        }

    # ── 6. Labour / Salary ────────────────────────────────────────────────────
    if has(LABOUR_KW):
        name_m = re.search(
            r"\b(?:name|worker|labour|majoor|manager)\s*[:\-]?\s*(?P<name>[a-z ]+)", msg
        )
        amount_val  = _first_number(msg)
        worker_name = name_m.group("name").strip().title() if name_m else "Worker"
        return {
            "language": lang,
            "intent":   "add_labour_salary",
            "target_sheet": "Labour_Salary",
            "extracted_data": {
                "Date": today, "Worker_Name": worker_name,
                "Amount_INR": amount_val, "Notes": message,
            },
            "confirmation_message": (
                f"👷 *Labour Salary*\n"
                f"Worker: {worker_name}\n"
                f"Amount: ₹{amount_val}\n\n"
                f"Confirm? Reply *Yes* / *No*"
            ),
            "missing_fields": [],
        }

    # ── 7. Cashflow ───────────────────────────────────────────────────────────
    if has(CASHFLOW_KW):
        amount_val = _first_number(msg)
        flow_type  = "IN" if has(CASH_IN_KW) else "OUT"
        # Extract payer/payee name for context
        party_m = re.search(
            r"(?:from|thi|se|ne|ko)\s+([A-Za-z][A-Za-z\s]{2,25})", message, re.IGNORECASE
        )
        party = party_m.group(1).strip().title() if party_m else ""
        desc  = f"{party} — " if party else ""
        return {
            "language": lang,
            "intent":   "add_cashflow",
            "target_sheet": "Cashflow",
            "extracted_data": {
                "Date": today, "Type": flow_type,
                "Amount_INR": amount_val,
                "Description": desc + message[:80],
            },
            "confirmation_message": (
                f"💰 *Cashflow*\n"
                f"Type: {'IN ⬆️' if flow_type=='IN' else 'OUT ⬇️'}\n"
                f"Amount: ₹{amount_val}\n"
                f"{f'Party: {party}' if party else ''}\n\n"
                f"Confirm? Reply *Yes* / *No*"
            ).strip(),
            "missing_fields": [],
        }

    # ── Fallback ──────────────────────────────────────────────────────────────
    return {
        "language": "en",
        "intent":   "unknown",
        "target_sheet": None,
        "extracted_data": {},
        "confirmation_message": (
            "❓ I couldn't understand your message.\n\n"
            "Try:\n"
            "• 'Sold 50 brass to Patel Traders rate 800'\n"
            "• 'Today made 1200 60mm blocks'\n"
            "• 'Bought 30 ton cement rate 5500'\n"
            "• 'Paid 15000 salary to labour manager'\n"
            "• 'Received 50000 from Sharma Builders'"
        ),
        "missing_fields": [],
    }

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
    """Adds new production qty to New_Stock column, recalculates Total."""
    ws       = get_sheet("Block_Stocks")
    all_vals = ws.get_all_values()
    if len(all_vals) > 1:
        last_row = all_vals[-1]
        headers  = all_vals[0]
        try:
            closing_idx  = headers.index("Closing")
            prev_closing = float(last_row[closing_idx]) if last_row[closing_idx] else 0.0
        except (ValueError, IndexError):
            prev_closing = 0.0
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

    if session and session.get("state") == "pending":
        normalized = msg.lower().strip()

        if normalized in AFFIRMATIVE:
            target = session["target_sheet"]
            data   = session["extracted_data"]
            intent = session.get("intent", "")
            try:
                if intent == "add_production":
                    write_production_to_block_stocks(data)
                elif target in ("Block_Stocks", "Cement_Stocks"):
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

    else:
        parsed = simulated_llm_parser(msg)

        # If missing fields — don't save, ask user to resend with full info
        if parsed.get("missing_fields"):
            twiml_msg.body(parsed["confirmation_message"])
            # Don't store session — user must resend complete message

        elif parsed["intent"] == "unknown" or not parsed["target_sheet"]:
            twiml_msg.body(parsed["confirmation_message"])

        else:
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