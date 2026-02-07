import streamlit as st
import pandas as pd
import time
from Transfers import (prozess_kredit, lohnzahlung_prozess, produktion_prozess, kauf_invest_prozess, kauf_konsum_prozess
        ,dividende_prozess,kauf_eigentuemer_prozess,zentralbank_clearing, regeneration_prozess)
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
                "Bank C", "UI", "Eigentümer", "Beschäftigte"]

    st.session_state.balances = {
        "Zentralbank": {
            "Assets": {"Forderung Bank A": 0, "Forderung Bank B": 0, "Forderung Bank C": 0},
            "Liabilities": {"Reserve Bank A": 0, "Reserve Bank B": 0, "Reserve Bank C": 0, "Eigenkapital": 0}
        },
        "Bank A": {
            "Assets": {"Reserve bei ZB A": 0, "Kredite UK": 0},
            "Liabilities": {"Kredit bei ZB A": 0, "Einlage UK": 0, "Einlage Unternehmer UK": 0, "Eigenkapital A": 0}
        },
        "Bank B": {
            "Assets": {"Reserve bei ZB B": 0, "Kredite UI": 0},
            "Liabilities": {"Kredit bei ZB B": 0, "Einlage UI": 0, "Einlage Unternehmer UI": 0, "Eigenkapital B": 0}
        },
        "Bank C": {
            "Assets": {"Reserve bei ZB C": 0, "Kredite Beschäftigte": 0},
            "Liabilities": {"Kredit bei ZB C": 0, "Einlage Beschäftigte": 0, "Einlage Bankbesitzer": 0,
                            "Eigenkapital C": 0}
        },
        "UK": {
            "Assets": {"Bankguthaben bei A": 0, "Warenbestand UK": 0, "Sachvermögen UK": 0},
            "Liabilities": {"Kredit bei A": 0, "Eigenkapital UK": 0}
        },
        "UI": {
            "Assets": {"Bankguthaben bei B": 0, "Sachvermögen UI": 4000},
            "Liabilities": {"Kredit bei B": 0, "Eigenkapital UI": 4000}
        },
        "Beschäftigte": {
            "Assets": {"Bankguthaben bei C": 0, "Gebrauchsvermögen B": 0},
            "Liabilities": {"Kredit bei C": 0, "Eigenkapital Beschäftigte": 0}
        },
        "Eigentümer": {
            "Assets": {"Guthaben bei A": 1000, "Guthaben bei B": 0, "Guthaben bei C": 0,
                       "Gebrauchsvermögen E": 0},
            "Liabilities": {"Eigenk. Eigentümer UK": 1000, "Eigenk. Eigentümer UI": 0, "Eigenk. Bankenbesitzer": 0}
        },
    }

    st.session_state.value_balances = {
        "UK": {
            "Arbeitskraft": 0.0,
            "Warenbestand": 0,
            "Sachvermögen": 0.0
        },
        "UI": {
            "Arbeitskraft": 0.0,
            "Sachvermögen": 4000
        },
        "Beschäftigte": {
            "Arbeitskraft": 1500,  # Das "Potenzial", das sie verkaufen können
            "Gebrauchsvermögen B": 0
        },
        "Eigentümer": {
            "Gebrauchsvermögen A": 0,  # Das "Potenzial", das sie verkaufen können
            "Gebrauchsvermögen B": 0,
            "Gebrauchsvermögen C": 0
        }
    }
    st.session_state.BIP_history = [0]  # Startwert für den Plot
    st.session_state.round_history = [0]
    st.session_state.previous_BIP = 0
    st.session_state.previous_I = 0
    st.session_state.previous_C = 0
    st.session_state.current_I = 0
    st.session_state.current_C_roh = 0
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

        if name in st.session_state.value_balances:
            values = st.session_state.value_balances[name]
            if values:
                # Hier nutzen wir <b> für Fettung und <span> für die Trenner
                val_items = [f"<b>{k}:</b> {v}" for k, v in values.items()]
                val_text = " | ".join(val_items)
                st.markdown(f'<p class="real-werte">📦 {val_text}</p>', unsafe_allow_html=True)
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
        show_bilanz("UK")
    with row2_col2:
        show_bilanz("Bank C")
    with row2_col3:
        show_bilanz("UI")

    st.divider()

    # DRITTE ZEILE: Eigentümer | (leer) | Arbeiter
    import matplotlib.pyplot as plt

    # --- DRITTE ZEILE: Eigentümer | BIP-Plot | Arbeiter ---
    row3_col1, row3_col2, row3_col3 = st.columns(3)

    with row3_col1:
        show_bilanz("Eigentümer")

    with row3_col2:
        st.markdown("<h3 style='text-align: center;'>📈 BIP Entwicklung</h3>", unsafe_allow_html=True)

        # Sicherstellen, dass die Historie mindestens einen Startwert hat, falls noch nicht geschehen
        if "BIP_history" not in st.session_state or len(st.session_state.BIP_history) == 0:
            st.session_state.BIP_history = [0]
        if "round_history" not in st.session_state or len(st.session_state.round_history) == 0:
            st.session_state.round_history = [0]

        # 1. Erstellung der Figure
        # figsize (5, 3.5) ist ideal für das 3-Spalten-Layout
        fig, ax = plt.subplots(figsize=(5, 3.5))

        # Hintergrund des Plots an das Streamlit Design anpassen (optional)
        fig.patch.set_facecolor('#f9f9f9')
        ax.set_facecolor('#f9f9f9')

        # 2. Daten plotten
        ax.plot(
            st.session_state.round_history,
            st.session_state.BIP_history,
            marker="o",
            markersize=4,
            linestyle="-",
            color="#f59b00",  # Dein Orange-Ton
            linewidth=2,
            label="BIP"
        )

        # 3. Styling des Plots
        ax.set_xlabel("Runde", fontsize=8)
        ax.set_ylabel("Euro (€)", fontsize=8)
        ax.tick_params(axis='both', which='major', labelsize=7)

        # Gitternetz für bessere Lesbarkeit
        ax.grid(True, linestyle="--", alpha=0.5)

        # Dynamischer Titel basierend auf dem aktuellen Stand
        current_bip = st.session_state.BIP_history[-1]
        ax.set_title(f"Stand: {current_bip:,.2f} €", fontsize=10, fontweight='bold')

        # Achsen-Limits: Damit es bei Runde 0 nicht komisch aussieht
        if len(st.session_state.round_history) == 1:
            ax.set_xlim(-0.5, 1.5)
            ax.set_ylim(0, max(100, current_bip * 1.5))

        plt.tight_layout()

        # 4. In Streamlit anzeigen
        st.pyplot(fig)

        # Speicher bereinigen
        plt.close(fig)

        # Kleine Info-Box für das Delta (nur wenn wir mindestens in Runde 1 sind)
        if len(st.session_state.BIP_history) > 1:
            delta_bip = st.session_state.BIP_history[-1] - st.session_state.BIP_history[-2]
            st.caption(f"Letztes Wachstum: **{delta_bip:,.2f} €**")
        else:
            st.caption("Starte die erste Runde, um Wachstum zu generieren.")

    with row3_col3:
        show_bilanz("Beschäftigte")
