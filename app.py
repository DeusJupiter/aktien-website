import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import json
import os
from ai_assistant import render_ai_sidebar

# --- PAGE SETUP ---
st.set_page_config(page_title="Aktien-Dashboard Pro", page_icon="📈", layout="wide")

# --- CUSTOM CSS LADEN ---
def load_css(css_file):
    if os.path.exists(css_file):
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")

st.title("📈 Mein Aktien-Dashboard Pro")

# --- CACHED FUNCTIONS ---
@st.cache_data(ttl=3600)
def search_tickers(query):
    """Sucht nach Unternehmensnamen und gibt eine Liste passender Ticker zurück."""
    if not query:
        return [("Apple Inc.", "AAPL")]
    
    clean_q = query.strip()
    results = []
    
    try:
        search_res = yf.Search(clean_q, max_results=5).quotes
        for quote in search_res:
            symbol = quote.get('symbol')
            shortname = quote.get('shortname') or quote.get('longname') or symbol
            if symbol:
                results.append((f"{shortname} ({symbol})", symbol))
    except Exception:
        pass

    if not results:
        results.append((clean_q.upper(), clean_q.upper()))
        
    return results

@st.cache_data(ttl=300)
def get_ticker_info(symbol):
    try:
        t = yf.Ticker(symbol)
        return t.info
    except Exception:
        return {}

@st.cache_data(ttl=300)
def get_ticker_history(symbol, period):
    try:
        t = yf.Ticker(symbol)
        return t.history(period=period)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_ticker_news(symbol):
    try:
        t = yf.Ticker(symbol)
        return t.news or []
    except Exception:
        return []

@st.cache_data(ttl=600)
def get_tops_flops_data(symbols):
    data = []
    for s in symbols:
        try:
            t = yf.Ticker(s)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[-2]
                curr_close = hist['Close'].iloc[-1]
                change_pct = ((curr_close - prev_close) / prev_close) * 100
                data.append({"Symbol": s, "Kurs": round(curr_close, 2), "Änderung (%)": round(change_pct, 2)})
        except Exception:
            pass
    return pd.DataFrame(data)

# --- WATCHLIST FUNKTIONALITÄT ---
WATCHLIST_FILE = "watchlist.json"

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return ["AAPL", "MSFT", "TSLA", "NVDA", "SAP.DE"]

def save_watchlist(watchlist_data):
    try:
        with open(WATCHLIST_FILE, "w") as f:
            json.dump(watchlist_data, f)
    except Exception:
        pass

watchlist = load_watchlist()

# --- SIDEBAR: SUCHE & EINSTELLUNGEN ---
st.sidebar.header("🔍 Suche & Einstellungen")

user_search = st.sidebar.text_input(
    "Firma oder Symbol eingeben:", 
    value="Apple",
    placeholder="z. B. Apple, Tesla, BMW, NVDA..."
)

# Suchtreffer abrufen
search_results = search_tickers(user_search)
options_dict = {label: sym for label, sym in search_results}

selected_option = st.sidebar.selectbox(
    "Passende Aktie auswählen:", 
    options=list(options_dict.keys()),
    index=0
)

symbol = options_dict[selected_option]

st.sidebar.markdown("---")
st.sidebar.subheader("⭐ Meine Watchlist")

# Watchlist-Buttons
col_fav1, col_fav2 = st.sidebar.columns(2)
if symbol not in watchlist:
    if col_fav1.button("⭐ Zu Favoriten"):
        watchlist.append(symbol)
        save_watchlist(watchlist)
        st.rerun()
else:
    if col_fav2.button("❌ Aus Favoriten"):
        watchlist.remove(symbol)
        save_watchlist(watchlist)
        st.rerun()

selected_from_watchlist = st.sidebar.radio("Favorit auswählen:", watchlist)
if st.sidebar.button("Favorit laden"):
    symbol = selected_from_watchlist

zeitraum = st.sidebar.selectbox("Zeitraum:", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=3)

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Indikatoren")
show_sma50 = st.sidebar.checkbox("SMA 50 (50-Tage-Durchschnitt)", value=True)
show_sma200 = st.sidebar.checkbox("SMA 200 (200-Tage-Durchschnitt)", value=False)

