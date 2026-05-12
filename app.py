from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
import os, json
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Rajratan Enterprises",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design Tokens ─────────────────────────────────────────────────────────────
S = {
    "bg":         "#080b10",
    "surface":    "#0e1117",
    "card":       "#111520",
    "border":     "#1a2035",
    "borderHover":"#253050",
    "text":       "#e8eaf0",
    "muted":      "#4a5272",
    "accent":     "#00d4aa",
    "accentDim":  "rgba(0,212,170,0.1)",
    "amber":      "#f59e0b",
    "amberDim":   "rgba(245,158,11,0.1)",
    "red":        "#f45b6b",
    "redDim":     "rgba(244,91,107,0.1)",
    "blue":       "#4f6ef7",
    "blueDim":    "rgba(79,110,247,0.1)",
    "purple":     "#a78bfa",
    "chartGrid":  "#151c2e",
}

PIE_COLORS = ["#00d4aa", "#f59e0b", "#4f6ef7", "#f45b6b", "#a78bfa", "#06b6d4"]

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif !important;
    background-color: {S['bg']} !important;
    color: {S['text']} !important;
}}
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.stMainBlockContainer,
section.main > div {{
    background-color: {S['bg']} !important;
}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background: {S['surface']} !important;
    border-right: 1px solid {S['border']} !important;
    min-width: 240px !important;
    max-width: 240px !important;
}}
section[data-testid="stSidebar"] * {{ color: {S['muted']} !important; font-family: 'DM Sans', sans-serif !important; }}
section[data-testid="stSidebar"] .stRadio > div {{ gap: 2px !important; }}
section[data-testid="stSidebar"] .stRadio label {{
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    padding: 10px 12px !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
    border-left: 2px solid transparent !important;
    color: {S['muted']} !important;
    width: 100% !important;
}}
section[data-testid="stSidebar"] .stRadio label:hover {{
    background: rgba(0,212,170,0.06) !important;
    color: {S['text']} !important;
}}
section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] > div:first-child {{ display: none !important; }}
div[data-testid="stMarkdownContainer"] p {{ color: {S['muted']} !important; }}

/* ── Main area ── */
.main .block-container {{
    background: {S['bg']} !important;
    padding: 32px 36px !important;
    max-width: 1400px !important;
}}

/* Hide streamlit chrome */
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

/* ── Metric cards ── */
.metric-card {{
    background: {S['card']};
    border: 1px solid {S['border']};
    border-radius: 14px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s, transform 0.15s;
    height: 100%;
    min-height: 110px;
}}
.metric-card:hover {{
    border-color: {S['borderHover']};
    transform: translateY(-1px);
}}
.metric-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent, {S['accent']}), transparent);
}}
.metric-label {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: {S['muted']} !important;
    margin-bottom: 12px;
}}
.metric-value {{
    font-size: 26px;
    font-weight: 600;
    color: {S['text']} !important;
    font-family: 'JetBrains Mono', monospace !important;
    line-height: 1;
    margin-bottom: 8px;
}}
.metric-sub {{
    font-size: 11px;
    color: {S['muted']} !important;
}}
.metric-change-pos {{
    font-size: 11px;
    color: {S['accent']} !important;
    background: {S['accentDim']};
    padding: 2px 7px;
    border-radius: 20px;
    font-weight: 600;
    display: inline-block;
    margin-left: 8px;
}}
.metric-change-neg {{
    font-size: 11px;
    color: {S['red']} !important;
    background: {S['redDim']};
    padding: 2px 7px;
    border-radius: 20px;
    font-weight: 600;
    display: inline-block;
    margin-left: 8px;
}}

/* ── Section label ── */
.section-label {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 28px 0 16px;
}}
.section-label span {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: {S['muted']} !important;
    white-space: nowrap;
}}
.section-label::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: {S['border']};
}}

/* ── Page titles ── */
.page-title {{
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 28px;
    font-weight: 700;
    color: {S['text']} !important;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
}}
.page-sub {{
    font-size: 13px;
    color: {S['muted']} !important;
    margin-bottom: 24px;
}}

/* ── Brand block ── */
.brand-wrap {{
    padding: 24px 20px 16px;
    border-bottom: 1px solid {S['border']};
    margin-bottom: 12px;
}}
.brand-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
}}
.brand-icon {{
    width: 32px; height: 32px;
    border-radius: 8px;
    background: linear-gradient(135deg, {S['accent']}, #00a07e);
    display: flex; align-items: center; justify-content: center;
    font-family: 'Rajdhani', sans-serif;
    font-weight: 700; font-size: 16px;
    color: #000; flex-shrink: 0;
}}
.brand-name {{
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700;
    font-size: 18px;
    color: {S['text']} !important;
    line-height: 1;
}}
.brand-sub-text {{
    font-size: 10px;
    color: {S['muted']} !important;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}}
.status-box {{
    background: {S['bg']};
    border: 1px solid {S['border']};
    border-radius: 8px;
    padding: 10px 12px;
}}
.status-time {{
    font-size: 11px;
    color: {S['accent']} !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 500;
}}
.status-dot {{
    width: 6px; height: 6px;
    border-radius: 50%;
    background: {S['accent']};
    display: inline-block;
    margin-right: 4px;
    animation: pulse 2s infinite;
}}
@keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.4; }} }}

/* ── Status strip ── */
.status-strip {{
    display: flex;
    gap: 8px;
    margin-bottom: 24px;
    flex-wrap: wrap;
}}
.status-pill {{
    display: flex;
    align-items: center;
    gap: 6px;
    background: {S['card']};
    border: 1px solid {S['border']};
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 11px;
}}
.status-pill-dot {{
    width: 5px; height: 5px;
    border-radius: 50%;
    display: inline-block;
    animation: pulse 2s infinite;
}}
.status-pill-label {{ color: {S['muted']} !important; }}
.status-pill-val {{ font-weight: 600; }}

