import streamlit as st
import pandas as pd
import time
from Transfers import prozess_kredit, lohnzahlung_prozess, interbank_transfer,prozess_kredit_intro
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
    st.session_state.highlights = []
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
        st.markdown(f"<h4 style='text-align: center;'>{name}</h4>", unsafe_allow_html=True)

        assets_dict = st.session_state.balances[name]["Assets"]
        liabs_dict = st.session_state.balances[name]["Liabilities"]

        assets = st.session_state.balances[name]["Assets"]
        liabs = st.session_state.balances[name]["Liabilities"]
        a_list = []
        for k, v in assets.items():
            # Check: Ist dieses Konto in der Liste der zuletzt geänderten?
            if k in st.session_state.get("highlights", []):
                a_list.append(f'<div class="flash-change">{k}: {v}</div>')
            else:
                a_list.append(f"{k}: {v}")
        l_list = []
        for k, v in liabs_dict.items():
            # Check: Ist dieses Konto in der Liste der zuletzt geänderten?
            if k in st.session_state.get("highlights", []):
                l_list.append(f'<div class="flash-change">{k}: {v}</div>')
            else:
                l_list.append(f"{k}: {v}")

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
        speed = st.slider("Speed", 0.0, 4.0, 1.0, key="intro_speed")
        zins_val = st.slider("Zinssatz (%)", 0.0, 0.20, 0.0, step=0.01)
        st.write("**Kredite (Geld schöpfen)**")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Kredit Kunde 1", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": prozess_kredit_intro, "args": (betrag, zins_val, "Kunde 1", "Bank A", speed, 1)},
                    {"func": prozess_kredit_intro, "args": (betrag, zins_val, "Kunde 1", "Bank A", speed, 2)}
                ]
                st.rerun()
        with c2:
            if st.button("Kredit Kunde 2", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": prozess_kredit, "args": (betrag, zins_val, "Kunde 2", "Bank B", speed, 1)},
                    {"func": prozess_kredit, "args": (betrag, zins_val, "Kunde 2", "Bank B", speed, 2)}
                ]
                st.rerun()

        st.divider()
        st.write("**Überweisungen (Geld transferieren)**")
        t1, t2 = st.columns(2)
        from Transfers import interbank_transfer  # Import hier oder oben

        with t1:
            if st.button("Transfer 1 -> 2", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": interbank_transfer,
                     "args": (betrag, "Kunde 1", "Kunde 2", "Bank A", "Bank B", speed, 1)},
                    {"func": interbank_transfer,
                     "args": (betrag, "Kunde 1", "Kunde 2", "Bank A", "Bank B", speed, 2)},
                    {"func": interbank_transfer,
                     "args": (betrag, "Kunde 1", "Kunde 2", "Bank A", "Bank B", speed, 3)},
                    {"func": interbank_transfer,
                     "args": (betrag, "Kunde 1", "Kunde 2", "Bank A", "Bank B", speed, 4)},
                    {"func": interbank_transfer,
                     "args": (betrag, "Kunde 1", "Kunde 2", "Bank A", "Bank B", speed, 5)},
                    {"func": interbank_transfer,
                     "args": (betrag, "Kunde 1", "Kunde 2", "Bank A", "Bank B", speed, 6)},
                    {"func": interbank_transfer,
                     "args": (betrag, "Kunde 1", "Kunde 2", "Bank A", "Bank B", speed, 7)}
                ]
                st.rerun()
        with t2:
            if st.button("Transfer 2 -> 1", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": interbank_transfer,
                     "args": (betrag, "Kunde 2", "Kunde 1", "Bank B", "Bank A", speed, 1)},
                    {"func": interbank_transfer,
                     "args": (betrag, "Kunde 2", "Kunde 1", "Bank B", "Bank A", speed, 2)},
                    {"func": interbank_transfer,
                     "args": (betrag, "Kunde 2", "Kunde 1", "Bank B", "Bank A", speed, 3)},
                    {"func": interbank_transfer,
                     "args": (betrag, "Kunde 2", "Kunde 1", "Bank B", "Bank A", speed, 4)},
                    {"func": interbank_transfer,
                     "args": (betrag, "Kunde 2", "Kunde 1", "Bank B", "Bank A", speed, 5)},
                    {"func": interbank_transfer,
                     "args": (betrag, "Kunde 2", "Kunde 1", "Bank B", "Bank A", speed, 6)},
                    {"func": interbank_transfer,
                     "args": (betrag, "Kunde 2", "Kunde 1", "Bank B", "Bank A", speed, 7)},
                ]
                st.rerun()


# --- MOTOR (Optimiert für perfektes Timing) ---
if st.session_state.get("pending_steps"):

    # Prüfen, ob wir gerade in einer "Lösch-Phase" sind
    # Wir nutzen ein Hilfs-Flag, um zu wissen, ob wir gerade erst gelöscht haben
    if st.session_state.get("highlights") != []:
        # Highlights sind da -> wir löschen sie jetzt für den nächsten Flash
        st.session_state.highlights = []
        time.sleep(1)  # Ganz kurzer Moment für den Browser-Reset
        st.rerun()

    else:
        # Highlights sind leer -> jetzt führen wir den nächsten echten Schritt aus
        current_action = st.session_state.pending_steps.pop(0)
        current_action["func"](*current_action["args"])

        # Jetzt leuchten die neuen Highlights. Wir warten die volle eingestellte Zeit,
        # damit der Nutzer die Buchung in Ruhe lesen kann.
        current_speed = st.session_state.get("intro_speed", 1.0)
        time.sleep(current_speed)

        # Nach der Pause triggern wir den Rerun.
        # Da Highlights jetzt NICHT leer sind, geht er oben in den "Lösch-Teil".
        st.rerun()
