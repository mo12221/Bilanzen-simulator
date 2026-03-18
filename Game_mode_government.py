import streamlit as st
import pandas as pd
import time
from Transfers import staat_prozess
# 1. KONFIGURATION & CSS
st.set_page_config(layout="wide", page_title="Staatsfinanzierungs-Simulator")

st.markdown("""
    <style>
        /* Den gesamten Hauptbereich nach oben schieben */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 0rem !important;
            max-width: 95% !important;
        }

        /* Überschriften extrem kompakt */
        h1 { font-size: 1.3rem !important; margin-top: -20px !important; }
        h2 { font-size: 1.2rem !important; margin-top: 0px !important; }
        h3 { font-size: 1.0rem !important; margin-bottom: 5px !important; }
        h4 { 
            font-size: 0.85rem !important; 
            font-weight: bold !important; 
            margin-bottom: 2px !important; 
            text-align: center;
            color: #31333F;
        }

        /* Tabellen noch flacher machen */
        .stTable { margin-bottom: -1.0rem !important; }
        .stTable td, .stTable th { font-size: 10px !important; padding: 1px 4px !important; }

        hr { margin-top: 0.4rem !important; margin-bottom: 0.4rem !important; }

    /* Gelber Plan: Was wird sich bewegen? */
        @keyframes flash-plan {
            0% { background-color: #fff9c4; } /* Sanftes Pastellgelb */
            100% { background-color: #fff9c4; } 
        }
        .plan-change {
            background-color: #fff9c4 !important;
            color: #000000 !important; /* Explizit schwarze Schrift */
            border: 1px solid #fbc02d;
            padding: 2px;
            border-radius: 3px;
            font-weight: 500;
        }
        
        /* GRÜNER Flash: Für Zunahmen (+) */
        @keyframes flash-green {
            0% { background-color: #c8e6c9; color: #1b5e20; }
            100% { background-color: transparent; }
        }
        .action-green {
            animation: flash-green 4s ease-out;
            font-weight: bold !important;
            color: #1b5e20 !important;
            border: 1px solid #2e7d32;
            padding: 2px;
            border-radius: 3px;
        }
    
        /* ROTER Flash: Für Abnahmen (-) */
        @keyframes flash-red {
            0% { background-color: #ffcdd2; color: #b71c1c; }
            100% { background-color: transparent; }
        }
        .action-red {
            animation: flash-red 4s ease-out;
            font-weight: bold !important;
            color: #b71c1c !important;
            border: 1px solid #c62828;
            padding: 2px;
            border-radius: 3px;
        }
    </style>
    """, unsafe_allow_html=True)

# 2. INITIALISIERUNG
if 'initialized' not in st.session_state:
    st.session_state.balances = {
        "Staat": {
            "Assets": {"Guthaben bei ZB": 0, "Anleihen Eigenbestand": 0},
            "Liabilities": {"Staatsanleihen (Gesamt)": 0, "Eigenkapital Staat": 0}
        },
        "Zentralbank": {
            "Assets": {"Forderung London Bank": 0, "Bestand Staatsanleihen": 0},
            "Liabilities": {"Bargeldumlauf":0,"Reserve London Bank": 0, "Guthaben Staat": 0}
        },
        "London Bank": {
            "Assets": {"Reserve bei ZB": 0, "Staatsanleihen": 0},
            "Liabilities": {"Kredit bei ZB":0,"Einlage Milton": 0, "Eigenkapital Bank": 0}
        },
        "Milton": {
            "Assets": {"Bankguthaben": 0, "Bargeld":0},
            "Liabilities": {"Eigenkapital Milton": 0}
        }
    }
    st.session_state.logs = ["Willkommen im Staats-Simulator!"]
    st.session_state.pending_steps = []
    st.session_state.highlights_red = []
    st.session_state.highlights_green = []
    st.session_state.highlights_plan = []
    st.session_state.initialized = True

# 4. HILFSFUNKTION BILANZ
def show_bilanz(name):
    if name in st.session_state.balances:
        st.markdown(f"#### {name}")
        assets = st.session_state.balances[name]["Assets"]
        liabs = st.session_state.balances[name]["Liabilities"]

        def format_cell(k, v):
            # 1. Priorität: Grün (Zunahme)
            if k in st.session_state.get("highlights_green", []):
                return f'<div class="action-green">{k}: {v}</div>'
            # 2. Priorität: Rot (Abnahme)
            elif k in st.session_state.get("highlights_red", []):
                return f'<div class="action-red">{k}: {v}</div>'
            # 3. Priorität: Plan (Gelb)
            elif k in st.session_state.get("highlights_plan", []):
                return f'<div class="plan-change">{k}: {v}</div>'
            return f"{k}: {v}"

        a_list = [format_cell(k, v) for k, v in assets.items()]
        l_list = [format_cell(k, v) for k, v in liabs.items()]

        max_rows = max(len(a_list), len(l_list))
        while len(a_list) < max_rows:
            a_list.append("")
        while len(l_list) < max_rows:
            l_list.append("")

        # Jetzt erstellen wir den DataFrame mit exakt ZWEI Spalten
        df = pd.DataFrame({
            "Aktiva": a_list,
            "Passiva": l_list
        })

        # Anzeige als kompakte Tabelle ohne Index-Spalte
        html_table = df.to_html(escape=False, index=False)
        st.write(html_table, unsafe_allow_html=True)