/* ── Badges ── */
.badge {{
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    padding: 3px 10px;
    border-radius: 20px;
}}
.badge-green {{ background: rgba(0,212,170,0.12); color: #00d4aa !important; border: 1px solid rgba(0,212,170,0.25); }}
.badge-red   {{ background: rgba(244,91,107,0.12); color: #f45b6b !important; border: 1px solid rgba(244,91,107,0.25); }}
.badge-amber {{ background: rgba(245,158,11,0.12); color: #f59e0b !important; border: 1px solid rgba(245,158,11,0.25); }}
.badge-blue  {{ background: rgba(79,110,247,0.12); color: #4f6ef7 !important; border: 1px solid rgba(79,110,247,0.25); }}
.badge-purple{{ background: rgba(167,139,250,0.12);color: #a78bfa !important; border: 1px solid rgba(167,139,250,0.25); }}

/* ── Tables ── */
.rtable {{ width: 100%; border-collapse: collapse; }}
.rtable th {{
    padding: 12px 20px;
    font-size: 10px;
    font-weight: 600;
    color: {S['muted']} !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    text-align: left;
    background: rgba(8,11,16,0.5);
}}
.rtable td {{
    padding: 12px 20px;
    font-size: 13px;
    color: {S['text']} !important;
    border-top: 1px solid {S['border']};
}}
.rtable tr:hover td {{ background: rgba(255,255,255,0.02); }}
.mono {{ font-family: 'JetBrains Mono', monospace !important; font-size: 12px; }}
.table-card {{
    background: {S['card']};
    border: 1px solid {S['border']};
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 20px;
}}
.table-header {{
    padding: 16px 20px 12px;
    border-bottom: 1px solid {S['border']};
    display: flex;
    align-items: center;
    justify-content: space-between;
}}
.table-header-label {{
    font-size: 12px;
    color: {S['muted']} !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* ── Utilization bar ── */
.util-wrap {{ display: flex; align-items: center; gap: 8px; }}
.util-bar-bg {{
    flex: 1; height: 4px;
    background: {S['border']};
    border-radius: 4px;
    overflow: hidden;
    min-width: 60px;
}}
.util-bar-fill {{ height: 100%; border-radius: 4px; }}
.util-val {{ font-size: 11px; color: {S['muted']} !important; font-family: 'JetBrains Mono', monospace; min-width: 36px; }}

/* ── Chart cards ── */
.chart-card {{
    background: {S['card']};
    border: 1px solid {S['border']};
    border-radius: 14px;
    padding: 20px 22px;
    transition: border-color 0.2s, transform 0.15s;
    margin-bottom: 16px;
}}
.chart-card:hover {{
    border-color: {S['borderHover']};
    transform: translateY(-1px);
}}
.chart-title {{
    font-size: 12px;
    color: {S['muted']} !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}}
.chart-legend {{
    display: flex;
    gap: 16px;
    margin-top: 8px;
}}
.legend-item {{
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    color: {S['muted']} !important;
}}
.legend-dot {{
    width: 10px; height: 10px;
    border-radius: 2px;
    display: inline-block;
}}

/* ── Tabs ── */
div[data-testid="stTabs"] button {{
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: {S['muted']} !important;
    background: none !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 10px 18px !important;
    transition: all 0.15s !important;
}}
div[data-testid="stTabs"] button:hover {{ color: {S['text']} !important; }}
div[data-testid="stTabs"] button[aria-selected="true"] {{
    color: {S['accent']} !important;
    border-bottom: 2px solid {S['accent']} !important;
}}
div[data-testid="stTabs"] [role="tablist"] {{
    border-bottom: 1px solid {S['border']} !important;
    gap: 0 !important;
}}

/* ── Buttons ── */
.stButton > button {{
    background: {S['surface']} !important;
    color: {S['muted']} !important;
    border: 1px solid {S['border']} !important;
    border-radius: 6px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
    padding: 6px 14px !important;
}}
.stButton > button:hover {{
    background: {S['card']} !important;
    color: {S['text']} !important;
    border-color: {S['borderHover']} !important;
}}

/* ── Search input ── */
.stTextInput input {{
    background: {S['card']} !important;
    border: 1px solid {S['border']} !important;
    border-radius: 10px !important;
    color: {S['text']} !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    padding: 10px 16px !important;
}}
.stTextInput input:focus {{
    border-color: {S['accent']} !important;
    box-shadow: 0 0 0 2px {S['accentDim']} !important;
}}
.stTextInput label {{ color: {S['muted']} !important; font-size: 11px !important; }}

/* ── Info / alerts ── */
.stAlert {{ border-radius: 10px !important; background: {S['card']} !important; border: 1px solid {S['border']} !important; }}
div[data-testid="stNotification"] {{ background: {S['card']} !important; }}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {S['border']}; border-radius: 4px; }}

/* ── Fade in ── */
@keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
.fade-in {{ animation: fadeIn 0.3s ease forwards; }}

/* ── Columns gap ── */
div[data-testid="column"] {{ padding: 0 6px !important; }}
div[data-testid="stHorizontalBlock"] {{ gap: 0 !important; }}
</style>
""", unsafe_allow_html=True)

# ── Formatters ─────────────────────────────────────────────────────────────────
def inr(v):
    try: return f"₹{float(v):,.0f}"
    except: return "₹0"

def compact(v):
    try:
        v = float(v)
        if v >= 100000: return f"₹{v/100000:.1f}L"
        if v >= 1000:   return f"₹{v/1000:.1f}K"
        return f"₹{v:.0f}"
    except: return "₹0"

def num_col(df, col):
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace("₹","",regex=False).str.replace(",","",regex=False).str.strip()
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

# ── Google Sheets ──────────────────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

@st.cache_resource(ttl=300)
def get_gc():
    creds_content = None
    try:    creds_content = st.secrets["GOOGLE_CREDS_JSON_CONTENT"]
    except: creds_content = os.getenv("GOOGLE_CREDS_JSON_CONTENT")
    if creds_content:
        creds = Credentials.from_service_account_info(
            json.loads(creds_content) if isinstance(creds_content, str) else creds_content,
            scopes=SCOPES
        )
    else:
        creds = Credentials.from_service_account_file(
            os.getenv("GOOGLE_CREDS_JSON", "credentials.json"), scopes=SCOPES
        )
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def load_sheet(name: str) -> pd.DataFrame:
    try:
        sheet_id = ""
        try:    sheet_id = st.secrets["GOOGLE_SHEET_ID"]
        except: sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
        gc = get_gc()
        ws = gc.open_by_key(sheet_id).worksheet(name)
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        # Normalize Date column: strip time, keep only date string
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d").fillna(df["Date"].astype(str))
        return df
    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"Sheet tab '{name}' not found.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading '{name}': {e}")
        return pd.DataFrame()

# ── Data prep helpers ──────────────────────────────────────────────────────────
def find_col(df, *candidates):
    """Return first matching column name from candidates (case-insensitive)."""
    lower_map = {c.lower().replace(" ","_"): c for c in df.columns}
    for cand in candidates:
        if cand in df.columns: return cand
        if cand.lower().replace(" ","_") in lower_map: return lower_map[cand.lower().replace(" ","_")]
    return None

def clean_num(df, col):
    """Remove ₹, commas, spaces then convert to float."""
    if col not in df.columns: return df
    df[col] = df[col].astype(str).str.replace("₹","",regex=False).str.replace(",","",regex=False).str.strip()
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

def prep_clients(df):
    if df.empty: return df
    # Rename Client_Name -> Name
    if "Client_Name" in df.columns: df.rename(columns={"Client_Name":"Name"}, inplace=True)
    for col in ["Qty_Brass","Rate_INR","Total_INR"]: df = clean_num(df, col)
    if "Total_INR" not in df.columns or df["Total_INR"].sum() == 0:
        if "Qty_Brass" in df.columns and "Rate_INR" in df.columns:
            df["Total_INR"] = df["Qty_Brass"] * df["Rate_INR"]
    return df

def prep_stocks(df, sheet_type="block"):
    if df.empty: return df
    # Exact column names from sheet
    # Block:  Opening Stock, New Stock, Total, Sales, Closing Stock
    # Cement: Opening Stock, New Stock, Total, Use, External Sale, Closing Stock
    renames = {
        "Opening Stock": "Opening",
        "New Stock":     "New_In",
        "Closing Stock": "Closing",
        "External Sale": "Sales",  # cement
        "Sales":         "Sales",  # block
        "Use":           "Internal_Use",
        "Total":         "Total",
    }
    df.rename(columns=renames, inplace=True)
    for col in ["Opening","New_In","Closing","Sales","Internal_Use","Total"]:
        if col in df.columns: df = num_col(df, col)
    # For cement, combine Use + External Sale as total sales
    if sheet_type == "cement":
        use = df["Internal_Use"] if "Internal_Use" in df.columns else 0
        sal = df["Sales"]        if "Sales"        in df.columns else 0
        df["Sales"] = use + sal if not isinstance(use, int) else sal
    return df

def prep_chemical(df):
    if df.empty: return df
    qty_c  = find_col(df, "Qty_Ton","Qty","qty","QTY","Quantity","qty_ton")
    rate_c = find_col(df, "Rate_INR","Rate","rate","RATE","Price","rate_inr")
    item_c = find_col(df, "Item_Name","Item","item","ITEM","Name","name","Material")
    amt_c  = find_col(df, "Amount_INR","Amount","amount","AMOUNT","Total","total")
    if qty_c  and qty_c  != "Qty_Ton":    df.rename(columns={qty_c:"Qty_Ton"},    inplace=True)
    if rate_c and rate_c != "Rate_INR":   df.rename(columns={rate_c:"Rate_INR"},  inplace=True)
    if item_c and item_c != "Item_Name":  df.rename(columns={item_c:"Item_Name"}, inplace=True)
    if amt_c  and amt_c  != "Amount_INR": df.rename(columns={amt_c:"Amount_INR"}, inplace=True)
    df = num_col(df, "Qty_Ton"); df = num_col(df, "Rate_INR")
    if "Qty_Ton" in df.columns and "Rate_INR" in df.columns and "Amount_INR" not in df.columns:
        df["Amount_INR"] = df["Qty_Ton"] * df["Rate_INR"]
    elif "Amount_INR" in df.columns:
        df = num_col(df, "Amount_INR")
    return df

def prep_cashflow(df):
    if df.empty: return df
    amt_c  = find_col(df, "Amount_INR","Amount","amount","AMOUNT","amount_inr","Value")
    type_c = find_col(df, "Type","type","TYPE","Flow_Type","flow_type","IN_OUT")
    if amt_c  and amt_c  != "Amount_INR": df.rename(columns={amt_c:"Amount_INR"},  inplace=True)
    if type_c and type_c != "Type":       df.rename(columns={type_c:"Type"},        inplace=True)
    df = num_col(df, "Amount_INR")
    return df

def prep_labour(df):
    if df.empty: return df
    # Exact columns: Date, Worker_Name, Amount_INR, Notes
    df = num_col(df, "Amount_INR")
    return df

# ── Chart theme ────────────────────────────────────────────────────────────────
def chart_layout(h=220):
    return dict(
        font_family="DM Sans",
        plot_bgcolor=S["card"],
        paper_bgcolor=S["card"],
        font_color=S["muted"],
        margin=dict(l=8, r=8, t=8, b=8),
        height=h,
        xaxis=dict(gridcolor=S["chartGrid"], showgrid=True, tickfont=dict(size=11, color=S["muted"]), showline=False, zeroline=False),
        yaxis=dict(gridcolor=S["chartGrid"], showgrid=True, tickfont=dict(size=11, color=S["muted"]), showline=False, zeroline=False),
        legend=dict(bgcolor=S["card"], bordercolor=S["border"], font=dict(size=11, color=S["muted"])),
        hoverlabel=dict(bgcolor=S["card"], bordercolor=S["border"], font=dict(size=12, color=S["text"])),
    )

def area_chart(x_vals, y_vals, name, color, y_fmt=None):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals, y=y_vals,
        mode="lines+markers",
        name=name,
        line=dict(color=color, width=2.5),
        marker=dict(size=4, color=color),
        fill="tozeroy",
        fillcolor=hex_to_rgba(color, 0.12),
    ))
    layout = chart_layout()
    if y_fmt:
        layout["yaxis"]["tickprefix"] = "₹"
    fig.update_layout(**layout)
    return fig

def hex_to_rgba(hex_color, alpha=0.1):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

def dual_area_chart(x_vals, y1, y2, n1, n2, c1, c2):
    fig = go.Figure()
    for y, n, c in [(y1,n1,c1),(y2,n2,c2)]:
        fig.add_trace(go.Scatter(
            x=x_vals, y=y, mode="lines+markers", name=n,
            line=dict(color=c, width=2),
            marker=dict(size=3, color=c),
            fill="tozeroy",
            fillcolor=hex_to_rgba(c, 0.12),
        ))
    fig.update_layout(yaxis_tickprefix="₹", **chart_layout())
    return fig

def bar_chart(x_vals, datasets, colors):
    fig = go.Figure()
    for (y, name), color in zip(datasets, colors):
        fig.add_trace(go.Bar(
            x=x_vals, y=y, name=name,
            marker_color=color, marker_line_width=0,
            marker_cornerradius=3,
        ))
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.05, **chart_layout())
    return fig

def h_bar_chart(y_vals, x_vals, color, h=220):
    fig = go.Figure(go.Bar(
        x=x_vals, y=y_vals, orientation="h",
        marker_color=color, marker_line_width=0,
        marker_cornerradius=3,
    ))
    fig.update_layout(xaxis_tickprefix="₹", **chart_layout(h=h))
    return fig

def pie_chart(labels, values, colors):
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker_colors=colors,
        hole=0.55,
        textfont_size=11,
        textfont_color=S["text"],
        showlegend=False,
    ))
    fig.update_layout(**chart_layout(h=200))
    return fig

# ── UI helpers ─────────────────────────────────────────────────────────────────
def metric_card(label, value, sub="", accent=None, change=None):
    accent = accent or S["accent"]
    change_html = ""
    if change:
        cls = "metric-change-pos" if not change.startswith("-") else "metric-change-neg"
        change_html = f'<span class="{cls}">{change}</span>'
    st.markdown(f"""
    <div class="metric-card" style="--accent:{accent}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub">{sub}{change_html}</div>
    </div>
    """, unsafe_allow_html=True)

def section_label(text):
    st.markdown(f'<div class="section-label"><span>{text}</span></div>', unsafe_allow_html=True)

def badge(text, btype="blue"):
    return f'<span class="badge badge-{btype}">{text}</span>'

def status_dot(status):
    m = {"Paid":"green","Pending":"red","Partial":"amber"}
    return badge(status, m.get(status,"blue"))

def util_bar(pct, color):
    bar_color = color if float(pct) > 50 else S["amber"]
    return f"""
    <div class="util-wrap">
        <div class="util-bar-bg">
            <div class="util-bar-fill" style="width:{min(float(pct),100)}%;background:{bar_color}"></div>
        </div>
        <span class="util-val">{pct}%</span>
    </div>"""

def chart_card(title, fig, legend_items=None):
    st.markdown(f'<div class="chart-card"><div class="chart-title">{title}</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    if legend_items:
        legend_html = '<div class="chart-legend">'
        for lbl, color in legend_items:
            legend_html += f'<span class="legend-item"><span class="legend-dot" style="background:{color}"></span>{lbl}</span>'
        legend_html += '</div>'
        st.markdown(legend_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def pie_legend(items):
    html = '<div style="display:flex;flex-direction:column;gap:6px;margin-top:8px">'
    for name, val, color in items:
        html += f'''
        <div style="display:flex;align-items:center;justify-content:space-between;font-size:11px">
            <span style="display:flex;align-items:center;gap:6px;color:{S['muted']}">
                <span style="width:8px;height:8px;border-radius:2px;background:{color};display:inline-block"></span>{name}
            </span>
            <span style="font-family:'JetBrains Mono',monospace;color:{S['text']};font-weight:500">{compact(val)}</span>
        </div>'''
    html += '</div>'
    return html

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    now = datetime.now()
    st.markdown(f"""
    <div class="brand-wrap">
        <div class="brand-row">
            <div class="brand-icon">R</div>
            <div>
                <div class="brand-name">Rajratan</div>
                <div class="brand-sub-text">Enterprises</div>
            </div>
        </div>
        <div class="status-box">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
                <span style="font-size:10px;color:{S['muted']};text-transform:uppercase;letter-spacing:1px">System</span>
                <span class="status-dot"></span>
            </div>
            <div class="status-time">{now.strftime('%H:%M:%S')}</div>
            <div style="font-size:10px;color:{S['muted']};margin-top:2px">Live · Auto-sync 5min</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<div style="font-size:10px;color:{S["muted"]};letter-spacing:1.2px;text-transform:uppercase;padding:0 8px;margin-bottom:8px">Navigation</div>', unsafe_allow_html=True)

    nav = st.radio("Navigation", [
        "⬡  Overview",
        "◧  Block & Cement",
        "◈  Clients & Materials",
        "◎  Financials",
    ], label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([3,1])
    with col1:
        if st.button("⟳  Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col2:
        st.button("⚙", use_container_width=True)

    with st.expander("🔍 Debug: Sheet Columns"):
        for sheet_name in ["Clients","Block_Stocks","Cement_Stocks","Cashflow","Greet_Powder_Chemical","Production_Notes","Labour_Salary"]:
            _df = load_sheet(sheet_name)
            if not _df.empty:
                st.markdown(f"**{sheet_name}**: `{list(_df.columns)}`")
            else:
                st.markdown(f"**{sheet_name}**: _(empty or not found)_")

    sheet_id = ""
    try:    sheet_id = st.secrets.get("GOOGLE_SHEET_ID","")
    except: sheet_id = os.getenv("GOOGLE_SHEET_ID","")
    connected = bool(sheet_id and sheet_id not in ("","YOUR_SHEET_ID"))
    st.markdown(f"""
    <div style="margin-top:16px;padding-top:16px;border-top:1px solid {S['border']}">
        <div style="display:flex;align-items:center;gap:8px">
            <div style="width:28px;height:28px;border-radius:50%;background:{S['accentDim']};border:1px solid {S['border']};display:flex;align-items:center;justify-content:center;font-size:11px;color:{S['accent']};font-weight:700">RP</div>
            <div>
                <div style="font-size:12px;font-weight:500;color:{S['text']}">Owner</div>
                <div style="font-size:10px;color:{S['muted']}">Administrator</div>
            </div>
        </div>
        <div style="margin-top:10px">
            {'<span class="badge badge-green">● Connected</span>' if connected else '<span class="badge badge-red">● No Sheet ID</span>'}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
#  OVERVIEW
# ════════════════════════════════════════════════════════════════════════════════
if nav == "⬡  Overview":
    st.markdown('<div class="page-title fade-in">Command Center</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Live factory snapshot · Rajratan Block Manufacturing</div>', unsafe_allow_html=True)

    # Load data
    df_clients  = prep_clients(load_sheet("Clients"))
    df_block    = prep_stocks(load_sheet("Block_Stocks"), "block")
    df_cement   = prep_stocks(load_sheet("Cement_Stocks"), "cement")
    df_cf       = prep_cashflow(load_sheet("Cashflow"))
    df_prod     = load_sheet("Production_Notes")
    df_chem     = prep_chemical(load_sheet("Greet_Powder_Chemical"))

    # Compute KPIs
    total_sales  = df_clients["Total_INR"].sum()   if not df_clients.empty and "Total_INR" in df_clients.columns else 0
    block_close  = df_block["Closing"].iloc[-1]    if not df_block.empty  and "Closing" in df_block.columns    else 0
    cement_close = df_cement["Closing"].iloc[-1]   if not df_cement.empty and "Closing" in df_cement.columns   else 0
    cash_in  = df_cf[df_cf["Type"]=="IN"]["Amount_INR"].sum()  if not df_cf.empty and "Type" in df_cf.columns else 0
    cash_out = df_cf[df_cf["Type"]=="OUT"]["Amount_INR"].sum() if not df_cf.empty and "Type" in df_cf.columns else 0
    net_cash = cash_in - cash_out

    num_prod = df_prod["Blocks"].sum() if not df_prod.empty and "Blocks" in df_prod.columns else 0
    try: num_prod = int(float(str(num_prod).replace(",","")))
    except: num_prod = 0

    pending = 0
    if not df_clients.empty and "Status" in df_clients.columns:
        pending = len(df_clients[df_clients["Status"].str.lower() == "pending"])

    # Status strip
    surplus = net_cash >= 0
    st.markdown(f"""
    <div class="status-strip">
        <div class="status-pill"><span class="status-pill-dot" style="background:{S['accent']}"></span><span class="status-pill-label">Production</span><span class="status-pill-val" style="color:{S['accent']}">Active</span></div>
        <div class="status-pill"><span class="status-pill-dot" style="background:{S['accent']}"></span><span class="status-pill-label">Stocks</span><span class="status-pill-val" style="color:{S['accent']}">Sufficient</span></div>
        <div class="status-pill"><span class="status-pill-dot" style="background:{'#00d4aa' if surplus else '#f45b6b'}"></span><span class="status-pill-label">Cashflow</span><span class="status-pill-val" style="color:{'#00d4aa' if surplus else '#f45b6b'}">{'Surplus' if surplus else 'Deficit'}</span></div>
        <div class="status-pill"><span class="status-pill-dot" style="background:{S['amber']}"></span><span class="status-pill-label">Orders</span><span class="status-pill-val" style="color:{S['amber']}">{pending} Pending</span></div>
    </div>
    """, unsafe_allow_html=True)

    # KPI row
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: metric_card("Total Client Sales", compact(total_sales), "All-time revenue", S["blue"])
    with c2: metric_card("Net Cashflow", compact(net_cash), "This period", S["accent"])
    with c3: metric_card("Block Stock", f"{int(block_close):,}", "Closing units", S["amber"])
    with c4: metric_card("Cement Stock", f"{int(cement_close):,}", "Closing bags", S["purple"])
    with c5: metric_card("Blocks Produced", f"{int(num_prod):,}", "Recent shifts", S["accent"])

    st.markdown("<br>", unsafe_allow_html=True)

    # Cashflow trend chart
    col_l, col_r = st.columns(2)
    with col_l:
        if not df_cf.empty and "Type" in df_cf.columns and "Date" in df_cf.columns:
            df_cf_p = df_cf.copy()
            df_cf_p["Date"] = df_cf_p["Date"].astype(str)
            grp = df_cf_p.groupby(["Date","Type"])["Amount_INR"].sum().reset_index()
            grp_in  = grp[grp["Type"]=="IN"].sort_values("Date")
            grp_out = grp[grp["Type"]=="OUT"].sort_values("Date")
            fig = dual_area_chart(
                grp_in["Date"].tolist(), grp_in["Amount_INR"].tolist(), grp_out["Amount_INR"].tolist(),
                "Cash IN", "Cash OUT", S["accent"], S["red"]
            )
            chart_card("Cashflow Trend", fig, [("Cash IN", S["accent"]),("Cash OUT", S["red"])])
        else:
            st.info("No cashflow data yet.")

    with col_r:
        if not df_block.empty and "Closing" in df_block.columns:
            date_col = "Date" if "Date" in df_block.columns else df_block.columns[0]
            x_vals = df_block[date_col].astype(str).tolist()
            fig = bar_chart(
                x_vals,
                [(df_block["Sales"].tolist(), "Sales"), (df_block["Closing"].tolist(), "Closing")],
                [S["blue"], S["accent"]]
            )
            chart_card("Block Stock Movement", fig, [("Closing", S["accent"]),("Sales", S["blue"])])
        else:
            st.info("No block stock data yet.")

    # Bottom row: Recent orders + material spend
    col_l2, col_r2 = st.columns([1.4, 1])
    with col_l2:
        section_label("Recent Client Orders")
        if not df_clients.empty:
            show_cols = ["Name","Qty_Brass","Total_INR","Status"]
            avail = [c for c in show_cols if c in df_clients.columns]
            rows_html = ""
            for _, row in df_clients.head(5).iterrows():
                name   = row.get("Name","—")
                qty    = f'{int(row["Qty_Brass"]):,}' if "Qty_Brass" in row else "—"
                total  = inr(row["Total_INR"]) if "Total_INR" in row else "—"
                status = status_dot(str(row.get("Status","—"))) if "Status" in row else "—"
                rows_html += f"""
                <tr>
                    <td style="font-weight:500">{name}</td>
                    <td class="mono" style="color:{S['muted']}">{qty}</td>
                    <td class="mono" style="color:{S['accent']};font-weight:600">{total}</td>
                    <td>{status}</td>
                </tr>"""
            st.markdown(f"""
            <div class="table-card">
                <div class="table-header">
                    <span class="table-header-label">Recent Orders</span>
                    <span class="badge badge-blue">{len(df_clients)} total</span>
                </div>
                <table class="rtable">
                    <thead><tr>
                        <th>Client</th><th>Qty (Brass)</th><th>Amount</th><th>Status</th>
                    </tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("No client data yet.")

    with col_r2:
        section_label("Material Spend Mix")
        if not df_chem.empty and "Amount_INR" in df_chem.columns:
            item_col = "Item_Name" if "Item_Name" in df_chem.columns else df_chem.columns[0]
            grp = df_chem.groupby(item_col)["Amount_INR"].sum().reset_index()
            labels = grp[item_col].tolist()
            values = grp["Amount_INR"].tolist()
            colors = PIE_COLORS[:len(labels)]
            st.markdown('<div class="chart-card"><div class="chart-title">Material Spend Mix</div>', unsafe_allow_html=True)
            st.plotly_chart(pie_chart(labels, values, colors), use_container_width=True, config={"displayModeBar":False})
            st.markdown(pie_legend(list(zip(labels, values, colors))), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No material data yet.")

# ════════════════════════════════════════════════════════════════════════════════
#  BLOCK & CEMENT
# ════════════════════════════════════════════════════════════════════════════════
elif nav == "◧  Block & Cement":
    st.markdown('<div class="page-title fade-in">Stock Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Block and cement inventory tracker</div>', unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["🧱 Block Stocks", "🏗️ Cement Stocks", "📋 Production Notes"])

    for tab, sheet_name, sheet_type, color, label, unit in [
        (t1, "Block_Stocks",  "block",  S["blue"],  "Block",  "units"),
        (t2, "Cement_Stocks", "cement", S["amber"], "Cement", "bags"),
    ]:
        with tab:
            df = prep_stocks(load_sheet(sheet_name), sheet_type)
            if not df.empty:
                last = df.iloc[-1]
                date_col = "Date" if "Date" in df.columns else df.columns[0]

                c1, c2, c3, c4 = st.columns(4)
                with c1: metric_card("Opening", f'{int(last.get("Opening",0)):,}', unit, S["muted"])
                with c2: metric_card("New In",  f'{int(last.get("New_In",0)):,}',  unit, S["purple"])
                with c3: metric_card("Sales",   f'{int(last.get("Sales",0)):,}',   unit, S["red"])
                with c4: metric_card("Closing", f'{int(last.get("Closing",0)):,}', unit, color)

                st.markdown("<br>", unsafe_allow_html=True)
                col_l, col_r = st.columns(2)
                with col_l:
                    x = df[date_col].astype(str).tolist()
                    y = df["Closing"].tolist()
                    fig = area_chart(x, y, f"{label} Closing", color, y_fmt=False)
                    chart_card("Closing Stock Trend", fig)
                with col_r:
                    fig = bar_chart(
                        df[date_col].astype(str).tolist(),
                        [(df["New_In"].tolist(),"New In"),(df["Sales"].tolist(),"Sales")],
                        [S["accent"], S["red"]]
                    )
                    chart_card("Sales vs New In", fig, [("New In",S["accent"]),("Sales",S["red"])])

                section_label("All Records")
                rows_html = ""
                for _, row in df.iterrows():
                    op   = int(row.get("Opening",0))
                    ni   = int(row.get("New_In",0))
                    sl   = int(row.get("Sales",0))
                    cl   = int(row.get("Closing",0))
                    util = f"{(sl/(op+ni)*100):.1f}" if (op+ni) > 0 else "0.0"
                    rows_html += f"""
                    <tr>
                        <td style="font-family:'Rajdhani',sans-serif;font-size:14px;font-weight:600">{row.get(date_col,'—')}</td>
                        <td class="mono" style="color:{S['muted']}">{op:,}</td>
                        <td class="mono" style="color:{S['purple']}">{ni:,}</td>
                        <td class="mono" style="color:{S['red']}">{sl:,}</td>
                        <td class="mono" style="color:{color}">{cl:,}</td>
                        <td>{util_bar(util, color)}</td>
                    </tr>"""
                st.markdown(f"""
                <div class="table-card">
                    <table class="rtable">
                        <thead><tr>
                            <th>Month</th><th>Opening</th><th>New In</th><th>Sales</th><th>Closing</th><th>Utilization</th>
                        </tr></thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                </div>""", unsafe_allow_html=True)
            else:
                st.info(f"No {label} stock data yet.")

    with t3:
        df = load_sheet("Production_Notes")
        if not df.empty:
            df = num_col(df, "Batches")
            df = num_col(df, "Blocks")
            total_batches = int(df["Batches"].sum()) if "Batches" in df.columns else 0
            total_blocks  = int(df["Blocks"].sum())  if "Blocks"  in df.columns else 0
            avg_shift     = int(total_blocks / len(df)) if len(df) > 0 else 0

            c1, c2, c3 = st.columns(3)
            with c1: metric_card("Total Batches",  f"{total_batches:,}", "Recent shifts",  S["accent"])
            with c2: metric_card("Total Blocks",   f"{total_blocks:,}", "Produced",        S["blue"])
            with c3: metric_card("Avg per Shift",  f"{avg_shift:,}",    "Blocks/shift",    S["purple"])

            section_label("Production Records")
            q_colors = {"A+":"green","A":"blue","B+":"amber","B":"amber"}
            rows_html = ""
            for _, row in df.iterrows():
                date    = row.get("Date","—")
                shift   = str(row.get("Shift","—"))
                batches = int(row.get("Batches",0))
                blocks  = int(row.get("Blocks",0))
                quality = str(row.get("Quality","—"))
                note    = row.get("Note","—")
                shift_type = "amber" if "morning" in shift.lower() else "blue"
                q_type  = q_colors.get(quality,"blue")
                rows_html += f"""
                <tr>
                    <td class="mono" style="color:{S['muted']}">{date}</td>
                    <td>{badge(shift, shift_type)}</td>
                    <td class="mono" style="color:{S['text']}">{batches}</td>
                    <td class="mono" style="color:{S['accent']};font-weight:600">{blocks:,}</td>
                    <td>{badge(quality, q_type)}</td>
                    <td style="color:{S['muted']};font-size:12px">{note}</td>
                </tr>"""
            st.markdown(f"""
            <div class="table-card">
                <table class="rtable">
                    <thead><tr>
                        <th>Date</th><th>Shift</th><th>Batches</th><th>Blocks</th><th>Quality</th><th>Note</th>
                    </tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("No production notes yet.")

# ════════════════════════════════════════════════════════════════════════════════
#  CLIENTS & MATERIALS
# ════════════════════════════════════════════════════════════════════════════════
elif nav == "◈  Clients & Materials":
    st.markdown('<div class="page-title fade-in">Clients & Materials</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Sales orders and raw material purchases</div>', unsafe_allow_html=True)

    t1, t2 = st.tabs(["👥 Clients", "🧪 Chemicals / Powder"])

    with t1:
        df = prep_clients(load_sheet("Clients"))
        if not df.empty:
            total_rev = df["Total_INR"].sum() if "Total_INR" in df.columns else 0
            total_qty = df["Qty_Brass"].sum()  if "Qty_Brass" in df.columns else 0

            c1, c2, c3 = st.columns(3)
            with c1: metric_card("Total Revenue",     compact(total_rev), "All clients",   S["blue"])
            with c2: metric_card("Total Qty (Brass)", f"{int(total_qty):,}", "Blocks delivered", S["accent"])
            with c3: metric_card("Active Clients",    str(len(df)),       "This period",   S["purple"])

            st.markdown("<br>", unsafe_allow_html=True)
            search = st.text_input("Search clients", placeholder="🔍  Search clients...", label_visibility="collapsed")
            filtered = df[df.apply(lambda r: search.lower() in str(r.get("Name","")).lower(), axis=1)] if search else df

            name_col   = "Name"          if "Name"        in df.columns else df.columns[0]
            qty_col    = "Qty_Brass"     if "Qty_Brass"   in df.columns else None
            rate_col   = "Rate_INR"      if "Rate_INR"    in df.columns else None
            total_col  = "Total_INR"     if "Total_INR"   in df.columns else None
            status_col = "Status"        if "Status"      in df.columns else None
            date_col   = "Date"          if "Date"        in df.columns else None

            rows_html = ""
            for _, row in filtered.iterrows():
                name   = row.get(name_col,"—")
                qty    = f'{int(row[qty_col]):,}'     if qty_col    else "—"
                rate   = f'₹{int(row[rate_col])}'    if rate_col   else "—"
                total  = inr(row[total_col])          if total_col  else "—"
                status = status_dot(str(row[status_col])) if status_col else "—"
                date   = str(row.get(date_col,"—"))   if date_col   else "—"
                rows_html += f"""
                <tr>
                    <td style="font-weight:600">{name}</td>
                    <td class="mono" style="color:{S['muted']}">{qty}</td>
                    <td class="mono" style="color:{S['muted']}">{rate}</td>
                    <td class="mono" style="color:{S['accent']};font-weight:600">{total}</td>
                    <td>{status}</td>
                    <td class="mono" style="color:{S['muted']};font-size:11px">{date}</td>
                </tr>"""
            st.markdown(f"""
            <div class="table-card" style="margin-top:12px">
                <table class="rtable">
                    <thead><tr>
                        <th>Client Name</th><th>Qty (Brass)</th><th>Rate/Brass</th><th>Total Amount</th><th>Status</th><th>Date</th>
                    </tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("No client data yet.")

    with t2:
        df = prep_chemical(load_sheet("Greet_Powder_Chemical"))
        if not df.empty:
            total_amt = df["Amount_INR"].sum() if "Amount_INR" in df.columns else 0
            total_qty = df["Qty_Ton"].sum()    if "Qty_Ton"    in df.columns else 0

            c1, c2, c3 = st.columns(3)
            with c1: metric_card("Total Spend",    compact(total_amt),        "All materials",      S["amber"])
            with c2: metric_card("Total Quantity", f"{total_qty:.1f} T",      "Tonnes purchased",   S["blue"])
            with c3: metric_card("Item Types",     str(len(df)),              "Distinct materials", S["purple"])

            st.markdown("<br>", unsafe_allow_html=True)
            item_col = "Item_Name" if "Item_Name" in df.columns else df.columns[0]
            col_l, col_r = st.columns(2)
            with col_l:
                grp    = df.groupby(item_col)["Amount_INR"].sum().reset_index()
                labels = grp[item_col].tolist()
                values = grp["Amount_INR"].tolist()
                colors = PIE_COLORS[:len(labels)]
                st.markdown('<div class="chart-card"><div class="chart-title">Spend by Material</div>', unsafe_allow_html=True)
                st.plotly_chart(pie_chart(labels, values, colors), use_container_width=True, config={"displayModeBar":False})
                st.markdown(pie_legend(list(zip(labels, values, colors))), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with col_r:
                if "Rate_INR" in df.columns:
                    fig = h_bar_chart(df[item_col].tolist(), df["Rate_INR"].tolist(), S["amber"])
                    chart_card("Cost per Tonne", fig)

            section_label("All Records")
            qty_col   = "Qty_Ton"   if "Qty_Ton"   in df.columns else None
            rate_col  = "Rate_INR"  if "Rate_INR"  in df.columns else None
            amt_col   = "Amount_INR"

            rows_html = ""
            for _, row in df.iterrows():
                item  = row.get(item_col,"—")
                qty   = f'{row[qty_col]:.2f} T' if qty_col else "—"
                rate  = inr(row[rate_col])       if rate_col else "—"
                amt   = inr(row[amt_col])        if amt_col in row else "—"
                rows_html += f"""
                <tr>
                    <td style="font-weight:600">{item}</td>
                    <td class="mono" style="color:{S['muted']}">{qty}</td>
                    <td class="mono" style="color:{S['muted']}">{rate}</td>
                    <td class="mono" style="color:{S['amber']};font-weight:600">{amt}</td>
                </tr>"""
            st.markdown(f"""
            <div class="table-card">
                <table class="rtable">
                    <thead><tr>
                        <th>Item Name</th><th>Qty (Ton)</th><th>Rate / Ton</th><th>Total Amount</th>
                    </tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("No chemical/powder data yet.")

# ════════════════════════════════════════════════════════════════════════════════
#  FINANCIALS
# ════════════════════════════════════════════════════════════════════════════════
elif nav == "◎  Financials":
    st.markdown('<div class="page-title fade-in">Financials</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Cashflow, expenses, and labour salary records</div>', unsafe_allow_html=True)

    t1, t2 = st.tabs(["💸 Cashflow", "👷 Labour Salary"])

    with t1:
        df = prep_cashflow(load_sheet("Cashflow"))
        if not df.empty and "Type" in df.columns:
            cash_in  = df[df["Type"]=="IN"]["Amount_INR"].sum()
            cash_out = df[df["Type"]=="OUT"]["Amount_INR"].sum()
            net      = cash_in - cash_out

            c1, c2, c3 = st.columns(3)
            with c1: metric_card("Total IN",    compact(cash_in),  "Cash received", S["accent"])
            with c2: metric_card("Total OUT",   compact(cash_out), "Expenses",      S["red"])
            with c3: metric_card("Net Balance", compact(net), "✅ Surplus" if net >= 0 else "⚠️ Deficit", S["accent"] if net >= 0 else S["red"])

            st.markdown("<br>", unsafe_allow_html=True)
            col_l, col_r = st.columns([1.2, 1])
            with col_l:
                # Monthly grouped bar
                if "Date" in df.columns:
                    df["Date"] = df["Date"].astype(str)
                    grp = df.groupby(["Date","Type"])["Amount_INR"].sum().reset_index()
                    dates  = sorted(grp["Date"].unique())
                    in_vals  = [grp[(grp["Date"]==d) & (grp["Type"]=="IN")]["Amount_INR"].sum()  for d in dates]
                    out_vals = [grp[(grp["Date"]==d) & (grp["Type"]=="OUT")]["Amount_INR"].sum() for d in dates]
                    fig = bar_chart(dates, [(in_vals,"Cash IN"),(out_vals,"Cash OUT")], [S["accent"],S["red"]])
                    chart_card("Monthly Cashflow Comparison", fig, [("Cash IN",S["accent"]),("Cash OUT",S["red"])])

            with col_r:
                if "Date" in df.columns:
                    df_in = df[df["Type"]=="IN"].sort_values("Date")
                    if not df_in.empty:
                        net_by_date = df.groupby("Date").apply(
                            lambda g: g[g["Type"]=="IN"]["Amount_INR"].sum() - g[g["Type"]=="OUT"]["Amount_INR"].sum()
                        ).reset_index()
                        net_by_date.columns = ["Date","Net"]
                        fig = area_chart(net_by_date["Date"].astype(str).tolist(), net_by_date["Net"].tolist(), "Net", S["accent"], y_fmt=True)
                        chart_card("Net Profit Trend", fig)

            section_label("Monthly Records")
            if "Date" in df.columns:
                monthly = df.groupby(["Date","Type"])["Amount_INR"].sum().unstack(fill_value=0).reset_index()
                monthly.columns.name = None
                if "IN" not in monthly.columns:  monthly["IN"]  = 0
                if "OUT" not in monthly.columns: monthly["OUT"] = 0
                monthly["Net"]    = monthly["IN"] - monthly["OUT"]
                monthly["Margin"] = (monthly["Net"] / monthly["IN"] * 100).round(1).fillna(0)

                rows_html = ""
                for _, row in monthly.iterrows():
                    n   = row["Net"]
                    mg  = row["Margin"]
                    bar_color = S["accent"] if mg > 40 else S["amber"]
                    rows_html += f"""
                    <tr>
                        <td style="font-family:'Rajdhani',sans-serif;font-size:14px;font-weight:700">{row['Date']}</td>
                        <td class="mono" style="color:{S['accent']}">{inr(row['IN'])}</td>
                        <td class="mono" style="color:{S['red']}">{inr(row['OUT'])}</td>
                        <td class="mono" style="color:{'#00d4aa' if n>=0 else S['red']};font-weight:600">{inr(n)}</td>
                        <td>{util_bar(f'{mg:.1f}', bar_color)}</td>
                    </tr>"""
                st.markdown(f"""
                <div class="table-card">
                    <table class="rtable">
                        <thead><tr>
                            <th>Month</th><th>Cash IN</th><th>Cash OUT</th><th>Net</th><th>Margin</th>
                        </tr></thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No cashflow data yet.")

    with t2:
        df = prep_labour(load_sheet("Labour_Salary"))
        if not df.empty:
            total_sal = df["Amount_INR"].sum()
            c1, c2, c3 = st.columns(3)
            with c1: metric_card("Total Salary Paid", inr(total_sal), "This period", S["amber"])
            with c2: metric_card("Total Workers",     str(len(df)),   "Active",      S["blue"])
            with c3: metric_card("Avg Per Worker",    inr(int(total_sal/len(df))) if len(df)>0 else "₹0", "Average salary", S["purple"])

            st.markdown("<br>", unsafe_allow_html=True)
            # Exact columns: Date, Worker_Name, Amount_INR, Notes
            name_col = "Worker_Name"

            by_worker = df.groupby(name_col)["Amount_INR"].sum().reset_index().sort_values("Amount_INR")
            fig = h_bar_chart(
                by_worker[name_col].tolist(),
                by_worker["Amount_INR"].tolist(),
                S["amber"],
                h=max(180, len(by_worker)*50)
            )
            chart_card("Salary by Worker", fig)

            section_label("All Records")
            rows_html = ""
            for _, row in df.iterrows():
                name  = row.get("Worker_Name","—")
                amt   = inr(row.get("Amount_INR",0))
                date  = str(row.get("Date","—"))
                note  = str(row.get("Notes","—"))
                rows_html += f"""
                <tr>
                    <td class="mono" style="color:{S['muted']}">{date}</td>
                    <td style="font-weight:600">{name}</td>
                    <td class="mono" style="color:{S['amber']};font-weight:600">{amt}</td>
                    <td style="color:{S['muted']};font-size:12px">{note}</td>
                </tr>"""
            st.markdown(f"""
            <div class="table-card">
                <table class="rtable">
                    <thead><tr>
                        <th>Date</th><th>Worker Name</th><th>Amount</th><th>Notes</th>
                    </tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("No labour salary data yet.")