## Gameplay
with col_control:
    mission = get_mission(st.session_state.current_round)

    # NUR ins Log schreiben, wenn wir es in DIESER Runde noch nicht getan haben
    if st.session_state.last_logged_round < st.session_state.current_round:
        st.session_state.logs.append(f"<b style='color: #FFA500;'>🎯 {mission['title']}</b>")
        st.session_state.logs.append(f"📝 {mission['task']}")
        # Merken, dass wir diese Runde bereits geloggt haben
        st.session_state.last_logged_round = st.session_state.current_round

# --- LINKE SPALTE: LOG & STEUERUNG ---
with col_control:
    st.markdown("<h3 style='margin-bottom: 0px;'>📟 System-Log</h3>", unsafe_allow_html=True)

    log_box = st.container(height=150, border=True)
    with log_box:
        with log_box:
            # Das [::-1] dreht die Liste um: Die neuste Nachricht (Ende der Liste) kommt zuerst
            for msg in st.session_state.logs[::-1]:
                st.markdown(f"<p style='font-size: 12px; margin: 0; line-height: 1.2;'>{msg}</p>",
                            unsafe_allow_html=True)
    st.markdown("### 💰 Eingabe")
    betrag_val = st.number_input("Betrag für Aktionen", value=0, step=500, key="main_betrag")

    st.markdown("### 🕹️ Steuerung")
    control_container = st.container(height=500, border=True)
    with control_container:
        # Eingaben
        zins_val = st.slider("Zinssatz (%)", 0.0, 0.20, 0.05, step=0.01)
        speed_val = st.slider("Speed (sek)", 0.0, 3.0, 0.5)

        st.divider()

        # Kredit-Aktionen
        st.write("**Kredit-Aktionen:**")
        b_col1, b_col2, b_col3 = st.columns(3)

        with b_col1:
            is_positive = betrag_val > 0
            already_done = "kredit_uk" in st.session_state.actions_done
            if st.button("Kredit UK", disabled=(is_positive and already_done), use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": prozess_kredit, "args": (betrag_val, zins_val, "UK", "Bank A", speed_val, 1)},
                    {"func": prozess_kredit, "args": (betrag_val, zins_val, "UK", "Bank A", speed_val, 2)}
                ]
                if is_positive: st.session_state.actions_done.append("kredit_uk")
                st.rerun()

        with b_col2:
            already_done = "kredit_ui" in st.session_state.actions_done
            if st.button("Kredit UI", disabled=(is_positive and already_done), use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": prozess_kredit, "args": (betrag_val, zins_val, "UI", "Bank B", speed_val, 1)},
                    {"func": prozess_kredit, "args": (betrag_val, zins_val, "UI", "Bank B", speed_val, 2)}
                ]
                if is_positive: st.session_state.actions_done.append("kredit_ui")
                st.rerun()

        with b_col3:
            already_done = "kredit_a" in st.session_state.actions_done
            if st.button("Angestellte", disabled=(is_positive and already_done), use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": prozess_kredit, "args": (betrag_val, zins_val, "Beschäftigte", "Bank C", speed_val, 1)},
                    {"func": prozess_kredit, "args": (betrag_val, zins_val, "Beschäftigte", "Bank C", speed_val, 2)}
                ]
                if is_positive: st.session_state.actions_done.append("kredit_a")
                st.rerun()

        st.write("**Lohnzahlungen:**")
        col_lohn1, col_lohn2 = st.columns(2)
        with col_lohn1:
            already_done = "lohn_uk" in st.session_state.actions_done
            if st.button("Lohn UK", disabled=already_done, use_container_width=True):
                # Wir prüfen VOR dem Hinzufügen zu 'actions_done', ob genug Geld da ist
                guthaben = st.session_state.balances["UK"]["Assets"]["Bankguthaben bei A"]

                if betrag_val > guthaben:
                    st.error("Nicht genug Guthaben!")
                    st.toast("Transaktion abgebrochen: UK ist pleite!", icon="🚫")
                else:
                    # Nur wenn genug Geld da ist, werden die Schritte geladen
                    # und die Aktion als "erledigt" markiert
                    st.session_state.pending_steps = [
                        {"func": lohnzahlung_prozess, "args": (betrag_val, "UK", "Bank A", speed_val, i)}
                        for i in range(1, 5)
                    ]
                    st.session_state.actions_done.append("lohn_uk")
                    st.rerun()

        with col_lohn2:
            already_done = "lohn_ui" in st.session_state.actions_done
            if st.button("Lohn UI", disabled=already_done, use_container_width=True):
                guthaben = st.session_state.balances["UI"]["Assets"]["Bankguthaben bei B"]

                if betrag_val > guthaben:
                    st.error("Nicht genug Guthaben!")
                    st.toast("Transaktion abgebrochen: UI ist pleite!", icon="🚫")
                else:
                    st.session_state.pending_steps = [
                        {"func": lohnzahlung_prozess, "args": (betrag_val, "UI", "Bank B", speed_val, i)}
                        for i in range(1, 5)
                    ]
                    st.session_state.actions_done.append("lohn_ui")
                    st.rerun()
        st.divider()
        st.write("**Produktion**")
        p_col1, p_col2 = st.columns(2)

        with p_col1:
            st.markdown("**UK (Konsum)**")
            k_sum_uk = st.number_input("Gesamtkapital (K)", 0, 50000, 2500, step=100, key="k_sum_uk")
            q_uk = st.slider("Arbeitsquote (v/K)", 0.0, 1.0, 0.2, key="q_uk")
            r_uk = st.slider("Profitrate (r)", 0.0, 1.0, 0.2, key="r_uk_p")

            v_calc_uk = round(k_sum_uk * q_uk, 2)
            c_calc_uk = round(k_sum_uk * (1 - q_uk), 2)

            # Ressourcen-Check UK
            vorrat_v_uk = st.session_state.value_balances["UK"]["Arbeitskraft"]
            vorrat_c_uk = st.session_state.value_balances["UK"]["Sachvermögen"]
            genug_ressourcen_uk = (v_calc_uk <= vorrat_v_uk and c_calc_uk <= vorrat_c_uk)

            color_uk = "gray" if genug_ressourcen_uk else "red"
            st.markdown(f"<p style='font-size: 11px; color: {color_uk}; margin-top: -10px;'>"
                        f"Bedarf: v={v_calc_uk} , c={c_calc_uk}</p>", unsafe_allow_html=True)

            done_uk = "prod_uk" in st.session_state.actions_done
            if st.button("Produzieren UK", use_container_width=True, disabled=done_uk):
                if genug_ressourcen_uk:
                    st.session_state.pending_steps = [
                        {"func": produktion_prozess, "args": ("UK", k_sum_uk, q_uk, r_uk, 1)},
                        {"func": produktion_prozess, "args": ("UK", k_sum_uk, q_uk, r_uk, 2)}
                    ]
                    st.session_state.actions_done.append("prod_uk")
                    st.rerun()
                else:
                    st.error("Ressourcen fehlen!")

        with p_col2:
            st.markdown("**UI (Investition)**")
            k_sum_ui = st.number_input("Gesamtkapital (K)", 0, 50000, 5000, step=100, key="k_sum_ui")
            q_ui = st.slider("Arbeitsquote (v/K)", 0.0, 1.0, 0.2, key="q_ui")
            r_ui = st.slider("Profitrate (r)", 0.0, 1.0, 0.2, key="r_ui_p")

            v_calc_ui = round(k_sum_ui * q_ui, 2)
            c_calc_ui = round(k_sum_ui * (1 - q_ui), 2)

            # Ressourcen-Check UI
            vorrat_v_ui = st.session_state.value_balances["UI"]["Arbeitskraft"]
            vorrat_c_ui = st.session_state.value_balances["UI"]["Sachvermögen"]
            genug_ressourcen_ui = (v_calc_ui <= vorrat_v_ui and c_calc_ui <= vorrat_c_ui)

            color_ui = "gray" if genug_ressourcen_ui else "red"
            st.markdown(f"<p style='font-size: 11px; color: {color_ui}; margin-top: -10px;'>"
                        f"Bedarf: v={v_calc_ui} , c={c_calc_ui}</p>", unsafe_allow_html=True)

            done_ui = "prod_ui" in st.session_state.actions_done
            if st.button("Produzieren UI", use_container_width=True, disabled=done_ui):
                if genug_ressourcen_ui:
                    st.session_state.pending_steps = [
                        {"func": produktion_prozess, "args": ("UI", k_sum_ui, q_ui, r_ui, 1)},
                        {"func": produktion_prozess, "args": ("UI", k_sum_ui, q_ui, r_ui, 2)}
                    ]
                    st.session_state.actions_done.append("prod_ui")
                    st.rerun()
                else:
                    st.error("Ressourcen fehlen!")

        st.write("**🛒 Markttransaktionen**")
        m_col1, m_col2 = st.columns(2)

        with m_col1:
            if st.button("Kauf Invest-Güter (UK)", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": kauf_invest_prozess, "args": (betrag_val, i)} for i in range(1, 5)
                ]
                st.rerun()

        with m_col2:
            if st.button("Kauf Lebensmittel", use_container_width=True):
                st.session_state.pending_steps = [
                    {"func": kauf_konsum_prozess, "args": (betrag_val, i,r_uk, q_uk)} for i in range(1, 5)
                ]
                st.rerun()
        st.divider()
        st.write("**💎 Eigentümer & Dividenden**")


        st.caption("🏢Dividenden Unternehmen")
        u_row1, u_row2 = st.columns(2)

        with u_row1:
            # Check für UK
            done_div_uk = "div_uk" in st.session_state.actions_done
            if st.button("Dividende UK", use_container_width=True, disabled=done_div_uk):
                st.session_state.pending_steps = [{"func": dividende_prozess, "args": ("UK", betrag_val, i)} for i
                                                  in [1, 2]]
                st.session_state.actions_done.append("div_uk")
                st.rerun()

        with u_row2:
            # Check für UI
            done_div_ui = "div_ui" in st.session_state.actions_done
            if st.button("Dividende UI", use_container_width=True, disabled=done_div_ui):
                st.session_state.pending_steps = [{"func": dividende_prozess, "args": ("UI", betrag_val, i)} for i
                                                  in [1, 2]]
                st.session_state.actions_done.append("div_ui")
                st.rerun()

        st.caption("🏛️Dividenden Banken")
        b_row1, b_row2, b_row3 = st.columns(3)

        with b_row1:
            # Check für Bank A
            done_div_ba = "div_ba" in st.session_state.actions_done
            if st.button("Bank A", use_container_width=True, disabled=done_div_ba):
                # Jetzt 2 Schritte für den Transfer zu Bank C
                st.session_state.pending_steps = [{"func": dividende_prozess, "args": ("Bank A", betrag_val, i)} for i
                                                  in [1, 2]]
                st.session_state.actions_done.append("div_ba")
                st.rerun()

        with b_row2:
            # Check für Bank B
            done_div_bb = "div_bb" in st.session_state.actions_done
            if st.button("Bank B", use_container_width=True, disabled=done_div_bb):
                # Jetzt 2 Schritte für den Transfer zu Bank C
                st.session_state.pending_steps = [{"func": dividende_prozess, "args": ("Bank B", betrag_val, i)} for i
                                                  in [1, 2]]
                st.session_state.actions_done.append("div_bb")
                st.rerun()

        with b_row3:
            # Check für Bank C
            done_div_bc = "div_bc" in st.session_state.actions_done
            if st.button("Bank C", use_container_width=True, disabled=done_div_bc):
                # Jetzt 2 Schritte für den Transfer zu Bank C
                st.session_state.pending_steps = [{"func": dividende_prozess, "args": ("Bank C", betrag_val, i)} for i
                                                  in [1, 2]]
                st.session_state.actions_done.append("div_bc")
                st.rerun()

        st.caption("🛒 Eigentümer-Konsum (Lebensmittel)")

        k_row1, k_row2, k_row3 = st.columns(3)

        with k_row1:
            if st.button("Konto A", key="buy_a", use_container_width=True):
                # Auch bei Bank A nutzen wir i in range(1, 5), die Funktion überspringt
                # dort einfach die ZB-Schritte logisch
                st.session_state.pending_steps = [{"func": kauf_eigentuemer_prozess, "args": (betrag_val, "A",i, r_uk, q_uk)} for i
                                                  in range(1, 5)]
                st.rerun()

        with k_row2:
            if st.button("Konto B", key="buy_b", use_container_width=True):
                st.session_state.pending_steps = [{"func": kauf_eigentuemer_prozess, "args": (betrag_val, "B",i, r_uk, q_uk)} for i
                                                  in range(1, 5)]
                st.rerun()

        with k_row3:
            if st.button("Konto C", key="buy_c", use_container_width=True):
                st.session_state.pending_steps = [{"func": kauf_eigentuemer_prozess, "args": (betrag_val, "C",i, r_uk, q_uk)} for i
                                                  in range(1, 5)]
                st.rerun()
        st.divider()
        st.write("**Perioden-Abschluss**")
        c_col1, c_col2 = st.columns(2)

        with c_col1:
            if st.button("🏦 ZB-Clearing", use_container_width=True):
                zentralbank_clearing()
                st.rerun()

        with c_col2:
            if st.button("🍕 Regenerieren", use_container_width=True):
                regeneration_prozess()
                st.rerun()

        # --- In der col_control oder wo deine Steuerung sitzt ---

        curr_r = st.session_state.current_round
        if st.button("🏁 Runde Abschließen", type="primary", key=f"finish_{curr_r}", use_container_width=True):
            # Summe der tatsächlichen Käufe dieser Runde
            current_BIP = st.session_state.current_I + st.session_state.current_C_roh

            # Historie & Reset
            st.session_state.BIP_history.append(current_BIP)
            st.session_state.round_history.append(curr_r)
            st.session_state.current_I = 0
            st.session_state.current_C_roh = 0

            st.session_state.current_round += 1
            st.session_state.actions_done = []
            st.rerun()



# --- HIER GANZ UNTEN KOMMT DER MOTOR REIN (siehe oben) ---
t = 1
if st.session_state.get("pending_steps"):
    # 1. Reset-Blitz (Highlights löschen)
    if st.session_state.get("highlights"):
        st.session_state.highlights = []
        time.sleep(t) # Nur ganz kurz!
        st.rerun()

    # 2. Aktion ausführen
    else:
        current_action = st.session_state.pending_steps.pop(0)
        # Wichtig: Wir fangen den Rückgabewert ab
        success = current_action["func"](*current_action["args"])

        # Pause, damit der User das Ergebnis (Gelb) sehen kann
        time.sleep(st.session_state.get("intro_speed", 0.5))
        st.rerun()