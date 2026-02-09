import streamlit as st
import pandas as pd
import time

from Transfers import prozess_kredit, lohnzahlung_prozess, interbank_transfer,prozess_kredit_intro, zb_kredit_prozess
from Game_play import get_mission
import matplotlib.pyplot as plt

# 1. KONFIGURATION
st.set_page_config(layout="wide", page_title="Wirtschafts-Simulator 2.0")

if "pending_steps" not in st.session_state:
    st.session_state.pending_steps = []

st.markdown("""
    <style>
        /* Hauptüberschriften (h1, h2) verkleinern */
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.2rem !important; }
        h3 { font-size: 1.0rem !important; }

        /* Die Namen über deinen Bilanzen (h4) */
        h4 { 
            font-size: 0.9rem !important; 
            font-weight: bold !important;
            margin-bottom: 0px !important;
            padding-bottom: 1px !important;
        }

        /* Die Schrift innerhalb der Tabellen (st.table) */
        .stTable td, .stTable th {
            font-size: 11px !important;
            padding: 2px 5px !important;
        }

        /* Den Abstand zwischen den Elementen verringern */
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
        }

        /* Abstand der Trennlinien (st.divider) drastisch reduzieren */
        hr {
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }

        /* Den Abstand zwischen den Spalten (st.columns) verringern */
        [data-testid="column"] {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
        }

        /* Den Abstand der Tabellen nach unten verkleinern */
        .stTable {
            margin-bottom: -1.5rem !important;
        }

        /* Abstand zwischen den einzelnen Elementen im Streamlit-Block */
        .element-container {
            margin-bottom: 0.2rem !important;
        }

        .real-werte {
                    font-size: 10px !important;
                    margin-top: -15px !important; /* Zieht den Text ganz nah an die Tabelle */
                    margin-bottom: 10px !important;
                    text-align: center;
                    font-family: sans-serif;
                }
        @keyframes flash {
                0% { background-color: #ffff99; } /* Helles Gelb am Anfang */
                100% { background-color: transparent; } /* Zurück zum Normalzustand */
            }

            .flash-change {
                animation: flash 2s ease-out;
            }
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
        
        /* Roter Flash: Was ändert sich JETZT? */
        @keyframes flash-action {
            0% { background-color: #ffcdd2; color: #b71c1c; } /* Hellrot mit dunkelroter Schrift */
            100% { background-color: transparent; }
        }
        .action-change {
            animation: flash-action 4s ease-out;
            font-weight: bold !important;
            color: #b71c1c !important; /* Dunkelrot für bessere Lesbarkeit */
            border: 1px solid #e53935;
            padding: 2px;
            border-radius: 3px;
        }
    </style>
    """, unsafe_allow_html=True)

# 2. INITIALISIERUNG DES SPEICHERS (Session State)
if 'initialized' not in st.session_state:
    entities = ["Bank A", "Zentralbank", "Bank B", "UK",
                "Bank C", "UI", "Eigentümer", "Arbeiter:innen"]

    st.session_state.balances = {
        "Zentralbank": {
            "Assets": {"Forderung Bank A": 0, "Forderung Bank B": 0},
            "Liabilities": {"Reserve Bank A": 0, "Reserve Bank B": 0}
        },
        "Bank A": {
            "Assets": {"Reserve bei ZB A": 0, "Kredite Kunde 1": 0},
            "Liabilities": {"Kredit bei ZB A": 0, "Einlage Kunde 1": 0, "Eigenkapital A": 0}
        },
        "Bank B": {
            "Assets": {"Reserve bei ZB B": 0, "Kredite Kunde 2": 0},
            "Liabilities": {"Kredit bei ZB B": 0, "Einlage Kunde 2": 0, "Eigenkapital B": 0}
        },
        "Kunde 1": {
            "Assets": {"Bankguthaben bei A": 0, "Sachvermögen 1": 100},
            "Liabilities": {"Kredit bei A": 0, "Eigenkapital 1": 100}
        },
        "Kunde 2": {
            "Assets": {"Bankguthaben bei B": 0, "Sachvermögen 2": 100},
            "Liabilities": {"Kredit bei B": 0, "Eigenkapital 2": 100}
        },
    }
    st.session_state.BIP_history = [0]  # Startwert für den Plot
    st.session_state.round_history = [0]
    st.session_state.previous_BIP = 0
    st.session_state.previous_I = 0
    st.session_state.previous_C = 0
    st.session_state.logs = ["Willkommen beim Simulator!"]
    st.session_state.current_round = 1
    st.session_state.actions_done = []
    st.session_state.highlights_action = []
    st.session_state.highlights_plan = []
    st.session_state.last_logged_round = 0
    st.session_state.initialized = True


# HILFSFUNKTION FÜR PRINT-ERSATZ
def log_info(text):
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    st.session_state.logs.append(f"Runde {st.session_state.current_round}: {text}")


# ---------------------------------------------------------
# 3. DAS SPIELFELD (LAYOUT)
# ---------------------------------------------------------

# Obere Sektion: Links Log, Rechts Bilanzen

col_control, col_tableau = st.columns([1, 3.5])

# --- RECHTE SPALTE: DIE BILANZEN ---
with col_tableau:
    st.markdown("<h3 style='text-align: center;'>📊 Wirtschafts-Tableau</h3>", unsafe_allow_html=True)

    # Deine r1, r2, r3 Reihen hier rein...
    # row1_col1, row1_col2, row1_col3 = st.columns(3) usw.


# --- BILANZ-GRID LAYOUT ---

