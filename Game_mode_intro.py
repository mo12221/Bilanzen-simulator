import streamlit as st
import pandas as pd
import time
import altair as alt

from Transfers import prozess_kredit, lohnzahlung_prozess, interbank_transfer, prozess_kredit_intro, zb_kredit_prozess, \
    bargeld_intro
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

# 2. INITIALISIERUNG DES SPEICHERS (Session State)
if 'initialized' not in st.session_state:
    st.session_state.balances = {
        "Bank of England (BoE)": {
            "Assets": {"Forderung London Bank": 0, "Forderung Edinburgh Bank": 0},
            "Liabilities": {"Reserve London Bank": 0, "Reserve Edinburgh Bank": 0, "Bargeldumlauf": 0}
        },
        "London Bank (LB)": {
            "Assets": {"Reserve bei BoE LB": 0, "Kredite Karl": 0, "Kredite Friedrich": 0,
                       "Staatsanleihen LB": 200, "Staatsanleihen (verpfändet) LB": 0},
            "Liabilities": {"Refinanzierungskredit bei BoE LB": 0, "Einlage Karl": 0, "Einlage Friedrich": 0, "Eigenkapital LB": 200}
        },
        "Edinburgh Bank (EB)": {
            "Assets": {"Reserve bei BoE EB": 0, "Kredite Adam": 0, "Staatsanleihen EB": 100, "Staatsanleihen (verpfändet) EB": 0},
            "Liabilities": {"Refinanzierungskredit bei BoE EB": 0, "Einlage Adam": 0, "Eigenkapital EB": 100}
        },
        "Karl": {
            "Assets": {"Bankguthaben Karl bei LB": 0, "Bargeld K.": 0, "Sachvermögen K.": 100},
            "Liabilities": {"Darlehen bei LB": 0, "Eigenkapital K.": 100}
        },
        "Adam": {
            "Assets": {"Bankguthaben Adam bei EB": 0, "Bargeld A.": 0, "Sachvermögen A.": 100},
            "Liabilities": {"Darlehen Adam bei EB": 0, "Eigenkapital A.": 100}
        },
        "Friedrich": {
            "Assets": {"Bankguthaben Friedrich bei LB": 0, "Bargeld F.": 0, "Sachvermögen F.": 100},
            "Liabilities": {"Darlehen Friedrich bei LB": 0, "Eigenkapital F.": 100}
        }
    }
    st.session_state.BIP_history = [0]  # Startwert für den Plot
    st.session_state.round_history = [0]
    st.session_state.previous_BIP = 0
    st.session_state.previous_I = 0
    st.session_state.previous_C = 0
    st.session_state.logs = ["Willkommen beim Simulator!"]
    st.session_state.current_round = 1
    st.session_state.actions_done = []
    st.session_state.highlights_red = []
    st.session_state.highlights_green = []
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