# ---------------------------------------------------------
# 5. DAS SPIELFELD (PERMANENTES LAYOUT)
# ---------------------------------------------------------

# Hier definieren wir die Spalten im Hauptbereich (nicht in der Sidebar!)
col_control, col_tableau = st.columns([1, 3])

# --- LINKE SPALTE: LOG & STEUERUNG (Immer offen) ---
with col_control:
    st.markdown("### 📟 System-Log")
    log_box = st.container(height=180, border=True)
    with log_box:
        for msg in reversed(st.session_state.logs):
            st.markdown(f"<p style='font-size: 10px; margin: 0; line-height: 1.2;'>{msg}</p>", unsafe_allow_html=True)

    st.markdown("### 💰 Eingabe")
    betrag_val = st.number_input("Betrag", value=100, step=10, key="gov_betrag")
    speed = st.slider("Dauer Animation (sek)", 0.0, 4.0, 1.0, key="gov_speed")

    st.markdown("### 🕹️ Steuerung")
    control_container = st.container(height=450, border=True)
    with control_container:
        st.write("**Bank**")
        if st.button("Gewähre ZB-Kredit", use_container_width=True,
                     help="London Bank verschuldet sich bei der ZB, um Reserven zu erhalten."):
            st.session_state.pending_steps = [
                {"func": staat_prozess, "args": ("Kredit ZB", betrag_val, i)}
                for i in range(1, 5)
            ]
            st.rerun()


        if st.button("Anleihe kaufen", use_container_width=True):
            st.session_state.pending_steps = [
                {"func": staat_prozess, "args": ("verkaufen", betrag_val, i)}
                for i in range(1, 6)
            ]
            st.rerun()
        st.divider()

        st.write("**Zentralbank (QE)**")
        if st.button("Starte QE-Ankauf", use_container_width=True,
                     help="Die ZB kauft Anleihen ab und 'flutet' die Bank mit Reserven."):
            st.session_state.pending_steps = [
                {"func": staat_prozess, "args": ("QE", betrag_val, i)}
                for i in range(1, 5)
            ]
            st.rerun()
        st.divider()

        st.write("**Staat**")
        if st.button("Anleihe erzeugen", use_container_width=True):
            st.session_state.pending_steps = [
                {"func": staat_prozess, "args":("erzeugen", betrag_val, i)}
                for i in range(1, 4)
            ]
            st.rerun()
        st.divider()
        if st.button("Lohn zahlen (Staat)", use_container_width=True):
            st.session_state.pending_steps = [
                {"func": staat_prozess, "args": ("lohn", betrag_val, i)}
                    for i in range(1, 7)
            ]
            st.rerun()
        st.divider()
        st.write("**Milton**")
        if st.button("5. Steuern zahlen (Milton)", use_container_width=True):
            st.session_state.pending_steps = [
                {"func": staat_prozess, "args": ("steuern", betrag_val, i)}
                for i in range(1, 7)
            ]
            st.rerun()
        if st.button("6. Bargeld abheben (Milton)", use_container_width=True):
            st.session_state.pending_steps = [
                {"func": staat_prozess, "args": ("bargeld", betrag_val, i)}
                for i in range(0, 5)
            ]
            st.rerun()

        st.divider()
        if st.button("🔄 Simulator Reset", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# --- RECHTE SPALTE: DIE BILANZEN ---
with col_tableau:
    st.markdown("<h2 style='text-align: center; margin-bottom: 10px;'>🏛️ Staatsfinanzierungs-Tableau</h2>", unsafe_allow_html=True)

    # ERSTE ZEILE: Staat | Zentralbank | Bank A
    row1_c1, row1_c2, row1_c3 = st.columns(3)
    with row1_c1:
        show_bilanz("Staat")
    with row1_c2:
        show_bilanz("Zentralbank")
    with row1_c3:
        show_bilanz("London Bank")

    st.divider()

    # ZWEITE ZEILE: Bürger (Zentriert durch leere Spalten links und rechts)
    row2_empty1, row2_empty2, row2_c2 = st.columns(3)
    with row2_c2:
        show_bilanz("Milton")

# ---------------------------------------------------------
# 6. MOTOR (Für die Animationen)
# ---------------------------------------------------------
has_active_highlights = len(st.session_state.get("highlights_green", [])) > 0 or len(st.session_state.get("highlights_red", [])) > 0

if st.session_state.get("pending_steps") or has_active_highlights:

    # 1. LÖSCH-PHASE: Wenn Farbe leuchtet, löschen wir sie für den nächsten Schritt
    if has_active_highlights:
        # Wir lassen die Farbe für die Dauer des Sliders stehen (wurde unten pausiert)
        st.session_state.highlights_green = []
        st.session_state.highlights_red = []

        if not st.session_state.get("pending_steps"):
            st.session_state.highlights_plan = []

        time.sleep(1) # Kurzer technischer Reset
        st.rerun()

    # 2. AKTIONS-PHASE: Nächsten Schritt ausführen
    elif st.session_state.get("pending_steps"):
        current_step_data = st.session_state.pending_steps.pop(0)
        current_step_data["func"](*current_step_data["args"])

        # JEDER Schritt (auch der gelbe Plan) bekommt die Pause vom Slider
        waited_time = st.session_state.get("intro_speed", 1)
        time.sleep(waited_time)

        # Rerun, damit das gerade gesetzte Highlight (Grün oder Rot) angezeigt wird
        st.rerun()