def show_bilanz(name):
    if name in st.session_state.balances:
        st.markdown(f"#### {name}")
        assets = st.session_state.balances[name]["Assets"]
        liabs = st.session_state.balances[name]["Liabilities"]

        def format_cell(k, v):
            # Priorität 1: Aktuelle Änderung (Rot)
            if k in st.session_state.get("highlights_action", []):
                return f'<div class="action-change">{k}: {v}</div>'
            # Priorität 2: Geplanter Bereich (Gelb)
            elif k in st.session_state.get("highlights_plan", []):
                return f'<div class="plan-change">{k}: {v}</div>'
            return f"{k}: {v}"

        a_list = [format_cell(k, v) for k, v in assets.items()]
        l_list = [format_cell(k, v) for k, v in liabs.items()]

        # ... Rest der Funktion (DataFrame-Erstellung) wie gehabt ...

        # Symmetrie herstellen (auffüllen mit Leerzeichen)
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


with col_tableau:
    st.subheader("Wirtschafts-Tableau")
    # ERSTE ZEILE: Bank A | Zentralbank | Bank B
    row1_col1, row1_col2, row1_col3 = st.columns(3)
    with row1_col1:
        show_bilanz("Bank A")
    with row1_col2:
        show_bilanz("Zentralbank")
    with row1_col3:
        show_bilanz("Bank B")

    st.divider()

    # ZWEITE ZEILE: UK | Bank C | UI
    row2_col1, row2_col2, row2_col3 = st.columns(3)
    with row2_col1:
        show_bilanz("Kunde 1")
    with row2_col2:
        st.write("")
    with row2_col3:
        show_bilanz("Kunde 2")

# --- LINKE SPALTE: LOG & STEUERUNG ---
with col_control:
    st.markdown("### 📟 System-Log")
    log_box = st.container(height=150, border=True)
    with log_box:
        for msg in st.session_state.logs[-30:]:
            st.markdown(f"<p style='font-size: 10px; margin: 0;'>{msg}</p>", unsafe_allow_html=True)

    st.markdown("### 💰 Eingabe")
    betrag = st.number_input("Betrag für Aktionen", value=0, step=100, key="main_betrag")

    st.markdown("### 🕹️ Steuerung")
    control_box = st.container(height=400, border=True)
    with control_box:
        speed = st.slider("Speed", 0.0, 4.0, 2, key="intro_speed")
        zins_val = st.slider("Zinssatz (%)", 0.0, 0.20, 0.0, step=0.01)
        st.write("**Kredite (Geld schöpfen)**")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Kredit Kunde 1", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": prozess_kredit_intro, "args": (betrag, zins_val, "Kunde 1", "Bank A", speed, i)}
                    for i in range(1, 5)
                ]
                st.rerun()
        with c2:
            if st.button("Kredit Kunde 2", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": prozess_kredit, "args": (betrag, zins_val, "Kunde 2", "Bank B", speed, i)}
                    for i in range(1, 5)
                ]
                st.rerun()

        st.divider()
        # --- Unter "Steuerung" im control_box Bereich ---

        st.write("**Zentralbank-Liquidität**")
        zbc1, zbc2 = st.columns(2)
        with zbc1:
            if st.button("ZB-Kredit Bank A", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": zb_kredit_prozess,
                     "args": (betrag, "Bank A", speed, i)}
                    for i in range(1, 5)
                ]
                st.rerun()
        with zbc2:
            if st.button("ZB-Kredit Bank B", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": zb_kredit_prozess,
                     "args": (betrag, "Bank B", speed, i)}
                    for i in range(1, 5)
                ]
                st.rerun()

        st.divider()
        st.write("**Zahlungsverkehr (Transfer)**")
        t1, t2 = st.columns(2)

        with t1:
            if st.button("Transfer 1 ➔ 2", use_container_width=True):
                # Jetzt nur noch 5 Schritte (alt 3 bis 7)
                st.session_state.pending_steps = [
                    {"func": interbank_transfer,
                     "args": (betrag, "Kunde 1", "Kunde 2", "Bank A", "Bank B", speed, i)}
                    for i in range(1, 8)
                ]
                st.rerun()

        with t2:
            if st.button("Transfer 2 ➔ 1", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": interbank_transfer,
                     "args": (betrag, "Kunde 2", "Kunde 1", "Bank B", "Bank A", speed, i)}
                    for i in range(1, 8)
                ]
                st.rerun()

# --- MOTOR (Optimiert für Plan & Action Timing) ---
# --- PRÄZISIONS-MOTOR V4 (Einzelschritt-Garantie) ---
# --- PRÄZISIONS-MOTOR V5 (Sichtbarkeit für den letzten Schritt) ---
if st.session_state.get("pending_steps") or st.session_state.get("highlights_action"):

    # 1. Lösch-Phase: Wenn Rot leuchtet, löschen wir es für den nächsten Schritt
    if st.session_state.get("highlights_action"):
        # Wir warten hier NICHT (das haben wir nach der Aktion schon getan)
        st.session_state.highlights_action = []

        # Falls die Warteschlange jetzt leer ist, löschen wir auch den gelben Plan
        if not st.session_state.get("pending_steps"):
            st.session_state.highlights_plan = []

        time.sleep(1)  # Kurzer visueller Reset
        st.rerun()

    # 2. Aktions-Phase: Nächsten Schritt ausführen
    elif st.session_state.get("pending_steps"):
        current_step_data = st.session_state.pending_steps.pop(0)
        current_step_data["func"](*current_step_data["args"])

        # JEDER Schritt (auch der gelbe Plan und das letzte Rot) bekommt die Pause vom Slider
        waited_time = st.session_state.get("intro_speed", 2)
        time.sleep(waited_time)

        # Wir triggern den Rerun, damit das gerade gesetzte Highlight angezeigt wird
        st.rerun()