with col_tableau:
    st.subheader("Wirtschafts-Tableau")

    # ERSTE ZEILE: Bank A | Zentralbank | Bank B
    row1_col1, row1_col2, row1_col3 = st.columns(3)
    with row1_col1:
        show_bilanz("London Bank (LB)")
    with row1_col2:
        # Die Zentralbank bleibt oben (wirkt dadurch 'angehoben')
        show_bilanz("Bank of England (BoE)")
    with row1_col3:
        show_bilanz("Edinburgh Bank (EB)")

    st.divider()

    # ZWEITE ZEILE: Karl | Friedrich | Adam
    row2_col1, row2_col2, row2_col3 = st.columns(3)
    with row2_col1:
        show_bilanz("Karl")
    with row2_col2:
        show_bilanz("Friedrich")
    with row2_col3:
        show_bilanz("Adam")

    # --- MITTIGE GELDMENGEN-ANZEIGE UNTEN ---
    st.write("")
    # Wir erstellen 3 Spalten, nutzen aber nur die mittlere (Breite 2), um M0/M1 zu zentrieren
    _, center_col, _ = st.columns([1, 2, 1])

    with center_col:
        st.write("### ⚖️ Monetäre Aggregate: M0 = ZB-Geld | M1 = Privates Geld")

        # Berechnung (Beispielwerte aus deinem System)
        m0 = sum(st.session_state.balances["Bank of England (BoE)"]["Liabilities"].values())

        # M1 Summe (Karl + Friedrich + Adam + Milton)
        m1 = (st.session_state.balances["London Bank (LB)"]["Liabilities"].get("Einlage Karl", 0) +
              st.session_state.balances["London Bank (LB)"]["Liabilities"].get("Einlage Friedrich", 0) +
              st.session_state.balances["Edinburgh Bank (EB)"]["Liabilities"].get("Einlage Adam", 0))

        # --- 3. ANZEIGE ALS LIVE-BALKEN ---
        # Daten für das Diagramm vorbereiten
        df = pd.DataFrame({
            "Geldmenge": ["Basisgeld (M0)", "Giralgeld (M1)"],
            "Betrag": [m0, m1]
        })

        chart = alt.Chart(df).mark_bar(size=40).encode(  # size=40 macht die Balken schön dünn!
            x=alt.X("Geldmenge:N",
                    axis=alt.Axis(
                        labelAngle=0,  # 0 Grad = Perfekt im Querformat/Horizontal!
                        labelFontSize=12,
                        title=None
                    )),
            y=alt.Y("Betrag:Q", title="Betrag in £"),
            color=alt.Color("Geldmenge:N", legend=None, scale=alt.Scale(range=["#1f77b4", "#ff7f0e"]))
            # Blau für M0, Orange für M1
        ).properties(
            width=300,  # Begrenzt die Gesamtbreite des Diagramms
            height=250  # Höhe des Diagramms
        )

        # Diagramm im Streamlit anzeigen
        st.altair_chart(chart, width="stretch")

        st.caption("💡 **M0** = ZB-Geld im Umlauf | **M1** = Giralgeld")




