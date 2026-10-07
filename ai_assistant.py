import streamlit as st
import requests

# ==============================================================================
# 🔑 API-KEY EINSTELLUNG:
# Hier deinen OpenRouter Key eintragen oder leer lassen für manuelle Eingabe in der UI
# ==============================================================================
DEFAULT_OPENROUTER_KEY = ""


def ask_stock_ai(api_key: str, prompt: str, current_symbol: str, stock_info: dict, watchlist: list) -> str:
    """Sendet eine Anfrage über die OpenRouter API mit dem Modell 'openrouter/free'."""
    if not api_key:
        return "⚠️ Bitte gib zuerst einen gültigen OpenRouter API-Key in der Sidebar ein."

    context = f"""
    Du bist ein erfahrener KI-Finanz- und Aktien-Analyst in einem professionellen Dashboard.
    
    Aktuelle Daten zur ausgewählten Aktie:
    - Symbol: {current_symbol}
    - Unternehmensname: {stock_info.get('longName', current_symbol)}
    - Aktueller Kurs: {stock_info.get('currentPrice', 'N/A')} {stock_info.get('currency', '')}
    - KGV (P/E Ratio): {stock_info.get('trailingPE', 'N/A')}
    - Marktkapitalisierung: {stock_info.get('marketCap', 'N/A')}
    - Aktuelle Watchlist des Nutzers: {', '.join(watchlist)}
    
    Aufgabe:
    Beantworte die Anfrage des Nutzers präzise, analytisch und auf Deutsch. 
    Falls der Nutzer nach einer Kauf- oder Verkaufsempfehlung fragt:
    1. Gib eine klare, nachvollziehbare Einschätzung (z.B. Einschätzung: KAUFEN / HALTEN / VERKAUFEN mit Begründung basierend auf Kennzahlen/Marktlage).
    2. Hebe Chancen und Risiken hervor.
    3. FÜGE AM ENDE JEDER ANTWORT UNBEDINGT DIESEN SATZ HINZU:
       "⚠️ *Haftungsausschluss: Dies ist keine Anlageberatung. Alle Angaben ohne Gewähr. Keine Haftung für Verluste oder Schäden.*"
    
    Frage des Nutzers: {prompt}
    """

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "Stock Dashboard Pro"
    }

    payload = {
        "model": "openrouter/free",
        "messages": [
            {"role": "user", "content": context}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            error_msg = response.json().get('error', {}).get('message', response.text)
            return f"⚠️ OpenRouter Fehler ({response.status_code}): {error_msg}"
            
    except Exception as e:
        return f"Fehler bei der Verbindung zu OpenRouter: {str(e)}"


def render_ai_sidebar(current_symbol: str, stock_info: dict, watchlist: list):
    """Rendert das OpenRouter KI-Chat-UI in der Streamlit-Sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 KI-Finanzassistent")

    # Wichtiger Haftungsausschluss-Banner
    st.sidebar.warning(
        "⚖️ **Rechtlicher Hinweis:**\n\n"
        "Die KI gibt automatische Analysen & Einschätzungen. "
        "Dies stellt **keine Finanzberatung** dar. "
        "Für etwaige Anlageentscheidungen oder Verluste wird **keinerlei Haftung** übernommen."
    )

    # API-Key Eingabefeld
    openrouter_api_key = st.sidebar.text_input(
        "🔑 OpenRouter API-Key:", 
        value=DEFAULT_OPENROUTER_KEY,
        type="password", 
        placeholder="sk-or-v1-...",
        help="Erstelle dir einen Key unter https://openrouter.ai/keys"
    )

    # Schnell-Aktionsbuttons für Kaufempfehlung
    st.sidebar.markdown("**⚡ KI-Schnellanalyse:**")
    col_ai1, col_ai2 = st.sidebar.columns(2)
    quick_prompt = None
    if col_ai1.button("💡 Kaufempfehlung?"):
        quick_prompt = f"Gib mir eine Kaufempfehlung und Risikoanalyse für die Aktie {current_symbol}."
    if col_ai2.button("📊 Kennzahlen-Check"):
        quick_prompt = f"Analysiere die Kennzahlen (KGV, Marktkapitalisierung) von {current_symbol}."

    # Chat-Verlauf im Session-State speichern
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []

    # Chat-Bereich
    with st.sidebar.expander("💬 KI-Chat öffnen", expanded=True):
        # Bisherigen Verlauf anzeigen
        for msg in st.session_state.ai_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        user_prompt = st.chat_input(f"Frage zu {current_symbol}...")
        
        # Falls ein Schnell-Button geklickt wurde
        if quick_prompt:
            user_prompt = quick_prompt

        if user_prompt:
            st.session_state.ai_messages.append({"role": "user", "content": user_prompt})
            
            with st.spinner("KI analysiert die Aktie..."):
                answer = ask_stock_ai(openrouter_api_key, user_prompt, current_symbol, stock_info, watchlist)
                st.session_state.ai_messages.append({"role": "assistant", "content": answer})
                st.rerun()