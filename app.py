import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os, json

st.set_page_config(
    page_title="Rajratan Enterprises",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"], .stMarkdown, .stMetric, .stDataFrame,
    .stSelectbox, .stText, h1, h2, h3, h4, p, span, div, label,
    .stSidebar, .stMetricLabel, .stMetricValue, .stMetricDelta {
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
        color: #1a1a2e !important;
    }
    h1 { font-size: 24px !important; font-weight: 700 !important; }
    h2 { font-size: 20px !important; font-weight: 600 !important; }
    h3 { font-size: 16px !important; font-weight: 600 !important; }
    .stMetricValue { font-size: 22px !important; font-weight: 700 !important; }
    .stMetricLabel { font-size: 12px !important; font-weight: 500 !important; color: #555 !important; }
    .main { background-color: #f8f9fb; }
    .stSidebar { background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%); }
    .stSidebar [class*="css"] { color: #e0e0e0 !important; }
    .stSidebar .stRadio label { color: #e0e0e0 !important; font-size: 14px !important; }
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        border-left: 4px solid #e94560;
        margin-bottom: 12px;
    }
    .kpi-title { font-size: 12px !important; color: #888 !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { font-size: 24px !important; font-weight: 700 !important; color: #1a1a2e !important; margin-top: 4px; }
    .kpi-sub { font-size: 12px !important; color: #27ae60 !important; margin-top: 2px; }
    div[data-testid="stDataFrame"] table { font-size: 13px !important; }
    .stDataFrame thead th { background-color: #1a1a2e !important; color: white !important; font-size: 13px !important; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    hr { border: none; border-top: 1px solid #e8e8e8; margin: 16px 0; }
</style>
""", unsafe_allow_html=True)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS_FILE = os.getenv("GOOGLE_CREDS_JSON", "credentials.json")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "YOUR_SHEET_ID")

def fmt_inr(val):
    try:
        return f"₹{float(val):,.2f}"
    except:
        return "₹0.00"

def fmt_int(val):
    try:
        return f"{int(float(val)):,}"
    except:
        return "0"

@st.cache_resource(ttl=300)
def get_gspread_client():
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def load_sheet(sheet_name: str) -> pd.DataFrame:
    try:
        gc = get_gspread_client()
        ws = gc.open_by_key(SHEET_ID).worksheet(sheet_name)
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception as e:
        st.error(f"Could not load sheet '{sheet_name}': {e}")
        return pd.DataFrame()

def compute_clients(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "Qty_Brass" in df.columns and "Rate_INR" in df.columns:
        df["Qty_Brass"] = pd.to_numeric(df["Qty_Brass"], errors="coerce").fillna(0)
        df["Rate_INR"] = pd.to_numeric(df["Rate_INR"], errors="coerce").fillna(0)
        df["Total_INR"] = df["Qty_Brass"] * df["Rate_INR"]
    return df

def compute_stocks(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    for col in ["Opening", "New_In", "Sales"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "Opening" in df.columns and "New_In" in df.columns:
        df["Total"] = df["Opening"] + df["New_In"]
    if "Total" in df.columns and "Sales" in df.columns:
        df["Closing"] = df["Total"] - df["Sales"]
    if "Closing" in df.columns:
        for i in range(1, len(df)):
            if df.at[i, "Opening"] == 0:
                df.at[i, "Opening"] = df.at[i - 1, "Closing"]
                df.at[i, "Total"] = df.at[i, "Opening"] + df.at[i, "New_In"]
                df.at[i, "Closing"] = df.at[i, "Total"] - df.at[i, "Sales"]
    return df

def compute_chemical(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "Qty_Ton" in df.columns and "Rate_INR" in df.columns:
        df["Qty_Ton"] = pd.to_numeric(df["Qty_Ton"], errors="coerce").fillna(0)
        df["Rate_INR"] = pd.to_numeric(df["Rate_INR"], errors="coerce").fillna(0)
        df["Amount_INR"] = df["Qty_Ton"] * df["Rate_INR"]
    return df

def plotly_line(df, x_col, y_col, title, color="#e94560"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[y_col],
        mode="lines+markers",
        line=dict(color=color, width=2.5),
        marker=dict(size=6, color=color),
        fill="tozeroy",
        fillcolor=f"rgba(233,69,96,0.08)",
        name=y_col,
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(family="DM Sans", size=15, color="#1a1a2e")),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20, r=20, t=45, b=30),
        xaxis=dict(showgrid=False, tickfont=dict(family="DM Sans", size=12)),
        yaxis=dict(gridcolor="#f0f0f0", tickfont=dict(family="DM Sans", size=12)),
        height=300,
    )
    return fig

def plotly_cashflow_bar(df):
    if df.empty or "Type" not in df.columns or "Amount_INR" not in df.columns:
        return go.Figure()
    df["Amount_INR"] = pd.to_numeric(df["Amount_INR"], errors="coerce").fillna(0)
    grouped = df.groupby("Type")["Amount_INR"].sum().reset_index()
    colors = {"IN": "#27ae60", "OUT": "#e94560"}
    fig = go.Figure(data=[
        go.Bar(
            x=grouped["Type"],
            y=grouped["Amount_INR"],
            marker_color=[colors.get(t, "#888") for t in grouped["Type"]],
            text=[fmt_inr(v) for v in grouped["Amount_INR"]],
            textposition="outside",
            textfont=dict(family="DM Sans", size=13),
            width=0.4,
        )
    ])
    fig.update_layout(
        title=dict(text="Cashflow: IN vs OUT", font=dict(family="DM Sans", size=15, color="#1a1a2e")),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=20, r=20, t=45, b=30),
        xaxis=dict(tickfont=dict(family="DM Sans", size=13)),
        yaxis=dict(gridcolor="#f0f0f0", tickfont=dict(family="DM Sans", size=12)),
        height=320,
        showlegend=False,
    )
    return fig

def kpi(title, value, sub=""):
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-title">{title}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🏗️ Rajratan Enterprises")
    st.markdown("<hr>", unsafe_allow_html=True)
    nav = st.radio(
        "Navigation",
        ["📊 Overview", "📦 Stocks", "🧪 Materials", "💰 Financials"],
        label_visibility="collapsed",
    )
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown(
        '<p style="font-size:11px !important; color:#aaa !important; text-align:center; margin-top:16px;">Read-only · Auto-refresh 5min</p>',
        unsafe_allow_html=True,
    )

# ─── Pages ────────────────────────────────────────────────────────────────────

if nav == "📊 Overview":
    st.markdown("## 📊 Business Overview")
    st.markdown("---")

    df_clients = compute_clients(load_sheet("Clients"))
    df_block = compute_stocks(load_sheet("Block_Stocks"))
    df_cement = compute_stocks(load_sheet("Cement_Stocks"))
    df_cashflow = load_sheet("Cashflow")
    df_cashflow["Amount_INR"] = pd.to_numeric(df_cashflow.get("Amount_INR", pd.Series(dtype=float)), errors="coerce").fillna(0) if not df_cashflow.empty else pd.Series(dtype=float)

    total_sales = df_clients["Total_INR"].sum() if not df_clients.empty and "Total_INR" in df_clients.columns else 0
    block_closing = df_block["Closing"].iloc[-1] if not df_block.empty and "Closing" in df_block.columns else 0
    cement_closing = df_cement["Closing"].iloc[-1] if not df_cement.empty and "Closing" in df_cement.columns else 0
    cash_in = df_cashflow[df_cashflow["Type"] == "IN"]["Amount_INR"].sum() if not df_cashflow.empty and "Type" in df_cashflow.columns else 0
    cash_out = df_cashflow[df_cashflow["Type"] == "OUT"]["Amount_INR"].sum() if not df_cashflow.empty and "Type" in df_cashflow.columns else 0
    net_cash = cash_in - cash_out

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Total Client Sales", fmt_inr(total_sales), "All time")
    with c2: kpi("Block Stock (Closing)", fmt_int(block_closing), "units")
    with c3: kpi("Cement Stock (Closing)", fmt_int(cement_closing), "bags")
    with c4: kpi("Net Cashflow", fmt_inr(net_cash), "IN - OUT")

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns(2)

    with col_l:
        if not df_block.empty and "Closing" in df_block.columns and "Date" in df_block.columns:
            st.plotly_chart(plotly_line(df_block, "Date", "Closing", "Block Stock — Closing Trend"), use_container_width=True)
        else:
            st.info("No Block Stock data available.")

    with col_r:
        if not df_cashflow.empty:
            st.plotly_chart(plotly_cashflow_bar(df_cashflow), use_container_width=True)
        else:
            st.info("No Cashflow data available.")

elif nav == "📦 Stocks":
    st.markdown("## 📦 Stock Management")
    st.markdown("---")

    tab1, tab2 = st.tabs(["🧱 Block Stocks", "🏗️ Cement Stocks"])

    with tab1:
        df = compute_stocks(load_sheet("Block_Stocks"))
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            with c1: kpi("Latest Opening", fmt_int(df["Opening"].iloc[-1]) if "Opening" in df.columns else "N/A")
            with c2: kpi("Latest Sales", fmt_int(df["Sales"].iloc[-1]) if "Sales" in df.columns else "N/A")
            with c3: kpi("Latest Closing", fmt_int(df["Closing"].iloc[-1]) if "Closing" in df.columns else "N/A")
            st.markdown("<br>", unsafe_allow_html=True)
            if "Date" in df.columns and "Closing" in df.columns:
                st.plotly_chart(plotly_line(df, "Date", "Closing", "Block Closing Stock Over Time", "#0f3460"), use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No Block Stock data found.")

    with tab2:
        df = compute_stocks(load_sheet("Cement_Stocks"))
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            with c1: kpi("Latest Opening", fmt_int(df["Opening"].iloc[-1]) if "Opening" in df.columns else "N/A")
            with c2: kpi("Latest Sales", fmt_int(df["Sales"].iloc[-1]) if "Sales" in df.columns else "N/A")
            with c3: kpi("Latest Closing", fmt_int(df["Closing"].iloc[-1]) if "Closing" in df.columns else "N/A")
            st.markdown("<br>", unsafe_allow_html=True)
            if "Date" in df.columns and "Closing" in df.columns:
                st.plotly_chart(plotly_line(df, "Date", "Closing", "Cement Closing Stock Over Time", "#533483"), use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No Cement Stock data found.")

elif nav == "🧪 Materials":
    st.markdown("## 🧪 Materials & Clients")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["👥 Clients", "🧪 Chemicals/Powder", "📝 Production Notes"])

    with tab1:
        df = compute_clients(load_sheet("Clients"))
        if not df.empty:
            total = df["Total_INR"].sum() if "Total_INR" in df.columns else 0
            qty = df["Qty_Brass"].sum() if "Qty_Brass" in df.columns else 0
            c1, c2, c3 = st.columns(3)
            with c1: kpi("Total Revenue", fmt_inr(total), "All clients")
            with c2: kpi("Total Qty (Brass)", fmt_int(qty))
            with c3: kpi("Total Entries", str(len(df)))
            st.markdown("<br>", unsafe_allow_html=True)
            if "Total_INR" in df.columns:
                df["Total_INR_fmt"] = df["Total_INR"].apply(fmt_inr)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No Client data found.")

    with tab2:
        df = compute_chemical(load_sheet("Greet_Powder_Chemical"))
        if not df.empty:
            total_amt = df["Amount_INR"].sum() if "Amount_INR" in df.columns else 0
            qty_total = df["Qty_Ton"].sum() if "Qty_Ton" in df.columns else 0
            c1, c2 = st.columns(2)
            with c1: kpi("Total Amount", fmt_inr(total_amt))
            with c2: kpi("Total Quantity", f"{qty_total:.2f} Ton")
            st.markdown("<br>", unsafe_allow_html=True)
            if not df.empty and "Item_Name" in df.columns and "Amount_INR" in df.columns:
                grouped = df.groupby("Item_Name")["Amount_INR"].sum().reset_index()
                fig = px.pie(grouped, names="Item_Name", values="Amount_INR",
                             title="Spend by Chemical/Powder",
                             color_discrete_sequence=px.colors.qualitative.Set2)
                fig.update_layout(
                    font_family="DM Sans", font_size=13,
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=10, r=10, t=45, b=10), height=320,
                )
                st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No Chemical/Powder data found.")

    with tab3:
        df = load_sheet("Production_Notes")
        if not df.empty:
            kpi("Total Production Entries", str(len(df)))
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No Production Notes found.")

elif nav == "💰 Financials":
    st.markdown("## 💰 Financials")
    st.markdown("---")

    tab1, tab2 = st.tabs(["💸 Cashflow", "👷 Labour Salary"])

    with tab1:
        df = load_sheet("Cashflow")
        if not df.empty:
            df["Amount_INR"] = pd.to_numeric(df["Amount_INR"], errors="coerce").fillna(0)
            cash_in = df[df["Type"] == "IN"]["Amount_INR"].sum() if "Type" in df.columns else 0
            cash_out = df[df["Type"] == "OUT"]["Amount_INR"].sum() if "Type" in df.columns else 0
            net = cash_in - cash_out
            c1, c2, c3 = st.columns(3)
            with c1: kpi("Total IN", fmt_inr(cash_in), "Revenue received")
            with c2: kpi("Total OUT", fmt_inr(cash_out), "Expenses paid")
            with c3: kpi("Net Balance", fmt_inr(net), "✅ Surplus" if net >= 0 else "⚠️ Deficit")
            st.markdown("<br>", unsafe_allow_html=True)
            st.plotly_chart(plotly_cashflow_bar(df), use_container_width=True)
            if "Date" in df.columns and "Amount_INR" in df.columns:
                df_in = df[df["Type"] == "IN"].copy() if "Type" in df.columns else pd.DataFrame()
                if not df_in.empty:
                    st.plotly_chart(plotly_line(df_in, "Date", "Amount_INR", "Cash IN Over Time", "#27ae60"), use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No Cashflow data found.")

    with tab2:
        df = load_sheet("Labour_Salary")
        if not df.empty:
            df["Amount_INR"] = pd.to_numeric(df["Amount_INR"], errors="coerce").fillna(0)
            total_salary = df["Amount_INR"].sum()
            c1, c2 = st.columns(2)
            with c1: kpi("Total Salary Paid", fmt_inr(total_salary))
            with c2: kpi("Total Workers Logged", str(len(df)))
            st.markdown("<br>", unsafe_allow_html=True)
            if "Worker_Name" in df.columns:
                by_worker = df.groupby("Worker_Name")["Amount_INR"].sum().reset_index().sort_values("Amount_INR", ascending=False)
                fig = px.bar(by_worker, x="Worker_Name", y="Amount_INR",
                             title="Salary by Worker",
                             color="Amount_INR",
                             color_continuous_scale=["#f8f9fb", "#e94560"],
                             text=by_worker["Amount_INR"].apply(fmt_inr))
                fig.update_layout(
                    font_family="DM Sans", font_size=13,
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=10, r=10, t=45, b=30), height=350,
                    coloraxis_showscale=False,
                )
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No Labour Salary data found.")