# 🏗️ Rajratan Enterprises — AI WhatsApp Business Manager

> An AI-powered business management system for a paver block manufacturing factory.  
> Manage stocks, sales, cashflow and labour — just by sending a WhatsApp message.  
> **Total deployment cost: ₹0**

---

## 📸 What It Does

My family runs **Rajratan Enterprises** — a paver block factory. Every day they manually recorded:
- Block production & stock
- Cement usage
- Client orders
- Labour payments
- Cash in/out

Now they just **WhatsApp it**. The AI agent handles everything.

```
User  → "Today made 3268 blocks"
Bot   → "🏭 Block Production
         New Stock: 3268 | Sales: 0
         Confirm? Yes / No"
User  → "Yes"
Bot   → "✅ Saved to Block_Stocks successfully!"
```

---

## 🤖 Features

- **Multilingual** — Understands Gujarati, Hindi & English naturally
- **Smart Parser** — Detects intent from casual messages (no commands needed)
- **Confirm before save** — Every entry is confirmed before writing to sheet
- **Auto Stock Continuity** — Row N Opening = Row N-1 Closing (auto-calculated)
- **Cement Logic** — Closing = Total - Use - External Sale
- **Live Dashboard** — Streamlit read-only dashboard with KPI cards & charts
- **Zero cost** — Railway (FastAPI) + Streamlit Cloud + Google Sheets

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Uvicorn |
| WhatsApp | Twilio WhatsApp API |
| Database | Google Sheets (gspread) |
| Dashboard | Streamlit + Plotly |
| Deployment | Railway (bot) + Streamlit Cloud (dashboard) |
| Language | Python 3.10+ |

---

## 📊 Supported Sheets & Logic

| Sheet | Logic |
|---|---|
| `Block_Stocks` | Opening(auto) + New Stock - Sales = Closing |
| `Cement_Stocks` | Opening(auto) + New Stock - Use - External Sale = Closing |
| `Clients` | Qty × Rate = Total INR |
| `Greet_Powder_Chemical` | Qty(ton) × Rate = Amount INR |
| `Labour_Salary` | Date, Worker, Amount |
| `Cashflow` | Type (IN/OUT), Amount, Description |
| `Production_Notes` | Free-form notes |

---

## 💬 Example WhatsApp Commands

```
# Block Production
"Today made 3268 60mm blocks"
"Production 5198 blocks sales 2850"

# Cement Stock
"Cement used 37 bags today"
"Cement used 25 bags external 10"
"Bought 840 bags cement rate 350"

# Client Order
"Sold 50 brass to Patel Traders rate 800"

# Cashflow
"Received 50000 from Sharma Builders"
"Paid 12000 for diesel expense"

# Labour
"Paid salary to worker manager 15000"

# Set Base Stock (first time setup)
"Set block base stock 160136"
"Set cement base stock 56"
```

---

## 🚀 Local Setup

### 1. Clone & Install
```bash
git clone https://github.com/YOUR_USERNAME/rajratan-bot.git
cd rajratan-bot
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Google Sheets Setup
- Create a GCP project → Enable Google Sheets API
- Create a Service Account → Download `credentials.json`
- Share your Google Sheet with the service account email (Editor access)
- Create these tabs in your sheet:
  `Clients`, `Block_Stocks`, `Cement_Stocks`, `Greet_Powder_Chemical`, `Production_Notes`, `Labour_Salary`, `Cashflow`

### 3. Sheet Headers (Row 1)

**Block_Stocks:**
```
Date | Opening Stock | New Stock | Total | Sales | Closing Stock
```

**Cement_Stocks:**
```
Date | Opening Stock | New Stock | Total | Use | External Sale | Closing Stock
```

### 4. Environment Variables
Create a `.env` file:
```env
GOOGLE_SHEET_ID=your_google_sheet_id
GOOGLE_CREDS_JSON=credentials.json
```

### 5. Run Locally
```bash
# Terminal 1 — FastAPI bot
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Streamlit dashboard
streamlit run app.py

# Terminal 3 — ngrok tunnel for Twilio
ngrok http 8000
```

Set ngrok URL in Twilio → Messaging → Sandbox Settings:
```
https://your-ngrok-url.ngrok-free.app/whatsapp
```

---

## ☁️ Free Deployment

### FastAPI → Railway
1. Push code to GitHub
2. Connect repo on [railway.app](https://railway.app)
3. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables:
   - `GOOGLE_SHEET_ID`
   - `GOOGLE_CREDS_JSON_CONTENT` (paste full credentials.json content)
5. Generate domain → paste in Twilio webhook

### Streamlit Dashboard → Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect GitHub repo → select `app.py`
3. Add secrets:
```toml
GOOGLE_SHEET_ID = "your_sheet_id"
GOOGLE_CREDS_JSON_CONTENT = '''{ paste credentials.json content }'''
```

---

## 📁 Project Structure

```
rajratan-bot/
├── main.py              ← FastAPI WhatsApp bot
├── app.py               ← Streamlit dashboard
├── requirements.txt     ← Python dependencies
├── .env                 ← Local env variables (don't commit)
├── credentials.json     ← GCP service account (don't commit)
├── .gitignore
└── README.md
```

---

## 🔮 Roadmap

- [ ] Gemini AI integration for smarter NLP
- [ ] Daily auto-summary WhatsApp message every evening
- [ ] Streamlit Cloud public dashboard
- [ ] Multi-factory support
- [ ] PDF invoice generation

---

## 👤 Author

**Mithil Mohite (Dominic)**  
Associate Trainee — Data Analysis & QA @ Apexon  
AWS Certified Cloud Practitioner | AI/ML Enthusiast  

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://linkedin.com/in/YOUR_LINKEDIN)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-black)](https://github.com/YOUR_USERNAME)

---

## 📄 License

MIT License — free to use, modify and build upon.

---

> *"Built for my family. Useful for every Indian manufacturer."* 🇮🇳