# --- LINKE SPALTE: LOG & STEUERUNG ---
with col_control:
    st.markdown("### 📟 System-Log")
    log_box = st.container(height=150, border=True)
    with log_box:
        for msg in st.session_state.logs[::-1]:
            st.markdown(f"<p style='font-size: 10px; margin: 0;'>{msg}</p>", unsafe_allow_html=True)

    st.markdown("### 💰 Eingabe")
    betrag = st.number_input("Betrag für Aktionen", value=0, step=100, key="main_betrag")

    st.markdown("### 🕹️ Steuerung")
    control_box = st.container(height=400, border=True)
    with control_box:
        speed = st.slider("Dauer Animation (sek)", 0.0, 4.0, 2.0, key="intro_speed")
        zins_val = st.slider("Zinssatz (%)", 0.0, 0.20, 0.0, step=0.01)
        st.write("**Kreditschöpfung**")
        c1, c2, c3 = st.columns(3)
        num_steps = 4 if betrag > 0 else 6
        with c1:
            if st.button("Kredit für Karl", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": prozess_kredit_intro,
                     "args": (betrag, zins_val, "Karl", "London Bank (LB)", speed, i)}
                    for i in range(0, num_steps)
                ]
                st.rerun()

        with c2:
            if st.button("Kredit für Friedrich", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": prozess_kredit_intro,
                     "args": (betrag, zins_val, "Friedrich", "London Bank (LB)", speed, i)}
                    for i in range(0, num_steps)
                ]
                st.rerun()

        with c3:
            # Adam Smith bei der Edinburgh Bank
            if st.button("Kredit für Adam", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": prozess_kredit_intro,
                     "args": (betrag, zins_val, "Adam", "Edinburgh Bank (EB)", speed, i)}
                    for i in range(0, num_steps)
                ]
                st.rerun()
        st.divider()
        # --- Unter "Steuerung" im control_box Bereich ---

        st.write("**BoE-Liquidität (Refinanzierung gegen Staatsanleihen)**")
        zbc1, zbc2 = st.columns(2)

        with zbc1:
            # Button für die London Bank (LB)
            if st.button("BoE-Kredit London Bank", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": zb_kredit_prozess,
                     "args": (betrag, "London Bank (LB)", speed, i)}
                    for i in range(0, 5)  # 4 Schritte laut der neuen Funktion
                ]
                st.rerun()

        with zbc2:
            # Button für die Edinburgh Bank (EB)
            if st.button("BoE-Kredit Edinburgh Bank", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": zb_kredit_prozess,
                     "args": (betrag, "Edinburgh Bank (EB)", speed, i)}
                    for i in range(0, 5)  # 4 Schritte laut der neuen Funktion
                ]
                st.rerun()

        st.write("**Zahlungsverkehr & Bargeld**")
        # 1. Auswahl von Sender und Empfänger
        col_s, col_e = st.columns(2)

        personen = ["Karl", "Friedrich", "Adam"]
        # Mapping: Wer ist bei welcher Bank?
        bank_mapping = {
            "Karl": "London Bank (LB)",
            "Friedrich": "London Bank (LB)",
            "Adam": "Edinburgh Bank (EB)"
        }

        with col_s:
            sender = st.selectbox("Sender", personen, index=0)
        with col_e:
            # Wir filtern den Sender aus der Empfängerliste, damit man sich nicht selbst Geld schickt
            empfaenger_liste = [p for p in personen if p != sender]
            empfaenger = st.selectbox("Empfänger", empfaenger_liste, index=0)

        # 2. Den Transfer-Button auslösen
        if st.button(f"💸 Zahlung: {sender} ➔ {empfaenger}", use_container_width=True):
            bank_s = bank_mapping[sender]
            bank_e = bank_mapping[empfaenger]

            # Wir nutzen 6 Schritte (0 bis 5) für die neue interbank_transfer Funktion
            st.session_state.pending_steps = [
                {"func": interbank_transfer,
                 "args": (betrag, sender, empfaenger, bank_s, bank_e, speed, i)}
                for i in range(0, 6)
            ]
            st.rerun()

        # Zweite Zeile: Bargeld-Auszahlung (Reserven zu Bargeld)
        st.write("**Bargeld-Kasse (Abhebung)**")
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("Cash Karl", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": bargeld_intro, "args": (betrag, "Karl", "London Bank (LB)", speed, i)} for i in
                    range(5)]
                st.rerun()

        with b2:
            if st.button("Cash Friedrich", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": bargeld_intro, "args": (betrag, "Friedrich", "London Bank (LB)", speed, i)} for i in
                    range(5)]
                st.rerun()

        with b3:
            if st.button("Cash Adam", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": bargeld_intro, "args": (betrag, "Adam", "Edinburgh Bank (EB)", speed, i)} for i in
                    range(5)]
                st.rerun()

# --- MOTOR (Optimiert für Plan & Action Timing) ---
has_active_highlights = len(st.session_state.get("highlights_green", [])) > 0 or len(
    st.session_state.get("highlights_red", [])) > 0

if st.session_state.get("pending_steps") or has_active_highlights:

    # 1. LÖSCH-PHASE: Wenn Farbe leuchtet, löschen wir sie für den nächsten Schritt
    if has_active_highlights:
        # Wir lassen die Farbe für die Dauer des Sliders stehen (wurde unten pausiert)
        st.session_state.highlights_green = []
        st.session_state.highlights_red = []

        if not st.session_state.get("pending_steps"):
            st.session_state.highlights_plan = []

        time.sleep(2)  # Kurzer technischer Reset
        st.rerun()

    # 2. AKTIONS-PHASE: Nächsten Schritt ausführen
    elif st.session_state.get("pending_steps"):
        current_step_data = st.session_state.pending_steps.pop(0)
        current_step_data["func"](*current_step_data["args"])

        # JEDER Schritt (auch der gelbe Plan) bekommt die Pause vom Slider
        waited_time = st.session_state.get("intro_speed", 2.0)
        time.sleep(waited_time)

        # Rerun, damit das gerade gesetzte Highlight (Grün oder Rot) angezeigt wird
        st.rerun()
