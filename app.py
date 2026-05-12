from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Rajratan Enterprises",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Sora', sans-serif !important;
    background-color: #0d0f14 !important;
    color: #e8e9ed !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #13151c !important;
    border-right: 1px solid #1e2130 !important;
}
section[data-testid="stSidebar"] * { color: #b0b3c1 !important; }
section[data-testid="stSidebar"] .stRadio label:hover { color: #fff !important; }

/* Main area */
.main .block-container {
    background: #0d0f14 !important;
    padding: 2rem 2.5rem !important;
    max-width: 1400px;
}

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

/* Metric cards */
.metric-row { display: flex; gap: 16px; margin-bottom: 24px; }
.metric-card {
    flex: 1;
    background: #13151c;
    border: 1px solid #1e2130;
    border-radius: 14px;
    padding: 22px 24px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent, #4f6ef7);
}
.metric-card:hover { border-color: #2a2f45; }
.metric-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #5a5f7a !important;
    margin-bottom: 10px;
}
.metric-value {
    font-size: 28px;
    font-weight: 700;
    color: #f0f1f5 !important;
    font-family: 'JetBrains Mono', monospace !important;
    line-height: 1;
}
.metric-sub {
    font-size: 12px;
    color: #5a5f7a !important;
    margin-top: 8px;
}
.metric-accent { color: var(--accent, #4f6ef7) !important; }

/* Section headers */
.section-title {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #5a5f7a !important;
    margin: 28px 0 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #1e2130;
}

/* Page title */
.page-title {
    font-size: 26px;
    font-weight: 700;
    color: #f0f1f5 !important;
    margin-bottom: 4px;
}
.page-sub {
    font-size: 13px;
    color: #5a5f7a !important;
    margin-bottom: 28px;
}

/* Status badge */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
}
.badge-green { background: #0d2e1a; color: #34d27a !important; border: 1px solid #1a4a2e; }
.badge-red   { background: #2e0d0d; color: #f45b5b !important; border: 1px solid #4a1a1a; }
.badge-blue  { background: #0d1a2e; color: #4f6ef7 !important; border: 1px solid #1a2e4a; }

/* Dataframe overrides */
div[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden;
    border: 1px solid #1e2130 !important;
}

/* Tabs */
div[data-testid="stTabs"] button {
    font-family: 'Sora', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #5a5f7a !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #f0f1f5 !important;
    border-bottom-color: #4f6ef7 !important;
}

/* Buttons */
.stButton > button {
    background: #1e2130 !important;
    color: #b0b3c1 !important;
    border: 1px solid #2a2f45 !important;
    border-radius: 8px !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #2a2f45 !important;
    color: #f0f1f5 !important;
    border-color: #4f6ef7 !important;
}

/* Info/error boxes */
.stAlert { border-radius: 10px !important; }

/* Sidebar nav brand */
.brand-logo {
    font-size: 20px;
    font-weight: 700;
    color: #f0f1f5 !important;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
}
.brand-sub {
    font-size: 11px;
    color: #3d4260 !important;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 24px;
}
</style>
""", unsafe_allow_html=True)

# ── Google Sheets connection ───────────────────────────────────────────────────
SCOPES    = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS_FILE = os.getenv("GOOGLE_CREDS_JSON", "credentials.json")
SHEET_ID   = os.getenv("GOOGLE_SHEET_ID", "")

def fmt_inr(val):
    try: return f"₹{float(val):,.0f}"
    except: return "₹0"

def fmt_int(val):
    try: return f"{int(float(val)):,}"
    except: return "0"

@st.cache_resource(ttl=300)
def get_client():
    import json
    creds_content = None
    try:
        creds_content = st.secrets["GOOGLE_CREDS_JSON_CONTENT"]
    except:
        creds_content = os.getenv("GOOGLE_CREDS_JSON_CONTENT")
    if creds_content:
        creds = Credentials.from_service_account_info(
            json.loads(creds_content), scopes=SCOPES
        )
    else:
        creds = Credentials.from_service_account_file(
            os.getenv("GOOGLE_CREDS_JSON", "credentials.json"), scopes=SCOPES
        )
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def load_sheet(name: str) -> pd.DataFrame:
    try:
        sheet_id = st.secrets.get("GOOGLE_SHEET_ID", os.getenv("GOOGLE_SHEET_ID", ""))
        gc = get_client()
        ws = gc.open_by_key(sheet_id).worksheet(name)
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"Sheet tab '{name}' not found.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading '{name}': {e}")
        return pd.DataFrame()

# ── Compute helpers ───────────────────────────────────────────────────────────
def num(df, col):
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

def prep_clients(df):
    if df.empty: return df
    df = num(df, "Qty_Brass"); df = num(df, "Rate_INR")
    if "Qty_Brass" in df.columns and "Rate_INR" in df.columns:
        df["Total_INR"] = df["Qty_Brass"] * df["Rate_INR"]
    return df

def prep_stocks(df):
    if df.empty: return df
    for c in ["Opening","New_In","Sales","Total","Closing"]: df = num(df, c)
    return df

def prep_chemical(df):
    if df.empty: return df
    df = num(df, "Qty_Ton"); df = num(df, "Rate_INR")
    if "Qty_Ton" in df.columns and "Rate_INR" in df.columns:
        df["Amount_INR"] = df["Qty_Ton"] * df["Rate_INR"]
    return df

# ── Chart theme ───────────────────────────────────────────────────────────────
CHART_LAYOUT = dict(
    font_family="Sora",
    plot_bgcolor="#13151c",
    paper_bgcolor="#13151c",
    font_color="#b0b3c1",
    margin=dict(l=12, r=12, t=40, b=12),
    height=280,
    xaxis=dict(gridcolor="#1e2130", showgrid=False, tickfont_size=11),
    yaxis=dict(gridcolor="#1e2130", tickfont_size=11),
    legend=dict(bgcolor="#13151c", bordercolor="#1e2130"),
)

COLORS = ["#4f6ef7","#34d27a","#f7a94f","#f45b5b","#a855f7","#06b6d4"]

def line_chart(df, x, y, title, color="#4f6ef7"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[x], y=df[y],
        mode="lines+markers",
        line=dict(color=color, width=2),
        marker=dict(size=5, color=color),
        fill="tozeroy",
        fillcolor=f"rgba(79,110,247,0.06)",
    ))
    fig.update_layout(title=dict(text=title, font_size=13, font_color="#b0b3c1"), **CHART_LAYOUT)
    return fig

def bar_cashflow(df):
    if df.empty or "Type" not in df.columns: return go.Figure()
    df = num(df, "Amount_INR")
    g = df.groupby("Type")["Amount_INR"].sum().reset_index()
    colors = {"IN":"#34d27a","OUT":"#f45b5b"}
    fig = go.Figure(go.Bar(
        x=g["Type"], y=g["Amount_INR"],
        marker_color=[colors.get(t,"#4f6ef7") for t in g["Type"]],
        text=[fmt_inr(v) for v in g["Amount_INR"]],
        textposition="outside", textfont_size=12,
        width=0.35,
    ))
    fig.update_layout(title=dict(text="Cashflow IN vs OUT", font_size=13, font_color="#b0b3c1"),
                      showlegend=False, **CHART_LAYOUT)
    return fig

# ── Metric card helper ────────────────────────────────────────────────────────
def metric(title, value, sub="", accent="#4f6ef7"):
    st.markdown(f"""
    <div class="metric-card" style="--accent:{accent}">
        <div class="metric-label">{title}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

def section(label):
    st.markdown(f'<div class="section-title">{label}</div>', unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="brand-logo">🏗️ Rajratan</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">Enterprises · Dashboard</div>', unsafe_allow_html=True)

    nav = st.radio("", [
        "Overview",
        "Block & Cement",
        "Clients & Materials",
        "Financials",
    ], label_visibility="collapsed")

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Connection status check
    sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
    if sheet_id and sheet_id != "YOUR_SHEET_ID":
        st.markdown('<span class="badge badge-green">● Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-red">● No Sheet ID</span>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:11px;color:#5a5f7a;margin-top:8px">Set GOOGLE_SHEET_ID in .env</p>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⟳  Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

    st.markdown('<p style="font-size:10px;color:#3d4260;position:fixed;bottom:16px;left:16px">Auto-refresh · 5 min</p>',
                unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if nav == "Overview":
    st.markdown('<div class="page-title">Business Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Live snapshot from Google Sheets</div>', unsafe_allow_html=True)

    df_c  = prep_clients(load_sheet("Clients"))
    df_b  = prep_stocks(load_sheet("Block_Stocks"))
    df_ce = prep_stocks(load_sheet("Cement_Stocks"))
    df_cf = load_sheet("Cashflow")
    if not df_cf.empty: df_cf = num(df_cf, "Amount_INR")

    total_sales   = df_c["Total_INR"].sum()   if not df_c.empty  and "Total_INR" in df_c.columns  else 0
    block_close   = df_b["Closing"].iloc[-1]  if not df_b.empty  and "Closing"   in df_b.columns  else 0
    cement_close  = df_ce["Closing"].iloc[-1] if not df_ce.empty and "Closing"   in df_ce.columns else 0
    cash_in  = df_cf[df_cf["Type"]=="IN"]["Amount_INR"].sum()  if not df_cf.empty and "Type" in df_cf.columns else 0
    cash_out = df_cf[df_cf["Type"]=="OUT"]["Amount_INR"].sum() if not df_cf.empty and "Type" in df_cf.columns else 0
    net_cash = cash_in - cash_out

    c1, c2, c3, c4 = st.columns(4)
    with c1: metric("Total Client Sales", fmt_inr(total_sales), "All time", "#4f6ef7")
    with c2: metric("Block Stock", fmt_int(block_close), "Closing units", "#34d27a")
    with c3: metric("Cement Stock", fmt_int(cement_close), "Closing bags", "#f7a94f")
    with c4: metric("Net Cashflow", fmt_inr(net_cash),
                    "✅ Surplus" if net_cash >= 0 else "⚠️ Deficit",
                    "#34d27a" if net_cash >= 0 else "#f45b5b")

    section("Trends")
    col_l, col_r = st.columns(2)
    with col_l:
        if not df_b.empty and "Closing" in df_b.columns and "Date" in df_b.columns:
            st.plotly_chart(line_chart(df_b,"Date","Closing","Block Stock — Closing","#4f6ef7"),
                            use_container_width=True)
        else:
            st.info("No block stock data yet.")
    with col_r:
        if not df_cf.empty:
            st.plotly_chart(bar_cashflow(df_cf), use_container_width=True)
        else:
            st.info("No cashflow data yet.")

# ═══════════════════════════════════════════════════════════════════════════════
#  BLOCK & CEMENT
# ═══════════════════════════════════════════════════════════════════════════════
elif nav == "Block & Cement":
    st.markdown('<div class="page-title">Stock Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Block and cement inventory</div>', unsafe_allow_html=True)

    t1, t2 = st.tabs(["🧱 Block Stocks", "🏗️ Cement Stocks"])

    for tab, sheet, color, label in [
        (t1, "Block_Stocks",  "#4f6ef7", "Block"),
        (t2, "Cement_Stocks", "#f7a94f", "Cement"),
    ]:
        with tab:
            df = prep_stocks(load_sheet(sheet))
            if not df.empty:
                c1, c2, c3 = st.columns(3)
                with c1: metric("Opening",  fmt_int(df["Opening"].iloc[-1])  if "Opening"  in df.columns else "—")
                with c2: metric("Sales",    fmt_int(df["Sales"].iloc[-1])    if "Sales"    in df.columns else "—")
                with c3: metric("Closing",  fmt_int(df["Closing"].iloc[-1])  if "Closing"  in df.columns else "—", accent=color)
                section("Closing Trend")
                if "Date" in df.columns and "Closing" in df.columns:
                    st.plotly_chart(line_chart(df,"Date","Closing",f"{label} Closing Stock",color),
                                    use_container_width=True)
                section("All Records")
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info(f"No {label} data yet. Send a message via WhatsApp to add entries.")

# ═══════════════════════════════════════════════════════════════════════════════
#  CLIENTS & MATERIALS
# ═══════════════════════════════════════════════════════════════════════════════
elif nav == "Clients & Materials":
    st.markdown('<div class="page-title">Clients & Materials</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Sales orders and raw material purchases</div>', unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["👥 Clients", "🧪 Chemicals / Powder", "📝 Production Notes"])

    with t1:
        df = prep_clients(load_sheet("Clients"))
        if not df.empty:
            total = df["Total_INR"].sum() if "Total_INR" in df.columns else 0
            qty   = df["Qty_Brass"].sum() if "Qty_Brass"  in df.columns else 0
            c1, c2, c3 = st.columns(3)
            with c1: metric("Total Revenue",     fmt_inr(total), "All clients", "#4f6ef7")
            with c2: metric("Total Qty (Brass)", fmt_int(qty))
            with c3: metric("Total Entries",     str(len(df)))
            section("Records")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No client data yet.")

    with t2:
        df = prep_chemical(load_sheet("Greet_Powder_Chemical"))
        if not df.empty:
            total_amt = df["Amount_INR"].sum() if "Amount_INR" in df.columns else 0
            qty_total = df["Qty_Ton"].sum()    if "Qty_Ton"    in df.columns else 0
            c1, c2 = st.columns(2)
            with c1: metric("Total Amount",   fmt_inr(total_amt))
            with c2: metric("Total Quantity", f"{qty_total:.1f} Ton")
            if "Item_Name" in df.columns and "Amount_INR" in df.columns:
                section("Spend by Item")
                g = df.groupby("Item_Name")["Amount_INR"].sum().reset_index()
                fig = go.Figure(go.Pie(
                    labels=g["Item_Name"], values=g["Amount_INR"],
                    marker_colors=COLORS[:len(g)],
                    hole=0.5,
                    textfont_size=12,
                ))
                fig.update_layout(title=dict(text="Material Spend", font_size=13, font_color="#b0b3c1"),
                                  **{**CHART_LAYOUT, "height":300})
                st.plotly_chart(fig, use_container_width=True)
            section("Records")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No chemical/powder data yet.")

    with t3:
        df = load_sheet("Production_Notes")
        if not df.empty:
            metric("Total Entries", str(len(df)))
            section("Records")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No production notes yet.")

# ═══════════════════════════════════════════════════════════════════════════════
#  FINANCIALS
# ═══════════════════════════════════════════════════════════════════════════════
elif nav == "Financials":
    st.markdown('<div class="page-title">Financials</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Cashflow and labour salary records</div>', unsafe_allow_html=True)

    t1, t2 = st.tabs(["💸 Cashflow", "👷 Labour Salary"])

    with t1:
        df = load_sheet("Cashflow")
        if not df.empty:
            df = num(df, "Amount_INR")
            cash_in  = df[df["Type"]=="IN"]["Amount_INR"].sum()  if "Type" in df.columns else 0
            cash_out = df[df["Type"]=="OUT"]["Amount_INR"].sum() if "Type" in df.columns else 0
            net      = cash_in - cash_out
            c1, c2, c3 = st.columns(3)
            with c1: metric("Total IN",     fmt_inr(cash_in),  "Received",  "#34d27a")
            with c2: metric("Total OUT",    fmt_inr(cash_out), "Expenses",  "#f45b5b")
            with c3: metric("Net Balance",  fmt_inr(net),
                            "✅ Surplus" if net >= 0 else "⚠️ Deficit",
                            "#34d27a" if net >= 0 else "#f45b5b")
            section("Charts")
            col_l, col_r = st.columns(2)
            with col_l:
                st.plotly_chart(bar_cashflow(df), use_container_width=True)
            with col_r:
                df_in = df[df["Type"]=="IN"].copy() if "Type" in df.columns else pd.DataFrame()
                if not df_in.empty and "Date" in df_in.columns:
                    st.plotly_chart(line_chart(df_in,"Date","Amount_INR","Cash IN Over Time","#34d27a"),
                                    use_container_width=True)
            section("All Records")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No cashflow data yet.")

    with t2:
        df = load_sheet("Labour_Salary")
        if not df.empty:
            df = num(df, "Amount_INR")
            total_sal = df["Amount_INR"].sum()
            c1, c2 = st.columns(2)
            with c1: metric("Total Salary Paid", fmt_inr(total_sal), accent="#f7a94f")
            with c2: metric("Workers Logged",    str(len(df)))
            if "Worker_Name" in df.columns:
                section("Salary by Worker")
                by_w = df.groupby("Worker_Name")["Amount_INR"].sum().reset_index().sort_values("Amount_INR", ascending=True)
                fig = go.Figure(go.Bar(
                    x=by_w["Amount_INR"], y=by_w["Worker_Name"],
                    orientation="h",
                    marker_color="#f7a94f",
                    text=[fmt_inr(v) for v in by_w["Amount_INR"]],
                    textposition="outside", textfont_size=11,
                ))
                fig.update_layout(title=dict(text="Salary by Worker", font_size=13, font_color="#b0b3c1"),
                                  **{**CHART_LAYOUT, "height": max(200, len(by_w)*45)})
                st.plotly_chart(fig, use_container_width=True)
            section("All Records")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No labour salary data yet.")