# --- UNTERNEHMENSKENNZAHLEN ZUERST LADEN ---
info = get_ticker_info(symbol)

# --- KI-ASSISTENT IN SIDEBAR EINBINDEN ---
render_ai_sidebar(symbol, info, watchlist)


# --- HAUPTBEREICH: UNTERNEHMENSKENNZAHLEN ANZEIGEN ---
if info:
    company_name = info.get('longName') or info.get('shortName') or symbol
    st.subheader(f"Unternehmensdaten: {company_name} ({symbol})")

    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose') or 0
    prev_close = info.get('previousClose') or current_price
    
    delta_val = current_price - prev_close if current_price and prev_close else 0
    delta_pct = (delta_val / prev_close * 100) if prev_close else 0
    
    market_cap = info.get('marketCap')
    market_cap_str = f"{market_cap / 1e9:.2f} Mrd. $" if market_cap else "N/A"
    pe_ratio = round(info.get('trailingPE'), 2) if info.get('trailingPE') else "N/A"
    
    div_yield_val = info.get('dividendYield')
    div_yield_str = f"{round(div_yield_val * 100, 2)}%" if div_yield_val is not None else "N/A"

    currency = info.get('currency', 'USD')
    
    col_kpi1.metric("Aktueller Kurs", f"{current_price} {currency}", f"{delta_val:+.2f} {currency} ({delta_pct:+.2f}%)")
    col_kpi2.metric("Marktkapitalisierung", market_cap_str)
    col_kpi3.metric("KGV (P/E Ratio)", pe_ratio)
    col_kpi4.metric("Dividendenrendite", div_yield_str)
else:
    st.warning(f"Kennzahlen für '{symbol}' konnten nicht geladen werden.")

st.markdown("---")


# --- HAUPTLAYOUT: CHART & TOPS/FLOPS ---
col_chart, col_tops_flops = st.columns([3, 1])

# --- LINKER BEREICH: CHART & NEWS ---
with col_chart:
    st.subheader(f"Aktienchart: {symbol}")
    df = get_ticker_history(symbol, zeitraum)

    if not df.empty:
        fig = go.Figure()

        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=symbol
        ))

        if show_sma50:
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            fig.add_trace(go.Scatter(
                x=df.index, y=df['SMA_50'],
                mode='lines', name='SMA 50',
                line=dict(color='orange', width=1.5)
            ))

        if show_sma200:
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            fig.add_trace(go.Scatter(
                x=df.index, y=df['SMA_200'],
                mode='lines', name='SMA 200',
                line=dict(color='royalblue', width=1.5)
            ))

        fig.update_layout(
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            height=500,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="#1e222d",
            plot_bgcolor="#1e222d"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"Keine Kursdaten für '{symbol}' gefunden.")

    st.markdown("---")
    st.subheader(f"📰 Aktuelle Nachrichten zu {symbol}")
    news_items = get_ticker_news(symbol)
    
    if news_items:
        for item in news_items[:4]:
            title = item.get('title')
            link = item.get('link')
            publisher = item.get('publisher', 'Quelle unbekannt')
            if title and link:
                st.markdown(f"- **[{title}]({link})** *(Quelle: {publisher})*")
    else:
        st.info("Keine aktuellen Nachrichten verfügbar.")


# --- RECHTER BEREICH: TOPS & FLOPS ---
with col_tops_flops:
    st.subheader("🚀 Tops & Flops")
    watch_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "SAP.DE"]
    overview_df = get_tops_flops_data(watch_symbols)
    
    if not overview_df.empty:
        tops = overview_df.sort_values(by="Änderung (%)", ascending=False).head(3)
        flops = overview_df.sort_values(by="Änderung (%)", ascending=True).head(3)
        
        st.markdown("**Top Gewinner:**")
        st.dataframe(tops, hide_index=True)
        
        st.markdown("**Top Verlierer:**")
        st.dataframe(flops, hide_index=True)

# --- FOOTER / DISCLAIMER ---
st.markdown("---")
st.caption("ℹ️ **Haftungsausschluss:** Alle Daten (Kurse, Kennzahlen, KI-Analysen) dienen ausschließlich Informationszwecken und stellen keine Anlageberatung dar. Es wird keine Garantie für die Richtigkeit oder Vollständigkeit übernommen.")