import streamlit as st
import requests
import urllib.parse

DEFAULT_OPENROUTER_KEY = "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"


def ask_stock_ai(api_key: str, prompt: str, current_symbol: str, stock_info: dict, watchlist: list) -> str:
    """Sendet eine Anfrage über die OpenRouter API mit dem Modell 'openrouter/free'."""
    if not api_key:
        return "⚠️ Bitte gib zuerst einen gültigen OpenRouter API-Key an."

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
    Beantworte die Anfrage des Nutzers präzise, auf Deutsch und fass dich kurz (max. 3-4 Sätze oder übersichtliche Stichpunkte).
    Falls der Nutzer nach einer Kauf- oder Verkaufsempfehlung fragt:
    1. Gib eine kurze, klare Einschätzung (KAUFEN / HALTEN / VERKAUFEN mit prägnanter Begründung).
    2. FÜGE AM ENDE UNBEDINGT DIESEN SATZ HINZU:
       "⚠️ Haftungsausschluss: Keine Anlageberatung. Keine Haftung für Verluste."
    
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


def render_ai_top_bar(current_symbol: str, stock_info: dict, watchlist: list):
    """Rendert ein kompaktes KI-Pop-up-Icon am oberen Rand der Hauptseite."""
    
    # Zustand initialisieren
    if "latest_ai_answer" not in st.session_state:
        st.session_state.latest_ai_answer = ""
    if "speak_ai_answer" not in st.session_state:
        st.session_state.speak_ai_answer = False

    # Kompaktes Top-Layout: KI-Button oben links
    col_icon, col_status = st.columns([1, 5])

    with col_icon:
        # Erstellt den kleinen Popover-Button oben links
        with st.popover("🤖 KI-Assistent", use_container_width=True):
            st.markdown("### 🤖 KI-Analyst")
            st.caption("Einschätzungen, Kaufempfehlungen & Kennzahlen-Checks")
            
            # Wichtiger Disclaimer
            st.warning("⚖️ **Keine Anlageberatung:** Die KI-Einschätzungen erfolgen ohne Gewähr. Der Betreiber haftet nicht für etwaige Verluste.")
            
            # API Key Key-Input
            api_key = st.text_input(
                "🔑 OpenRouter API-Key:", 
                value=DEFAULT_OPENROUTER_KEY,
                type="password"
            )

            # Quick-Buttons für Kaufempfehlungen
            st.markdown("**⚡ Schnell-Anfrage:**")
            q_col1, q_col2 = st.columns(2)
            quick_prompt = None
            if q_col1.button("💡 Kaufempfehlung?"):
                quick_prompt = f"Gib mir eine kurze Kaufempfehlung für {current_symbol}."
            if q_col2.button("📊 Quick-Check"):
                quick_prompt = f"Analysiere kurz die Kennzahlen von {current_symbol}."

            # Eingabefeld
            user_prompt = st.text_input("Deine Frage an die KI:", placeholder=f"Z. B. Sollte ich {current_symbol} jetzt kaufen?")
            
            if quick_prompt:
                user_prompt = quick_prompt

            if st.button("🚀 KI Anfragen", type="primary") and user_prompt:
                with st.spinner("KI analysiert..."):
                    answer = ask_stock_ai(api_key, user_prompt, current_symbol, stock_info, watchlist)
                    st.session_state.latest_ai_answer = answer
                    st.rerun()

    # Zeige die KI-Antwort direkt oben am Hauptschirm an, wenn eine vorliegt
    if st.session_state.latest_ai_answer:
        st.info(f"**🤖 KI-Einschätzung zu {current_symbol}:**\n\n" + st.session_state.latest_ai_answer)
        
        # Vorlese-Button & Vorlesewidget (per JavaScript Web Speech API)
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("🔊 Antwort vorlesen"):
                # Clean text for speech JS
                clean_text = st.session_state.latest_ai_answer.replace('"', "'").replace("\n", " ")
                js_code = f"""
                <script>
                    var msg = new SpeechSynthesisUtterance("{clean_text}");
                    msg.lang = "de-DE";
                    window.speechSynthesis.speak(msg);
                </script>
                """
                st.components.v1.html(js_code, height=0)
        with col_btn2:
            if st.button("❌ Schließen"):
                st.session_state.latest_ai_answer = ""
                st.rerun()