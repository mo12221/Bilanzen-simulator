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

        @keyframes flash {
            0% { background-color: #ffff99; }
            100% { background-color: transparent; }
        }
        .flash-change { animation: flash 2s ease-out; border-radius: 3px; padding: 0 2px; }
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
            "Assets": {"Forderung Bank A": 0},
            "Liabilities": {"Reserve Bank A": 0, "Guthaben Staat": 0}
        },
        "Bank A": {
            "Assets": {"Reserve bei ZB": 0, "Staatsanleihen": 0},
            "Liabilities": {"Kredit bei ZB":0,"Einlage Bürger": 0, "Eigenkapital Bank": 0}
        },
        "Bürger": {
            "Assets": {"Bankguthaben": 0},
            "Liabilities": {"Eigenkapital Bürger": 0}
        }
    }
    st.session_state.logs = ["Willkommen im Staats-Simulator!"]
    st.session_state.pending_steps = []
    st.session_state.highlights = []
    st.session_state.initialized = True

# 4. HILFSFUNKTION BILANZ
def show_bilanz(name):
    if name in st.session_state.balances:
        st.markdown(f"<h4>{name}</h4>", unsafe_allow_html=True)
        assets = st.session_state.balances[name]["Assets"]
        liabs = st.session_state.balances[name]["Liabilities"]

        a_list = [f'<div class="flash-change">{k}: {v}</div>' if k in st.session_state.highlights else f"{k}: {v}" for
                  k, v in assets.items()]
        l_list = [f'<div class="flash-change">{k}: {v}</div>' if k in st.session_state.highlights else f"{k}: {v}" for
                  k, v in liabs.items()]

        max_rows = max(len(a_list), len(l_list))
        a_list += [""] * (max_rows - len(a_list))
        l_list += [""] * (max_rows - len(l_list))

        df = pd.DataFrame({"Aktiva": a_list, "Passiva": l_list})
        st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)


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
    speed = st.slider("Speed (sek)", 0.0, 4.0, 1.0, key="gov_speed")

    st.markdown("### 🕹️ Steuerung")
    control_container = st.container(height=450, border=True)
    with control_container:
        st.write("**Bank**")
        if st.button("ZB Kredit erzeugen", use_container_width=True):
            st.session_state.pending_steps = [
                {"func": staat_prozess, "args": ("Kredit ZB", betrag_val, 1)},
                {"func": staat_prozess, "args": ("Kredit ZB", betrag_val, 2)}
            ]
            st.rerun()
        st.divider()
        if st.button("Anleihe kaufen", use_container_width=True):
            st.session_state.pending_steps = [
                {"func": staat_prozess, "args": ("verkaufen", betrag_val, 1)},
                {"func": staat_prozess, "args": ("verkaufen", betrag_val, 2)},
                {"func": staat_prozess, "args": ("verkaufen", betrag_val, 3)}
            ]
            st.rerun()
        st.write("**Staat**")
        if st.button("Anleihe erzeugen", use_container_width=True):
            staat_prozess("erzeugen", betrag_val, 1)
            st.rerun()
        st.divider()
        if st.button("Lohn zahlen (Staat)", use_container_width=True):
            st.session_state.pending_steps = [
                {"func": staat_prozess, "args": ("lohn", betrag_val, 1)},
                {"func": staat_prozess, "args": ("lohn", betrag_val, 2)},
                {"func": staat_prozess, "args": ("lohn", betrag_val, 3)}
            ]
            st.rerun()
        st.divider()
        st.write("**Bürger**")
        if st.button("5. Steuern zahlen (Bürger)", use_container_width=True):
            st.session_state.pending_steps = [
                {"func": staat_prozess, "args": ("steuern", betrag_val, 1)},
                {"func": staat_prozess, "args": ("steuern", betrag_val, 2)},
                {"func": staat_prozess, "args": ("steuern", betrag_val, 3)}
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
        show_bilanz("Bank A")

    st.divider()

    # ZWEITE ZEILE: Bürger (Zentriert durch leere Spalten links und rechts)
    row2_empty1, row2_empty2, row2_c2 = st.columns(3)
    with row2_c2:
        show_bilanz("Bürger")

# ---------------------------------------------------------
# 6. MOTOR (Für die Animationen)
# ---------------------------------------------------------
if st.session_state.get("pending_steps"):
    if st.session_state.highlights:
        # Kurze Pause, um das Highlight zu zeigen, dann löschen für den nächsten Flash
        st.session_state.highlights = []
        time.sleep(1)
        st.rerun()
    else:
        # Nächsten Schritt ausführen
        step = st.session_state.pending_steps.pop(0)
        step["func"](*step["args"])
        time.sleep(speed)
        st.rerun()