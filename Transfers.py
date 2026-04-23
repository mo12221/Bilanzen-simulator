import streamlit as st
import time




def prozess_kredit(betrag, interest_rate, firma, bank, speed, schritt):
    # Dynamische Kürzel extrahieren
    bank_buchstabe = bank.split()[-1]  # "A", "B" oder "C"

    # Kontonamen definieren
    asset_firma = f"Bankguthaben bei {bank_buchstabe}"
    liab_firma = f"Kredit bei {bank_buchstabe}"
    asset_bank = f"Kredite {firma}"
    liab_bank = f"Einlage {firma}"

    # Eigenkapital-Konto der Bank (z.B. "Eigenkapital A")
    ek_bank = f"Eigenkapital {bank_buchstabe}"

    # Flexibler Check für das Eigenkapital-Konto der Firma (UK, UI oder Arbeiter)
    # Sucht nach "Eigenkapital UK", "Eigenkapital UI" oder "Eigenkapital"
    ek_firma_options = [f"Eigenkapital {firma}", "Eigenkapital"]
    ek_firma = next((opt for opt in ek_firma_options if opt in st.session_state.balances[firma]["Liabilities"]), None)

    try:
        # --- FALL A: KREDITAUFNAHME (GELDSCHÖPFUNG) ---
        if betrag > 0:
            if schritt == 0:
                st.session_state.highlights_plan = [asset_firma,liab_bank,asset_bank,liab_firma]
            if schritt == 1:
                # Schritt 1: Firma kriegt Guthaben, Bank kriegt Verbindlichkeit (Einlage)
                st.session_state.balances[firma]["Assets"][asset_firma] += betrag
                st.session_state.balances[bank]["Liabilities"][liab_bank] += betrag

                st.session_state.highlights_green = [asset_firma, liab_bank]
                st.session_state.logs.append(f"🏦 {bank}: Schöpft Giralgeld für {firma}.")

            elif schritt == 2:
                # Schritt 2: Bank kriegt Forderung (Kredit), Firma kriegt Verbindlichkeit
                st.session_state.balances[bank]["Assets"][asset_bank] += betrag
                st.session_state.balances[firma]["Liabilities"][liab_firma] += betrag

                st.session_state.highlights_green = [asset_bank, liab_firma]
            elif schritt == 3:
                st.session_state.highlights_plan = []
                st.session_state.logs.append(f"📝 {firma}: Kreditvertrag über {betrag}€ aktiviert.")

        # --- FALL B: TILGUNG & ZINSEN ---
        elif betrag < 0:
            kredit_anteil = abs(betrag)
            zins_anteil = round(kredit_anteil * interest_rate, 2)
            gesamt_abfluss = kredit_anteil + zins_anteil
            if schritt == 0:
                st.session_state.highlights_plan = [asset_firma,liab_firma,ek_firma,asset_bank,liab_bank,ek_bank]
            if schritt == 1:
                # Firma zahlt: Guthaben sinkt um Gesamt, Kredit sinkt um Tilgung, EK sinkt um Zins
                st.session_state.balances[firma]["Assets"][asset_firma] -= gesamt_abfluss
                st.session_state.balances[firma]["Liabilities"][liab_firma] -= kredit_anteil
                st.session_state.balances[firma]["Liabilities"][ek_firma] -= zins_anteil
                st.session_state.highlights_red = [asset_firma, liab_firma, ek_firma]
                st.session_state.logs.append(f"📉 {firma}: Tilgung {kredit_anteil}€ + Zins {zins_anteil}€.")

            elif schritt == 2:
                # Bank erhält: Kredit-Forderung sinkt, Einlagen-Verbindlichkeit sinkt, EK (Gewinn) steigt
                st.session_state.balances[bank]["Assets"][asset_bank] -= kredit_anteil
                st.session_state.balances[bank]["Liabilities"][liab_bank] -= gesamt_abfluss
                if ek_bank in st.session_state.balances[bank]["Liabilities"]:
                    st.session_state.balances[bank]["Liabilities"][ek_bank] += zins_anteil

                st.session_state.highlights_green = [asset_bank, liab_bank, ek_bank]
                st.session_state.logs.append(f"🏛️ {bank}: Zinsertrag verbucht.")

        return True

    except KeyError as e:
        st.error(f"Fehler in prozess_kredit: Konto {e} nicht gefunden!")
        st.session_state.pending_steps = []
        return False

### Transfer Lohn

def lohnzahlung_prozess(betrag, firma, bank_firma, speed, schritt):
    bank_buchstabe = bank_firma.split()[-1]

    try:
        # --- SCHRITT 1: ZB-Refinanzierung ---
        if schritt == 0:
            guthaben = st.session_state.balances[firma]["Assets"][f"Bankguthaben bei {bank_buchstabe}"]
            if betrag > guthaben:
                st.session_state.logs.append(f"⚠️ Nicht genügend Guthaben bei {firma}!")
                st.session_state.pending_steps = []
                return False
        elif schritt == 1:
            st.session_state.highlights_plan = [f"Forderung {bank_firma}",f"Reserve {bank_firma}",f"Reserve bei ZB {bank_buchstabe}",
            f"Kredit bei ZB {bank_buchstabe}",f"Einlage {firma}",f"Bankguthaben bei {bank_buchstabe}", f"Eigenkapital {firma}"
                , f"Reserve Bank C",f"Reserve bei ZB {bank_buchstabe}",f"Reserve {bank_firma}",
            "Bankguthaben bei C", "Einlage Beschäftigte", "Eigenkapital Beschäftigte"
            ,"Reserve bei ZB C", "Arbeitskraft"]

        elif schritt == 2:
            st.session_state.balances["Zentralbank"]["Assets"][f"Forderung {bank_firma}"] += betrag
            st.session_state.balances["Zentralbank"]["Liabilities"][f"Reserve {bank_firma}"] += betrag
            st.session_state.balances[bank_firma]["Assets"][f"Reserve bei ZB {bank_buchstabe}"] += betrag
            st.session_state.balances[bank_firma]["Liabilities"][f"Kredit bei ZB {bank_buchstabe}"] += betrag

            # Highlights für ZB-Refinanzierung
            st.session_state.highlights_green = [f"Reserve bei ZB {bank_buchstabe}", f"Kredit bei ZB {bank_buchstabe}", f"Forderung {bank_firma}", f"Reserve {bank_firma}"]
            st.session_state.logs.append(f"🏛️ ZB stellt {bank_firma} Reserven für die Lohnzahlung bereit.")

        # --- SCHRITT 2: Abbuchung & ZB-Umschichtung ---
        elif schritt == 3:
            st.session_state.balances[firma]["Assets"][f"Bankguthaben bei {bank_buchstabe}"] -= betrag
            st.session_state.balances[bank_firma]["Liabilities"][f"Einlage {firma}"] -= betrag
            st.session_state.highlights_red = [f"Einlage {firma}",f"Bankguthaben bei {bank_buchstabe}"]

        elif schritt == 4:
            st.session_state.balances[bank_firma]["Assets"][f"Reserve bei ZB {bank_buchstabe}"] -= betrag
            st.session_state.balances["Zentralbank"]["Liabilities"][f"Reserve {bank_firma}"] -= betrag
            st.session_state.highlights_red = [f"Reserve bei ZB {bank_buchstabe}",f"Reserve {bank_firma}"]

        elif schritt == 5:
            st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank C"] += betrag
            st.session_state.balances["Bank C"]["Assets"]["Reserve bei ZB C"] += betrag
            # Highlights für den Abfluss bei Bank A/B
            st.session_state.highlights_green = [f"Reserve Bank C","Reserve bei ZB C"]
            st.session_state.logs.append(f"🏦 {bank_firma} bucht Lohn ab und ZB schiebt Reserven zu Bank C.")

        # --- SCHRITT 3: Gutschrift bei Beschäftigte (Bank C) ---
        elif schritt == 6:
            st.session_state.balances["Bank C"]["Liabilities"]["Einlage Beschäftigte"] += betrag
            st.session_state.balances["Beschäftigte"]["Assets"]["Bankguthaben bei C"] += betrag

            # Highlights bei den Empfängern
            st.session_state.highlights_green = ["Bankguthaben bei C", "Einlage Beschäftigte"]
            st.session_state.logs.append(f"👷 Bank C schreibt den Lohn den Beschäftigte gut.")

        # --- SCHRITT 4: Realwirtschaft (Arbeitskraft-Transfer) ---
        elif schritt == 7:
            # Überprüfe, ob die Beträge ankommen
            st.session_state.balances["Beschäftigte"]["Liabilities"]["Eigenkapital Beschäftigte"] += betrag
            st.session_state.balances[firma]["Liabilities"][f"Eigenkapital {firma}"] -= betrag

            st.session_state.value_balances["Beschäftigte"]["Arbeitskraft"] -= betrag
            st.session_state.value_balances[firma]["Arbeitskraft"] += betrag

            st.session_state.highlights_red = [f"Eigenkapital {firma}"]
            st.session_state.highlights_green = [f"Eigenkapital Beschäftigte"]

            # WICHTIG: Setze die Highlights auf "Arbeitskraft",
            st.session_state.logs.append(f"✅ Arbeitskraft wurde physisch an {firma} übertragen.")
        return True

    except KeyError as e:
        st.error(f"Fehler: Konto {e} nicht gefunden!")
        st.session_state.pending_steps = []
        return False


def produktion_prozess(typ, k_gesamt, v_quote, profit_rate, schritt):
    """
    typ: "UK" oder "UI"
    k_gesamt: Das gesamte investierte Kapital (c + v)
    v_quote: Anteil des variablen Kapitals am Gesamtkapital (v / (v+c))
    profit_rate: r
    """
    # Herleitung von v und c aus der Quote
    v_kapital = round(k_gesamt * v_quote, 2)
    c_kapital = round(k_gesamt * (1 - v_quote), 2)
    ek_key = f"Eigenkapital {typ}"
    try:
        if schritt == 0:
            st.session_state.highlights_plan = [ek_key,"Arbeitskraft", f"Sachvermögen {typ}"]
        if schritt == 1:
            vorrat_v = st.session_state.value_balances[typ]["Arbeitskraft"]
            vorrat_k = st.session_state.value_balances[typ]["Sachvermögen"]

            if v_kapital > vorrat_v or c_kapital > vorrat_k:
                st.session_state.logs.append(
                    f"⚠️ {typ}: Ressourcen fehlen! (v:{v_kapital}/{vorrat_v}, c:{c_kapital}/{vorrat_k})")
                st.session_state.pending_steps = []
                return False

            # VERBRAUCH
            st.session_state.value_balances[typ]["Arbeitskraft"] -= v_kapital
            st.session_state.value_balances[typ]["Sachvermögen"] -= c_kapital
            st.session_state.balances[typ]["Assets"][f"Sachvermögen {typ}"] -= c_kapital
            st.session_state.balances[typ]["Liabilities"][f"Eigenkapital {typ}"] -= c_kapital

            st.session_state.highlights_red = [f"Eigenkapital {typ}", f"Sachvermögen {typ}"]
            st.session_state.logs.append(f"⚙️ {typ}: Produktion mit Quote {int(v_quote * 100)}% Arbeit startet.")

        elif schritt == 2:
            # ERZEUGNIS
            # Warenwert = K_gesamt * (1 + r)
            produkt_wert = round(k_gesamt * (1 + profit_rate), 2)
            mehrwert = produkt_wert - c_kapital  # Das ist v + Profit

            if typ == "UK":
                target = "Warenbestand UK"
                st.session_state.value_balances[typ]["Warenbestand"] += produkt_wert
            else:
                target = "Sachvermögen UI"
                st.session_state.value_balances[typ]["Sachvermögen"] += produkt_wert

            st.session_state.balances[typ]["Assets"][target] += produkt_wert
            st.session_state.balances[typ]["Liabilities"][ek_key] += produkt_wert

            st.session_state.highlights_green = [target, ek_key]
            st.session_state.logs.append(f"📦 {typ}: Output +{produkt_wert}€ (v: {v_kapital}, c: {c_kapital})")

        return True
    except Exception as e:
        st.error(f"Fehler: {e}")
        st.session_state.pending_steps = []
        return False


def kauf_invest_prozess(betrag, schritt):
    # IDs vorbereiten
    # Käufer: UK (Bank A), Verkäufer: UI (Bank B)
    try:
        if schritt == 0:
            # Validierung
            guthaben_uk = st.session_state.balances["UK"]["Assets"]["Bankguthaben bei A"]
            vorrat_ui = st.session_state.value_balances["UI"]["Sachvermögen"]

            if betrag > guthaben_uk:
                st.session_state.logs.append("⚠️ UK hat nicht genug Geld für Investitionen!")
                st.session_state.pending_steps = []
                return False
            if betrag > vorrat_ui:
                st.session_state.logs.append("⚠️ UI hat nicht genug Investitionsgüter auf Lager!")
                st.session_state.pending_steps = []
                return False
        elif schritt == 1:
            st.session_state.highlights_plan = ["Reserve bei ZB A", "Forderung Bank A", "Kredit bei ZB A",
                                                "Reserve Bank A",
                                                "Bankguthaben bei A", "Einlage UK", "Reserve Bank B",
                                                "Bankguthaben bei B", "Einlage UI", "Reserve bei ZB B",
                                                "Sachvermögen UI", "Sachvermögen UK"]
        elif schritt ==2:
            # Schritt 1: Refinanzierung Bank A (Käuferbank braucht Reserven)
            st.session_state.balances["Zentralbank"]["Assets"]["Forderung Bank A"] += betrag
            st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank A"] += betrag
            st.session_state.balances["Bank A"]["Assets"]["Reserve bei ZB A"] += betrag
            st.session_state.balances["Bank A"]["Liabilities"]["Kredit bei ZB A"] += betrag

            st.session_state.highlights_green = ["Reserve bei ZB A", "Forderung Bank A", "Kredit bei ZB A", "Reserve Bank A"]
            st.session_state.logs.append("🏛️ ZB stellt Bank A Reserven für den Kauf bereit.")

        elif schritt == 3:
            # Schritt 2: Abbuchung UK & ZB-Umschichtung zu Bank B
            st.session_state.balances["UK"]["Assets"]["Bankguthaben bei A"] -= betrag
            st.session_state.balances["Bank A"]["Liabilities"]["Einlage UK"] -= betrag
            st.session_state.highlights_red = ["Bankguthaben bei A", "Einlage UK"]
            st.session_state.logs.append("🏦 Bank A bucht ab, ZB leitet Reserven an Bank B weiter.")

        elif schritt == 4:
            st.session_state.balances["Bank A"]["Assets"]["Reserve bei ZB A"] -= betrag
            st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank A"] -= betrag
            st.session_state.highlights_red = ["Reserve bei ZB A","Reserve Bank A"]

        elif schritt == 5:
            st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank B"] += betrag
            st.session_state.balances["Bank B"]["Assets"]["Reserve bei ZB B"] += betrag
            st.session_state.highlights_green = ["Reserve Bank B","Reserve bei ZB B"]

        elif schritt == 6:
            # Schritt 3: Gutschrift bei UI (Bank B)
            st.session_state.balances["Bank B"]["Liabilities"]["Einlage UI"] += betrag
            st.session_state.balances["UI"]["Assets"]["Bankguthaben bei B"] += betrag
            st.session_state.highlights_green = ["Bankguthaben bei B", "Einlage UI"]
            st.session_state.logs.append("✅ UI hat die Zahlung erhalten.")

        elif schritt == 7:
            # Schritt 4: Realwirtschaftlicher Transfer
            # UI verliert Sachvermögen (Verkauf), UK gewinnt Sachvermögen (Investition)
            st.session_state.value_balances["UI"]["Sachvermögen"] -= betrag
            st.session_state.balances["UI"]["Assets"]["Sachvermögen UI"] -= betrag

            st.session_state.value_balances["UK"]["Sachvermögen"] += betrag
            st.session_state.balances["UK"]["Assets"]["Sachvermögen UK"] += betrag
            st.session_state.current_I += betrag
            # BIP Update (optional, falls du eine Variable dafür hast)
            if "BIP_aktuell" in st.session_state:
                st.session_state.BIP_aktuell += betrag

            st.session_state.highlights_green = ["Sachvermögen UK"]
            st.session_state.highlights_red = ["Sachvermögen UI"]

            st.session_state.logs.append(f"📦 Investitionsgüter ({betrag}€) von UI an UK übertragen.")

        return True
    except Exception as e:
        st.error(f"Fehler beim Kauf: {e}")
        st.session_state.pending_steps = []
        return False


def kauf_konsum_prozess(betrag, schritt,r,vk):
    try:
        if schritt == 0:
            # Validierung: Beschäftigte zu UK
            guthaben = st.session_state.balances["Beschäftigte"]["Assets"]["Bankguthaben bei C"]
            waren = st.session_state.value_balances["UK"]["Warenbestand"]

            if betrag > guthaben:
                st.session_state.logs.append("⚠️ Beschäftigte haben nicht genug Geld!")
                st.session_state.pending_steps = []
                return False
            if betrag > waren:
                st.session_state.logs.append("⚠️ UK hat nicht genug Lebensmittel auf Lager!")
                st.session_state.pending_steps = []
                return False
        elif schritt == 1:
            st.session_state.highlights_plan = ["Reserve bei ZB C", "Reserve Bank C","Kredit bei ZB C","Forderung Bank C",
                                                "Bankguthaben bei C", "Reserve Bank A", "Reserve Bank C",
                                                 "Einlage Beschäftigte", "Reserve bei ZB C",
                                                "Bankguthaben bei A", "Einlage UK","Reserve bei ZB A",
                                                "Warenbestand UK", "Gebrauchsvermögen B"]
        elif schritt == 2:
            # Interbanken-Refinanzierung (Bank C braucht Reserven)
            st.session_state.balances["Zentralbank"]["Assets"]["Forderung Bank C"] += betrag
            st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank C"] += betrag
            st.session_state.balances["Bank C"]["Assets"]["Reserve bei ZB C"] += betrag
            st.session_state.balances["Bank C"]["Liabilities"]["Kredit bei ZB C"] += betrag

            st.session_state.highlights_green = ["Reserve bei ZB C", "Reserve Bank C","Kredit bei ZB C","Forderung Bank C"]
            st.session_state.logs.append("🏛️ Bank C besorgt sich Reserven für den Transfer.")

        elif schritt == 3:
            # Abbuchung Beschäftigte & ZB-Transfer zu Bank A
            st.session_state.balances["Beschäftigte"]["Assets"]["Bankguthaben bei C"] -= betrag
            st.session_state.balances["Bank C"]["Liabilities"]["Einlage Beschäftigte"] -= betrag
            st.session_state.highlights_red = ["Bankguthaben bei C","Einlage Beschäftigte"]

        elif schritt == 4:
            st.session_state.balances["Bank C"]["Assets"]["Reserve bei ZB C"] -= betrag
            st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank C"] -= betrag
            st.session_state.highlights_red = ["Reserve bei ZB C","Reserve Bank C"]

        elif schritt == 5:
            st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank A"] += betrag
            st.session_state.balances["Bank A"]["Assets"]["Reserve bei ZB A"] += betrag
            st.session_state.highlights_green = ["Reserve Bank A","Reserve bei ZB A"]
        elif schritt == 6:
            # Gutschrift bei UK
            st.session_state.balances["Bank A"]["Liabilities"]["Einlage UK"] += betrag
            st.session_state.balances["UK"]["Assets"]["Bankguthaben bei A"] += betrag

            st.session_state.highlights_green = ["Bankguthaben bei A", "Einlage UK"]
            st.session_state.logs.append("💰 UK verbucht Verkaufserlös.")

        elif schritt == 7:
            # Warenübergabe
            st.session_state.value_balances["UK"]["Warenbestand"] -= betrag
            st.session_state.balances["UK"]["Assets"]["Warenbestand UK"] -= betrag
            st.session_state.balances["Beschäftigte"]["Assets"]["Gebrauchsvermögen B"] += betrag
            st.session_state.value_balances["Beschäftigte"]["Gebrauchsvermögen B"] += betrag

            st.session_state.highlights_green = ["Gebrauchsvermögen B"]
            st.session_state.highlights_red = ["Warenbestand UK"]

            st.session_state.logs.append("🍎 Lebensmittel an Beschäftigte geliefert.")
            st.session_state.current_C_roh += betrag
            C_bereinigt = betrag * (1 - (1 / (1 + r)) * (1 - vk))
            st.session_state.current_C_roh += C_bereinigt
        return True
    except Exception as e:
        st.error(f"Fehler beim Konsum: {e}")
        st.session_state.pending_steps = []
        return False


def dividende_prozess(typ, betrag, schritt):
    """
    typ: "UK", "UI", "Bank A", "Bank B" oder "Bank C"
    Logik: Bank A/B schütten an Bank C aus. Bank C schüttet intern aus.
    """
    try:
        # --- FALL 1: UNTERNEHMEN---
        if typ in ["UK", "UI"]:
            bank_id = "A" if typ == "UK" else "B"
            bank_name = f"Bank {bank_id}"
            if schritt == 0:
                if st.session_state.balances[typ]["Assets"][f"Bankguthaben bei {bank_id}"] < betrag:
                    st.session_state.logs.append(f"⚠️ {typ} hat nicht genug Guthaben!")
                    st.session_state.pending_steps = []
                    return False
            elif schritt == 1:
                st.session_state.highlights_plan = [f"Bankguthaben bei {bank_id}", f"Eigenkapital {typ}"
                    , f"Guthaben bei {bank_id}", f"Einlage Unternehmer {typ}", f"Einlage {typ}"
                    , f"Eigenk. Eigentümer {typ}"]
            elif schritt == 2:
                st.session_state.balances[typ]["Assets"][f"Bankguthaben bei {bank_id}"] -= betrag
                st.session_state.balances[typ]["Liabilities"][f"Eigenkapital {typ}"] -= betrag
                st.session_state.highlights_red = [f"Bankguthaben bei {bank_id}", f"Eigenkapital {typ}"]
            elif schritt == 3:
                st.session_state.balances[bank_name]["Liabilities"][f"Einlage {typ}"] -= betrag
                st.session_state.balances[bank_name]["Liabilities"][f"Einlage Unternehmer {typ}"] += betrag
                st.session_state.balances["Eigentümer"]["Assets"][f"Guthaben bei {bank_id}"] += betrag
                st.session_state.balances["Eigentümer"]["Liabilities"][f"Eigenk. Eigentümer {typ}"] += betrag
                st.session_state.highlights_green = [f"Guthaben bei {bank_id}",f"Einlage Unternehmer {typ}",f"Eigenk. Eigentümer {typ}"]
                st.session_state.highlights_red = [f"Einlage {typ}"]

        # --- FALL 2: BANKEN A & B (Überweisung an Bank C) ---
        elif typ in ["Bank A", "Bank B"]:
            bank_id = typ.split()[-1]  # "A" oder "B"
            ek_name = f"Eigenkapital {bank_id}"
            if schritt == 0:
                if st.session_state.balances[typ]["Liabilities"][ek_name] < betrag:
                    st.session_state.logs.append(f"⚠️ {typ} hat zu wenig EK!")
                    st.session_state.pending_steps = []
                    return False
            elif schritt == 1:
                st.session_state.highlights_plan = []
            elif schritt == 2:
                # Bank A/B mindert EK und besorgt sich ZB-Reserven für den Transfer zu Bank C
                st.session_state.balances["Zentralbank"]["Assets"][f"Forderung {typ}"] += betrag
                st.session_state.balances["Zentralbank"]["Liabilities"][f"Reserve {typ}"] += betrag
                st.session_state.balances[typ]["Assets"][f"Reserve bei ZB {bank_id}"] += betrag
                st.session_state.balances[typ]["Liabilities"][f"Kredit bei ZB {bank_id}"] += betrag

                st.session_state.highlights_green = [f"Reserve bei ZB {bank_id}",f"Forderung {typ}",f"Reserve bei ZB {bank_id}",f"Kredit bei ZB {bank_id}"]
                st.session_state.logs.append(f"🏛️ {typ} besorgt Reserven.")

            elif schritt == 3:
                # Transfer der Reserven von Bank A/B zu Bank C bei der ZB
                st.session_state.balances[typ]["Assets"][f"Reserve bei ZB {bank_id}"] -= betrag
                st.session_state.balances["Zentralbank"]["Liabilities"][f"Reserve {typ}"] -= betrag
                st.session_state.highlights_red = [f"Reserve {typ}",f"Reserve bei ZB {bank_id}"]

            elif schritt == 4:
                st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank C"] += betrag
                st.session_state.balances["Bank C"]["Assets"]["Reserve bei ZB C"] += betrag
                st.session_state.highlights_green = [f"Reserve C", f"Reserve bei ZB C"]
            elif schritt == 5:
                st.session_state.balances["Bank C"]["Liabilities"]["Einlage Bankbesitzer"] += betrag
                st.session_state.balances["Eigentümer"]["Assets"]["Guthaben bei C"] += betrag
                st.session_state.highlights_green = ["Guthaben bei C","Einlage Bankbesitzer"]
            elif schritt == 6:
                st.session_state.balances[typ]["Liabilities"][ek_name] -= betrag
                st.session_state.balances["Eigentümer"]["Liabilities"]["Eigenk. Bankenbesitzer"] += betrag
                st.session_state.highlights_green = ["Eigenk. Bankenbesitzer"]
                st.session_state.highlights_red = [ek_name]

                st.session_state.logs.append(f"💸 Dividende von {typ} floss über die ZB an den Besitzer bei Bank C.")

        # --- FALL 3: BANK C (Interne Ausschüttung) ---
        elif typ == "Bank C":
            if schritt == 0:
                if st.session_state.balances["Bank C"]["Liabilities"]["Eigenkapital C"] < betrag:
                    st.session_state.logs.append("⚠️ Bank C hat zu wenig EK!")
                    st.session_state.pending_steps = []
                    return False
            elif schritt == 1:
                st.session_state.highlights_plan = ["Eigenkapital C","Einlage Bankbesitzer", "Guthaben bei C","Eigenk. Bankenbesitzer"]
            elif schritt == 2:
                # Interner Passivtausch: EK C -> Einlage Bankbesitzer
                st.session_state.balances["Bank C"]["Liabilities"]["Eigenkapital C"] -= betrag
                st.session_state.highlights_red = ["Eigenkapital C"]

            elif schritt ==3:
                st.session_state.balances["Bank C"]["Liabilities"]["Einlage Bankbesitzer"] += betrag
                st.session_state.balances["Eigentümer"]["Assets"]["Guthaben bei C"] += betrag
                st.session_state.highlights_green = ["Einlage Bankbesitzer", "Guthaben bei C"]

            elif schritt ==4:
                st.session_state.balances["Eigentümer"]["Liabilities"]["Eigenk. Bankenbesitzer"] += betrag

                st.session_state.highlights_green = ["Eigenk. Bankenbesitzer"]
                st.session_state.logs.append("🏛️ Bank C hat intern Dividende an den Besitzer ausgeschüttet.")

        return True
    except Exception as e:
        st.error(f"Fehler: {e}")
        st.session_state.pending_steps = []
        return False


def kauf_eigentuemer_prozess(betrag, von_bank_id, schritt,r,vk):
    try:
        bank_name_von = f"Bank {von_bank_id}"

        if von_bank_id == "A":
            einlage_key_bank = "Einlage Unternehmer UK"
        elif von_bank_id == "B":
            einlage_key_bank = "Einlage Unternehmer UI"
        else:  # Bank C
            einlage_key_bank = "Einlage Bankbesitzer"
        if schritt == 0:
            guthaben = st.session_state.balances["Eigentümer"]["Assets"][f"Guthaben bei {von_bank_id}"]
            waren = st.session_state.value_balances["UK"]["Warenbestand"]

            if betrag > guthaben:
                st.session_state.logs.append(f"⚠️ Eigentümer hat zu wenig Guthaben bei Bank {von_bank_id}!")
                st.session_state.pending_steps = []
                return False
            if betrag > waren:
                st.session_state.logs.append("⚠️ UK hat nicht genug Lebensmittel auf Lager!")
                st.session_state.pending_steps = []
                return False
        if schritt == 1:
            if von_bank_id != "A":
                st.session_state.highlights_plan = [f"Reserve bei ZB {von_bank_id}", f"Forderung {bank_name_von}"
                    ,f"Reserve {bank_name_von}",f"Kredit bei ZB {von_bank_id}",f"Guthaben bei {von_bank_id}",einlage_key_bank,
                                                    f"Reserve bei ZB {von_bank_id}",f"Reserve {bank_name_von}",
                                                    "Reserve Bank A", "Reserve bei ZB A","Einlage UK",
                                                    "Gebrauchsvermögen E","Warenbestand UK","Bankguthaben bei A"]
            else:
                st.session_state.highlights_plan = [f"Guthaben bei {von_bank_id}",einlage_key_bank,
                                                    "Einlage UK","Bankguthaben bei A","Gebrauchsvermögen E","Warenbestand UK"]
        elif schritt == 2:
            if von_bank_id != "A":
                st.session_state.balances["Zentralbank"]["Assets"][f"Forderung {bank_name_von}"] += betrag
                st.session_state.balances["Zentralbank"]["Liabilities"][f"Reserve {bank_name_von}"] += betrag
                st.session_state.balances[bank_name_von]["Assets"][f"Reserve bei ZB {von_bank_id}"] += betrag
                st.session_state.balances[bank_name_von]["Liabilities"][f"Kredit bei ZB {von_bank_id}"] += betrag
                st.session_state.highlights_green = [f"Reserve bei ZB {von_bank_id}", f"Forderung {bank_name_von}"
                    ,f"Reserve {bank_name_von}",f"Kredit bei ZB {von_bank_id}"]
                st.session_state.logs.append(f"🏛️ ZB stellt {bank_name_von} Reserven bereit.")
            else:
                st.session_state.logs.append(f"🛒 Interner Kauf: Eigentümer zahlt innerhalb von Bank A.")

        elif schritt == 3:
            st.session_state.balances["Eigentümer"]["Assets"][f"Guthaben bei {von_bank_id}"] -= betrag
            st.session_state.balances[bank_name_von]["Liabilities"][einlage_key_bank] -= betrag
            st.session_state.highlights_red = [f"Guthaben bei {von_bank_id}",einlage_key_bank]
        elif schritt == 4:
            if von_bank_id != "A":
                st.session_state.balances[bank_name_von]["Assets"][f"Reserve bei ZB {von_bank_id}"] -= betrag
                st.session_state.balances["Zentralbank"]["Liabilities"][f"Reserve {bank_name_von}"] -= betrag
                st.session_state.highlights_red = [f"Reserve bei ZB {von_bank_id}",f"Reserve {bank_name_von}"]
                st.session_state.logs.append(f"🏦 Reserven fließen von {bank_name_von} zu Bank A.")
            else:
                None

        elif schritt == 5:
            # --- DER FIX: Reserven nur erhöhen, wenn sie von einer ANDEREN Bank kommen ---
            if von_bank_id != "A":
                st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank A"] += betrag
                st.session_state.balances["Bank A"]["Assets"]["Reserve bei ZB A"] += betrag
                st.session_state.highlights_green = ["Reserve Bank A", "Reserve bei ZB A"]
            else:
                # Interner Transfer: Keine ZB-Reserven involviert!
                None
        elif schritt == 6:
            st.session_state.balances["Bank A"]["Liabilities"]["Einlage UK"] += betrag
            st.session_state.balances["UK"]["Assets"]["Bankguthaben bei A"] += betrag
            st.session_state.highlights_green = ["Einlage UK","Bankguthaben bei A"]
            st.session_state.logs.append("💰 UK erhält Verkaufserlös bei Bank A.")

        elif schritt == 7:
            st.session_state.value_balances["UK"]["Warenbestand"] -= betrag
            st.session_state.balances["UK"]["Assets"]["Warenbestand UK"] -= betrag
            st.session_state.balances["Eigentümer"]["Assets"]["Gebrauchsvermögen E"] += betrag

            # Hier vorsicht mit dem Key-Namen in value_balances:
            if f"Gebrauchsvermögen {von_bank_id}" in st.session_state.value_balances["Eigentümer"]:
                st.session_state.value_balances["Eigentümer"][f"Gebrauchsvermögen {von_bank_id}"] += betrag

            st.session_state.highlights_red = ["Warenbestand UK"]
            st.session_state.highlights_green = ["Gebrauchsvermögen E"]
            st.session_state.logs.append(f"📦 Waren geliefert. Gebrauchsvermögen E erhöht.")
            C_bereinigt = betrag * (1 - (1 / (1 + r)) * (1 - vk))
            st.session_state.current_C_roh += C_bereinigt
        return True
    except KeyError as e:
        st.error(f"KeyError: Das Konto {e} wurde nicht gefunden!")
        st.session_state.pending_steps = []
        return False


def zentralbank_clearing():
    """
    Verrechnet Forderungen und Verbindlichkeiten der Banken gegenüber der Zentralbank.
    Nur der Netto-Saldo bleibt übrig.
    """
    banken = ["Bank A", "Bank B", "Bank C"]

    for bank_id in banken:
        # 1. Beträge holen
        # Annahme: Assets heißen 'Reserve bei ZB A/B/C' und Liabilities 'Kredit bei ZB A/B/C'
        # Wir müssen den Key dynamisch finden oder festlegen:
        suffix = bank_id.split()[-1]  # Ergibt 'A', 'B' oder 'C'

        reserve_key = f"Reserve bei ZB {suffix}"
        kredit_key = f"Kredit bei ZB {suffix}"
        zb_forderung_key = f"Forderung {bank_id}"
        zb_reserve_key = f"Reserve {bank_id}"

        # Aktuelle Werte aus dem State
        reserves = st.session_state.balances[bank_id]["Assets"].get(reserve_key, 0)
        kredite = st.session_state.balances[bank_id]["Liabilities"].get(kredit_key, 0)

        if reserves > 0 and kredite > 0:
            # Der Betrag, der gecleart werden kann, ist das Minimum von beiden
            clearing_betrag = min(reserves, kredite)

            # Buchung bei der Geschäftsbank
            st.session_state.balances[bank_id]["Assets"][reserve_key] -= clearing_betrag
            st.session_state.balances[bank_id]["Liabilities"][kredit_key] -= clearing_betrag

            # Buchung bei der Zentralbank (Spiegelbildlich)
            st.session_state.balances["Zentralbank"]["Assets"][zb_forderung_key] -= clearing_betrag
            st.session_state.balances["Zentralbank"]["Liabilities"][zb_reserve_key] -= clearing_betrag

            st.session_state.logs.append(f"🔄 Clearing {bank_id}: {clearing_betrag}€ wurden netto verrechnet.")
            st.session_state.highlights_green += [reserve_key, kredit_key, zb_forderung_key, zb_reserve_key]

    return True


def regeneration_prozess():
    """
    Verbraucht Gebrauchsvermögen (Konsum) und regeneriert Arbeitskraft bei Arbeitern.
    """
    # --- 1. BESCHÄFTIGTE / ARBEITER ---
    # Wir nehmen den gesamten Bestand an Gebrauchsvermögen B als Regenerationsbasis
    Lebensmittel = st.session_state.balances["Beschäftigte"]["Assets"]["Gebrauchsvermögen B"]

    if Lebensmittel > 0:
        # Finanziell: Gebrauchsvermögen und EK sinken (Wertverzehr)
        st.session_state.balances["Beschäftigte"]["Assets"]["Gebrauchsvermögen B"] -= Lebensmittel
        st.session_state.balances["Beschäftigte"]["Liabilities"]["Eigenkapital Beschäftigte"] -= Lebensmittel

        # Realwirtschaftlich: Arbeitskraft steigt im value_balance
        st.session_state.value_balances["Beschäftigte"]["Arbeitskraft"] += Lebensmittel
        st.session_state.value_balances["Beschäftigte"]["Gebrauchsvermögen B"] -= Lebensmittel

        st.session_state.logs.append(
            f"🥗 Arbeiter haben konsumiert: {Lebensmittel}€ Gebrauchsvermögen -> Arbeitskraft regeneriert.")

    # --- 2. EIGENTÜMER ---
    konsum_owner = st.session_state.balances["Eigentümer"]["Assets"]["Gebrauchsvermögen E"]

    A = st.session_state.value_balances["Eigentümer"][f"Gebrauchsvermögen A"]
    B = st.session_state.value_balances["Eigentümer"][f"Gebrauchsvermögen B"]
    C = st.session_state.value_balances["Eigentümer"][f"Gebrauchsvermögen C"]

    if konsum_owner > 0:
        # Finanziell: Gebrauchsvermögen sinkt, EK sinkt (hier muss man schauen, welches EK-Konto man mindert)
        st.session_state.balances["Eigentümer"]["Assets"]["Gebrauchsvermögen E"] -= konsum_owner
        # Wir mindern hier pauschal das Bankenbesitzer-EK oder verteilen es – hier als Beispiel:
        st.session_state.balances["Eigentümer"]["Liabilities"]["Eigenk. Eigentümer UK"] -= A
        st.session_state.balances["Eigentümer"]["Liabilities"]["Eigenk. Eigentümer UI"] -= B
        st.session_state.balances["Eigentümer"]["Liabilities"]["Eigenk. Bankenbesitzer"] -= C

        st.session_state.value_balances["Eigentümer"][f"Gebrauchsvermögen A"] = 0
        st.session_state.value_balances["Eigentümer"][f"Gebrauchsvermögen B"] = 0
        st.session_state.value_balances["Eigentümer"][f"Gebrauchsvermögen C"] = 0

        # Bei Eigentümern wird KEINE Arbeitskraft regeneriert (laut deiner Vorgabe)
        st.session_state.logs.append(f"🍷 Eigentümer haben konsumiert: {konsum_owner}€ Gebrauchsvermögen verbraucht.")

    st.session_state.highlights = ["Gebrauchsvermögen B", "Gebrauchsvermögen E", "Arbeitskraft",
                                   "Eigenkapital Beschäftigte","Eigenk. Eigentümer UK","Eigenk. Eigentümer UI"
        ,"Eigenk. Bankenbesitzer"]
    return True



"""Introduction"""
#### Funktionen für Introdukction

import streamlit as st


def zb_kredit_prozess(betrag, bank_name, speed, schritt):
    # Mapping für die unterschiedlichen Key-Stile in deiner neuen Bilanz
    if "London" in bank_name:
        b_id = "LB"
        b_full = "London Bank"
        anleihen_key = "Staatsanleihen LB"
        anleihen_key_verpfändet = "Staatsanleihen (verpfändet) LB"

    else:
        b_id = "EB"
        b_full = "Edinburgh Bank"
        anleihen_key = "Staatsanleihen EB"
        anleihen_key_verpfändet = "Staatsanleihen (verpfändet) EB"


    try:
        # --- SCHRITT 0: Validierung (Sicherheiten-Check) ---
        if schritt == 0:
            vorhandene_anleihen = st.session_state.balances[bank_name]["Assets"][anleihen_key]

            if betrag > vorhandene_anleihen:
                st.session_state.logs.append(f"❌ {bank_name} hat nicht genug Sicherheiten!")
                st.session_state.logs.append(f"Anleihen: {vorhandene_anleihen}£ | Benötigt: {betrag}£")
                st.session_state.pending_steps = []
                return False

            # Plan aufstellen: Alle beteiligten Konten markieren
            st.session_state.highlights_plan = [
                anleihen_key,
                anleihen_key_verpfändet,
                f"Forderung {b_full}",
                f"Refinanzierungskredit bei BoE {b_id}",
                f"Reserve bei BoE {b_id}",
                f"Reserve {b_full}"
            ]
            st.session_state.logs.append(
                f"📜 {bank_name} beantragt Liquidität bei der BoE gegen Verpfändung von Anleihen.")

        # --- SCHRITT 1: Kreditvertrag (Bilanzverlängerung ZB / Bank) ---
        elif schritt == 1:
            # BoE bekommt Forderung, Geschäftsbank bekommt Verbindlichkeit
            st.session_state.balances["Bank of England (BoE)"]["Assets"][f"Forderung {b_full}"] += betrag
            st.session_state.balances[bank_name]["Liabilities"][f"Refinanzierungskredit bei BoE {b_id}"] += betrag

            st.session_state.highlights_green = [f"Forderung {b_full}", f"Refinanzierungskredit bei BoE {b_id}"]
            st.session_state.logs.append(f"🏛️ BoE gewährt Kredit an {b_id}. Schulden der Bank steigen.")

        # --- SCHRITT 2: Gutschrift der Reserven ---
        elif schritt == 2:
            # BoE schreibt Reserve gut, Bank verbucht Reserve-Asset
            st.session_state.balances[bank_name]["Assets"][f"Reserve bei BoE {b_id}"] += betrag
            st.session_state.balances["Bank of England (BoE)"]["Liabilities"][f"Reserve {b_full}"] += betrag

            st.session_state.highlights_green = [f"Reserve bei BoE {b_id}", f"Reserve {b_full}"]
            # Wir lassen die Anleihen gelb leuchten als Hinweis auf die Besicherung
            st.session_state.highlights_plan = [anleihen_key,anleihen_key_verpfändet]
            st.session_state.logs.append(f"💰 {b_full} erhält Reserven auf ihrem BoE-Konto.")

        # --- SCHRITT 3: Abschluss & Cleanup ---
        elif schritt == 3:
            st.session_state.balances[bank_name]["Assets"][anleihen_key] -= betrag
            st.session_state.highlights_red = [anleihen_key]
            st.session_state.logs.append(f"📈 Als Sicherheit verpfändet {b_full} eine Staatsanleihe (REPO).")
        elif schritt == 4:
            st.session_state.balances[bank_name]["Assets"][anleihen_key_verpfändet] += betrag
            #st.session_state.highlights_plan = []
            st.session_state.highlights_green = [anleihen_key_verpfändet]
            st.session_state.logs.append(f"✅ Refinanzierung abgeschlossen. {b_full} ist nun liquide.")

        return True

    except KeyError as e:
        st.error(f"Fehler: Das Konto '{e}' wurde in der Bilanz nicht gefunden!")
        st.session_state.pending_steps = []
        return False


def bargeld_intro(betrag, kunde_name, bank_name, speed, schritt):
    # 1. Kürzel und IDs extrahieren
    b_id = "LB" if "London" in bank_name else "EB"
    k_init = kunde_name[0]  # "K", "F" oder "A"

    # Namen säubern für BoE-Keys (aus "London Bank (LB)" wird "London Bank")
    clean_bank = bank_name.split(" (")[0]
    zb_name = "Bank of England (BoE)"

    # --- DYNAMISCHE KONTENNAMEN ---
    konto_guthaben = f"Bankguthaben {kunde_name} bei {b_id}"
    konto_einlage = f"Einlage {kunde_name}"
    konto_reserve_bank = f"Reserve bei BoE {b_id}"
    konto_reserve_zb = f"Reserve {clean_bank}"  # Muss "Reserve London Bank" sein
    konto_bargeld = f"Bargeld {k_init}."  # Muss "Bargeld K." sein

    try:
        # Schritt 0: Validierung (Guthaben & Bankrun-Check)
        if schritt == 0:
            guthaben = st.session_state.balances[kunde_name]["Assets"][konto_guthaben]
            reserve_bank = st.session_state.balances[bank_name]["Assets"][konto_reserve_bank]

            if betrag > guthaben:
                st.session_state.logs.append(f"❌️ {kunde_name} hat nicht genug Guthaben bei der {b_id}!")
                st.session_state.pending_steps = []
                return False

            if betrag > reserve_bank:
                st.session_state.logs.append(f"💥 BANKRUN! {bank_name} fehlen Reserven für die Auszahlung.")
                st.session_state.logs.append("💡 Tipp: Verpfände erst Anleihen bei der BoE.")
                st.session_state.pending_steps = []
                return False

            st.session_state.highlights_plan = [
                konto_guthaben, konto_einlage,
                konto_reserve_bank, konto_reserve_zb,
                konto_bargeld, "Bargeldumlauf"
            ]
            st.session_state.logs.append(f"🔍 {kunde_name} fordert {betrag}£ in bar an.")

        # Schritt 1: Giralgeld wird vernichtet
        elif schritt == 1:
            st.session_state.balances[kunde_name]["Assets"][konto_guthaben] -= betrag
            st.session_state.balances[bank_name]["Liabilities"][konto_einlage] -= betrag
            st.session_state.highlights_red = [konto_guthaben, konto_einlage]
            st.session_state.logs.append(f"📉 Giralgeld von {kunde_name} wurde ausgebucht.")

        # Schritt 2: Bank tauscht Reserven bei der BoE gegen Cash
        elif schritt == 2:
            st.session_state.balances[bank_name]["Assets"][konto_reserve_bank] -= betrag
            st.session_state.balances[zb_name]["Liabilities"][konto_reserve_zb] -= betrag
            st.session_state.highlights_red = [konto_reserve_bank, konto_reserve_zb]
            st.session_state.logs.append(f"🏛️ {bank_name} reduziert Reserven bei der BoE.")

        # Schritt 3: Bargeld wird physisch beim Kunden eingebucht
        elif schritt == 3:
            st.session_state.balances[zb_name]["Liabilities"]["Bargeldumlauf"] += betrag
            st.session_state.balances[kunde_name]["Assets"][konto_bargeld] += betrag
            st.session_state.highlights_green = [konto_bargeld, "Bargeldumlauf"]
            st.session_state.logs.append(f"💵 {kunde_name} hält nun {betrag}£ physisches Bargeld.")

        # Schritt 4: Cleanup
        elif schritt == 4:
            st.session_state.highlights_plan = []
            st.session_state.highlights_green = []
            st.session_state.highlights_red = []
            st.session_state.logs.append(f"✅ Bargeld-Abhebung abgeschlossen.")

        return True

    except KeyError as e:
        st.error(f"Fehler: Das Konto {e} wurde nicht gefunden!")
        st.session_state.pending_steps = []
        return False


def interbank_transfer(betrag, sender, empfaenger, bank_sender, bank_empfaenger, speed, schritt):
    """
    Kombinierte Logik für:
    1. Interne Umbuchung (z.B. Friedrich -> Karl innerhalb LB)
    2. Interbank-Transfer (z.B. Friedrich -> Adam via BoE)
    """
    # Kürzel extrahieren
    s_id = "LB" if "London" in bank_sender else "EB"
    e_id = "LB" if "London" in bank_empfaenger else "EB"
    zb_name = "Bank of England (BoE)"

    # Prüfen, ob es dieselbe Bank ist
    is_internal = (bank_sender == bank_empfaenger)

    # Namen für Sachvermögen (K. / F. / A.)
    s_short = sender[0] + "."
    e_short = empfaenger[0] + "."

    try:
        # --- SCHRITT 0: Validierung ---
        if schritt == 0:
            guthaben = st.session_state.balances[sender]["Assets"][f"Bankguthaben {sender} bei {s_id}"]
            if betrag > guthaben:
                st.error(f"⚠️ {sender} hat nicht genug Guthaben!")
                st.session_state.logs.append(f"⚠️ {sender} hat nicht genug Guthaben!")
                st.session_state.pending_steps = []
                return False

            # Reserven-Check nur nötig, wenn es NICHT intern ist
            if not is_internal:
                reserven = st.session_state.balances[bank_sender]["Assets"][f"Reserve bei BoE {s_id}"]
                if betrag > reserven:
                    st.error(f"⚠️ {bank_sender} hat nicht genug Reserven für den Transfer zu einer anderen Bank!")
                    st.session_state.logs.append(f"⚠️ {bank_sender} hat nicht genug Reserven für den Transfer zu einer anderen Bank!")
                    st.session_state.pending_steps = []
                    return False

            if is_internal:
                st.session_state.highlights_plan = [
                f"Bankguthaben {sender} bei {s_id}", f"Einlage {sender}",
                f"Bankguthaben {empfaenger} bei {e_id}", f"Einlage {empfaenger}",
                f"Sachvermögen {s_short}", f"Sachvermögen {e_short}"
            ]

            if not is_internal:
                st.session_state.highlights_plan = [
                    f"Bankguthaben {sender} bei {s_id}", f"Einlage {sender}",
                    f"Bankguthaben {empfaenger} bei {e_id}", f"Einlage {empfaenger}",
                    f"Sachvermögen {s_short}", f"Sachvermögen {e_short}",
                    f"Reserve bei BoE {s_id}", f"Reserve London Bank",
                    f"Reserve bei BoE {e_id}", f"Reserve Edinburgh Bank"]

            st.session_state.logs.append(f"🔄 Transfer gestartet: {sender} ➔ {empfaenger} ({betrag}£)")

        # --- SCHRITT 1: Abbuchung beim Sender ---
        elif schritt == 1:
            st.session_state.balances[sender]["Assets"][f"Bankguthaben {sender} bei {s_id}"] -= betrag
            st.session_state.balances[bank_sender]["Liabilities"][f"Einlage {sender}"] -= betrag
            st.session_state.highlights_red = [f"Bankguthaben {sender} bei {s_id}", f"Einlage {sender}"]
            st.session_state.logs.append(f"📉 {bank_sender} belastet das Konto von {sender}.")

        # --- SCHRITT 2: Reserven-Transfer (NUR wenn Interbank) ---
        elif schritt == 2:
            if is_internal:
                st.session_state.logs.append("ℹ️ Interner Transfer: Keine BoE-Reserven nötig.")
            else:
                clean_s = bank_sender.split(" (")[0]
                clean_e = bank_empfaenger.split(" (")[0]
                st.session_state.balances[bank_sender]["Assets"][f"Reserve bei BoE {s_id}"] -= betrag

                # BoE-Liabilities (nutzen den sauberen Namen ohne Klammern)
                st.session_state.balances[zb_name]["Liabilities"][f"Reserve {clean_s}"] -= betrag
                st.session_state.balances[zb_name]["Liabilities"][f"Reserve {clean_e}"] += betrag
                # Bank-Assets Empfänger
                st.session_state.balances[bank_empfaenger]["Assets"][f"Reserve bei BoE {e_id}"] += betrag

                st.session_state.highlights_red = [f"Reserve bei BoE {s_id}", f"Reserve {clean_s}"]
                st.session_state.highlights_green = [f"Reserve bei BoE {e_id}", f"Reserve {clean_e}"]
                st.session_state.logs.append(f"🏛️ BoE schichtet Reserven von {clean_s} zu {clean_e} um.")        # --- SCHRITT 3: Gutschrift beim Empfänger ---
        elif schritt == 3:
            st.session_state.balances[bank_empfaenger]["Liabilities"][f"Einlage {empfaenger}"] += betrag
            st.session_state.balances[empfaenger]["Assets"][f"Bankguthaben {empfaenger} bei {e_id}"] += betrag
            st.session_state.highlights_green = [f"Bankguthaben {empfaenger} bei {e_id}", f"Einlage {empfaenger}"]
            st.session_state.logs.append(f"✅ {bank_empfaenger} schreibt {empfaenger} den Betrag gut.")

        # --- SCHRITT 4: Sachvermögen-Übertragung (Lieferung) ---
        elif schritt == 4:
            st.session_state.balances[empfaenger]["Assets"][f"Sachvermögen {e_short}"] -= betrag
            st.session_state.balances[sender]["Assets"][f"Sachvermögen {s_short}"] += betrag
            st.session_state.highlights_red = [f"Sachvermögen {e_short}"]
            st.session_state.highlights_green = [f"Sachvermögen {s_short}"]
            st.session_state.logs.append(f"📦 Sachwert wurde im Gegenzug an {sender} geliefert.")

        # --- SCHRITT 5: Abschluss ---
        elif schritt == 5:
            st.session_state.highlights_plan = []
            st.session_state.highlights_green = []
            st.session_state.highlights_red = []

        return True

    except KeyError as e:
        st.error(f"Fehler: Das Konto {e} wurde nicht gefunden!")
        st.session_state.pending_steps = []
        return False

def prozess_kredit_intro(betrag, interest_rate, firma, bank, speed, schritt):
    """
    Kreditprozess für das historische Setting:
    Karl/Friedrich bei London Bank (LB) oder Adam bei Edinburgh Bank (EB).
    """
    # 1. Kürzel extrahieren (LB oder EB)
    b_short = "LB" if "London" in bank else "EB"

    # 2. Vornamen für Keys isolieren (Karl, Friedrich, Adam)
    name = firma

    # --- DYNAMISCHE KONTENNAMEN (Mapping auf deinen neuen State) ---
    asset_firma = f"Bankguthaben {name} bei {b_short}"
    liab_firma = f"Darlehen bei {b_short}" if name == "Karl" else f"Darlehen {name} bei {b_short}"
    # Sonderfall Adam: In deiner Bilanz heißt es "Kredit Adam bei EB"
    if name == "Adam": liab_firma = "Darlehen Adam bei EB"

    asset_bank = f"Kredite {name}"
    liab_bank = f"Einlage {name}"

    ek_name_firma = f"Eigenkapital {name[0]}."  # K. / F. / A.
    ek_name_bank = f"Eigenkapital {b_short}"

    try:
        # --- FALL A: KREDITAUFNAHME (GELDSCHÖPFUNG) ---
        if betrag > 0:
            if schritt == 0:
                st.session_state.highlights_plan = [asset_firma, liab_bank, asset_bank, liab_firma]
                st.session_state.logs.append(f"📜 {name} beantragt einen Kredit bei der {bank}.")

            elif schritt == 1:
                # Giralgeldschöpfung: Kunde bekommt Guthaben, Bank hat Einlagen-Verbindlichkeit
                st.session_state.balances[firma]["Assets"][asset_firma] += betrag
                st.session_state.balances[bank]["Liabilities"][liab_bank] += betrag
                st.session_state.highlights_green = [asset_firma, liab_bank]
                st.session_state.logs.append(f"🏦 {bank}: Schöpft Giralgeld für {name}. Die Geldmenge steigt!")

            elif schritt == 2:
                # Bilanzverlängerung vervollständigen: Bank hat Forderung, Kunde hat Kredit-Schulden
                st.session_state.balances[bank]["Assets"][asset_bank] += betrag
                st.session_state.balances[firma]["Liabilities"][liab_firma] += betrag
                st.session_state.highlights_green = [asset_bank, liab_firma]

            elif schritt == 3:
                st.session_state.highlights_plan = []
                st.session_state.highlights_green = []
                st.session_state.logs.append(f"✅ Kreditvertrag über {betrag}£ erfolgreich gebucht.")

        # --- FALL B: TILGUNG & ZINSEN (GELDVERNICHTUNG) ---
        elif betrag < 0:
            kredit_anteil = abs(betrag)
            zins_anteil = round(kredit_anteil * interest_rate, 2)

            if schritt == 0:
                st.session_state.highlights_plan = [asset_firma, liab_bank, asset_bank, liab_firma, ek_name_firma,
                                                    ek_name_bank]
                st.session_state.logs.append(f"📉 {name} leistet eine Zahlung an die {bank} (Tilgung + Zins).")

            elif schritt == 1:
                # Tilgungsteil: Bankguthaben und Einlage sinken (Geldvernichtung)
                st.session_state.balances[firma]["Assets"][asset_firma] -= kredit_anteil
                st.session_state.balances[bank]["Liabilities"][liab_bank] -= kredit_anteil
                st.session_state.highlights_red = [asset_firma, liab_bank]
                st.session_state.logs.append(f"🔥 {kredit_anteil}£ Giralgeld wurden durch Tilgung vernichtet.")

            elif schritt == 2:
                # Kreditforderung der Bank erlischt
                st.session_state.balances[bank]["Assets"][asset_bank] -= kredit_anteil
                st.session_state.balances[firma]["Liabilities"][liab_firma] -= kredit_anteil
                st.session_state.highlights_red = [asset_bank, liab_firma]

            elif schritt == 3:
                # Zinszahlung: Mindert EK des Kunden
                st.session_state.balances[firma]["Assets"][asset_firma] -= zins_anteil
                st.session_state.balances[firma]["Liabilities"][ek_name_firma] -= zins_anteil
                st.session_state.highlights_red = [ek_name_firma, asset_firma]
                st.session_state.logs.append(f"💸 Zinsen in Höhe von {zins_anteil}£ an {bank} gezahlt.")

            elif schritt == 4:
                # Zinsgewinn für die Bank: Verschiebung von Einlage zu Eigenkapital
                st.session_state.balances[bank]["Liabilities"][liab_bank] -= zins_anteil
                st.session_state.balances[bank]["Liabilities"][ek_name_bank] += zins_anteil
                st.session_state.highlights_green = [ek_name_bank]
                st.session_state.highlights_red = [liab_bank]

            elif schritt == 5:
                st.session_state.highlights_plan = []
                st.session_state.highlights_green = []
                st.session_state.highlights_red = []
                st.session_state.logs.append(f"🏛️ {bank}: Zinsertrag verbucht.")

        return True

    except KeyError as e:
        st.error(f"Konto-Fehler: {e} nicht gefunden. Prüfe die Keys!")
        st.session_state.pending_steps = []
        return False
"""Staatsfinanzierung Government"""
def staat_prozess(aktion, betrag, schritt):
    try:
        if aktion == "Kredit ZB":
            if schritt == 1:
                st.session_state.highlights_plan = ["Reserve London Bank", "Reserve bei BoE",
                                                    "Refinanzierungskredit bei BoE", "Forderung London Bank"]
            elif schritt == 2:
                st.session_state.balances["London Bank"]["Liabilities"]["Refinanzierungskredit bei BoE"] += betrag
                st.session_state.balances["Bank of England"]["Assets"]["Forderung London Bank"] += betrag
                st.session_state.highlights_green = ["Refinanzierungskredit bei BoE", "Forderung London Bank"]
                st.session_state.logs.append(f"Kredit: {betrag}€ Kredit erzeugt.")
            elif schritt == 3:
                st.session_state.balances["London Bank"]["Assets"]["Reserve bei BoE"] += betrag
                st.session_state.balances["Bank of England"]["Liabilities"]["Reserve London Bank"] += betrag
                st.session_state.highlights_green = ["Reserve London Bank","Reserve bei BoE"]
            elif schritt == 4:
                st.session_state.highlights_plan = []
                st.session_state.logs.append(f"Kredit: {betrag}€ Reserve erzeugt.")

        elif aktion == "erzeugen":
            if schritt == 1:
                st.session_state.highlights_plan = ["Anleihen Eigenbestand", "Staatsanleihen (Gesamt)"]
            if schritt == 2:
                st.session_state.balances["Staat"]["Assets"]["Anleihen Eigenbestand"] += betrag
                st.session_state.balances["Staat"]["Liabilities"]["Staatsanleihen (Gesamt)"] += betrag
                st.session_state.highlights_green = ["Anleihen Eigenbestand", "Staatsanleihen (Gesamt)"]
            elif schritt == 3:
                st.session_state.highlights_plan = []
                st.session_state.logs.append(f"📜 Staat: {betrag}€ Anleihen im Eigenbestand erzeugt.")

        elif aktion == "verkaufen":
            if schritt == 0:
                bestand_staat = st.session_state.balances["Staat"]["Assets"]["Anleihen Eigenbestand"]
                guthaben_bank = st.session_state.balances["London Bank"]["Assets"]["Reserve bei BoE"]
                if betrag > bestand_staat:
                    st.session_state.logs.append(f"❌ Der Staat hat nicht genug Anleihen im Eigenbestand ({bestand_staat}£ verfügbar).")
                    st.session_state.pending_steps = []  # Stoppt die automatische Abfolge
                    return False
                if betrag > guthaben_bank:
                    st.session_state.logs.append(f"❌ Die Bank hat nicht genug Reserven für den Kauf ({guthaben_bank}£ verfügbar).")
                    st.session_state.pending_steps = []  # Stoppt die automatische Abfolge
                    return False
            elif schritt == 1:
                st.session_state.highlights_plan = ["Anleihen Eigenbestand","Staatsanleihen"
                    ,"Guthaben Staat","Guthaben bei BoE","Reserve bei BoE", "Reserve London Bank"]
            elif schritt == 2:
                st.session_state.balances["London Bank"]["Assets"]["Reserve bei BoE"] -= betrag
                st.session_state.balances["Bank of England"]["Liabilities"]["Reserve London Bank"] -= betrag
                st.session_state.highlights_red = ["Reserve bei BoE", "Reserve London Bank"]
                st.session_state.logs.append(f"🏛️ Verkauf Schritt 1: Bank zahlt Geld.")
            elif schritt == 3:
                st.session_state.balances["Bank of England"]["Liabilities"]["Guthaben Staat"] += betrag
                st.session_state.balances["Staat"]["Assets"]["Guthaben bei BoE"] += betrag
                st.session_state.highlights_green = ["Guthaben Staat","Guthaben bei BoE"]
                st.session_state.logs.append(f"🏛️ Verkauf Schritt 2: Bank of England tauscht Reserven.")
            elif schritt == 4:
                st.session_state.balances["Staat"]["Assets"]["Anleihen Eigenbestand"] -= betrag
                st.session_state.balances["London Bank"]["Assets"]["Staatsanleihen"] += betrag
                st.session_state.highlights_green = ["Staatsanleihen"]
                st.session_state.highlights_red = ["Anleihen Eigenbestand"]
            elif schritt == 5:
                st.session_state.highlights_plan = []
                st.session_state.logs.append(f"🏛️ Verkauf Schritt 3: Staat verkauft die Anleihe.")

        elif aktion == "lohn":
            if schritt == 0:
                guthaben_staat = st.session_state.balances["Staat"]["Assets"]["Guthaben bei BoE"]
                if betrag > guthaben_staat:
                    st.session_state.logs.append(f"❌ Der Staat ist zahlungsunfähig! Guthaben: {guthaben_staat}£, Benötigt: {betrag}£.")
                    st.session_state.logs.append("⚠️ Lohnzahlung abgebrochen: Staatliche Reserven unzureichend.")
                    st.session_state.pending_steps = []
                    return False
            elif schritt == 1:
                st.session_state.highlights_plan = ["Guthaben bei BoE", "Eigenkapital Staat", "Guthaben Staat"
                    ,"Reserve bei BoE","Reserve London Bank","Bankguthaben", "Einlage Milton", "Eigenkapital Milton"]
            elif schritt == 2:
                st.session_state.balances["Staat"]["Assets"]["Guthaben bei BoE"] -= betrag
                st.session_state.balances["Bank of England"]["Liabilities"]["Guthaben Staat"] -= betrag
                st.session_state.highlights_red = ["Guthaben bei BoE", "Guthaben Staat"]
                st.session_state.logs.append(f"💸 Lohn Schritt 1: Staat weist BoE zur Zahlung an.")
            elif schritt == 3:
                st.session_state.balances["Bank of England"]["Liabilities"]["Reserve London Bank"] += betrag
                st.session_state.balances["London Bank"]["Assets"]["Reserve bei BoE"] += betrag
                st.session_state.highlights_green = ["Reserve bei BoE","Reserve London Bank"]
                st.session_state.logs.append(f"💸 Lohn Schritt 2: Bank of England tauscht Reserven.")
            elif schritt == 4:
                st.session_state.balances["London Bank"]["Liabilities"]["Einlage Milton"] += betrag
                st.session_state.balances["Milton"]["Assets"]["Bankguthaben"] += betrag
                st.session_state.highlights_green = ["Bankguthaben", "Einlage Milton"]
            elif schritt == 5:
                st.session_state.balances["Staat"]["Liabilities"]["Eigenkapital Staat"] -= betrag
                st.session_state.balances["Milton"]["Liabilities"]["Eigenkapital Milton"] += betrag
                st.session_state.highlights_green = ["Eigenkapital Milton"]
                st.session_state.highlights_red = ["Eigenkapital Staat"]
            elif schritt == 6:
                st.session_state.highlights_plan = []
                st.session_state.logs.append(f"💸 Lohn Schritt 3: Milton erhält Giralgeld.")

        elif aktion == "steuern":
            bankguthaben = st.session_state.balances["Milton"]["Assets"]["Bankguthaben"]
            bargeld = st.session_state.balances["Milton"]["Assets"]["Bargeld"]
            if schritt == 1:
                if betrag > bankguthaben:
                     st.session_state.logs.append("❌ Du hast nicht genug Guthaben, um deine Steuern zu zahlen. Verdiene Geld oder zahle Bargeld ein!")
                     st.session_state.pending_steps = []
                     return False

                st.session_state.highlights_plan = ["Bankguthaben", "Einlage Milton", "Eigenkapital Milton",
                                                    "Reserve bei BoE", "Reserve London Bank","Guthaben bei BoE",
                                                    "Eigenkapital Staat", "Guthaben Staat"]

            elif schritt == 2:
                st.session_state.balances["London Bank"]["Liabilities"]["Einlage Milton"] -= betrag
                st.session_state.balances["Milton"]["Assets"]["Bankguthaben"] -= betrag
                st.session_state.highlights_red = ["Bankguthaben", "Einlage Milton"]
                st.session_state.logs.append(f"💸 Steuern Schritt 1: Milton zahlt Steuern.")
            elif schritt == 3:
                st.session_state.balances["Bank of England"]["Liabilities"]["Reserve London Bank"] -= betrag
                st.session_state.balances["London Bank"]["Assets"]["Reserve bei BoE"] -= betrag
                st.session_state.highlights_red = ["Reserve bei BoE", "Reserve London Bank"]
                st.session_state.logs.append(f"💸 Steuern Schritt 2: Bank of England tauscht Reserven.")
            elif schritt == 4:
                st.session_state.balances["Staat"]["Assets"]["Guthaben bei BoE"] += betrag
                st.session_state.balances["Bank of England"]["Liabilities"]["Guthaben Staat"] += betrag
                st.session_state.highlights_green = ["Guthaben bei BoE","Guthaben Staat"]
            elif schritt == 5:
                st.session_state.balances["Milton"]["Liabilities"]["Eigenkapital Milton"] -= betrag
                st.session_state.balances["Staat"]["Liabilities"]["Eigenkapital Staat"] += betrag
                st.session_state.highlights_red = ["Eigenkapital Milton"]
                st.session_state.highlights_green = ["Eigenkapital Staat"]
            elif schritt == 6:
                st.session_state.highlights_plan = []
                st.session_state.logs.append(f"💸 Steuern Schritt 3: Staat erhält Reserven.")

        elif aktion == "bargeld_abheben":
            guthaben = st.session_state.balances["Milton"]["Assets"]["Bankguthaben"]
            reserve_bank = st.session_state.balances["London Bank"]["Assets"]["Reserve bei BoE"]
            if schritt == 0:
                if betrag > guthaben:
                    st.session_state.logs.append(f"Zu wenig Guthaben!")
                    st.session_state.pending_steps = []
                    return False
                if betrag > reserve_bank:
                    st.session_state.logs.append(f"💥 BANKRUN! London Bank fehlen Reserven für die Auszahlung.")
                    st.session_state.logs.append("💡 Tipp: Verkaufe erst Anleihen bei der BoE (QE).")
                    st.session_state.pending_steps = []
                    return False

                st.session_state.highlights_plan = ["Bankguthaben", "Einlage Milton",
                                                    "Reserve bei BoE", "Reserve London Bank",
                                                    "Bargeld","Bargeldumlauf"]
            elif schritt == 1:
                st.session_state.balances["London Bank"]["Liabilities"]["Einlage Milton"] -= betrag
                st.session_state.balances["Milton"]["Assets"]["Bankguthaben"] -= betrag
                st.session_state.highlights_red = ["Bankguthaben", "Einlage Milton"]
            elif schritt == 2:
                st.session_state.balances["London Bank"]["Assets"]["Reserve bei BoE"] -= betrag
                st.session_state.balances["Bank of England"]["Liabilities"]["Reserve London Bank"] -= betrag
                st.session_state.highlights_red = ["Reserve bei BoE", "Reserve London Bank"]
            elif schritt == 3:
                st.session_state.balances["Bank of England"]["Liabilities"]["Bargeldumlauf"] += betrag
                st.session_state.balances["Milton"]["Assets"]["Bargeld"] += betrag
                st.session_state.highlights_green = ["Bargeld","Bargeldumlauf"]
            elif schritt == 4:
                st.session_state.highlights_plan = []
                st.session_state.logs.append(f"💸 Bargeld abgehoben.")
        elif aktion == "bargeld_einzahlen":
            bargeld = st.session_state.balances["Milton"]["Assets"]["Bargeld"]
            reserve_bank = st.session_state.balances["London Bank"]["Assets"]["Reserve bei BoE"]
            if schritt == 0:
                if betrag > bargeld:
                    st.session_state.logs.append("❌ Zu wenig Bargeld!")
                    st.session_state.pending_steps = []
                    return False
                st.session_state.highlights_plan = ["Bankguthaben", "Einlage Milton",
                                                    "Reserve bei BoE", "Reserve London Bank",
                                                    "Bargeld","Bargeldumlauf"]
            elif schritt == 1:
                st.session_state.balances["London Bank"]["Liabilities"]["Einlage Milton"] += betrag
                st.session_state.balances["Milton"]["Assets"]["Bankguthaben"] += betrag
                st.session_state.highlights_green = ["Bankguthaben", "Einlage Milton"]
            elif schritt == 2:
                st.session_state.balances["London Bank"]["Assets"]["Reserve bei BoE"] += betrag
                st.session_state.balances["Bank of England"]["Liabilities"]["Reserve London Bank"] += betrag
                st.session_state.highlights_green = ["Reserve bei BoE", "Reserve London Bank"]
            elif schritt == 3:
                st.session_state.balances["Bank of England"]["Liabilities"]["Bargeldumlauf"] -= betrag
                st.session_state.balances["Milton"]["Assets"]["Bargeld"] -= betrag
                st.session_state.highlights_red = ["Bargeld","Bargeldumlauf"]
            elif schritt == 4:
                st.session_state.highlights_plan = []
                st.session_state.logs.append(f"💸 Bargeld eingezahlt.")
        elif aktion == "QE":
            if schritt == 1:
                # Prüfung: Hat die Bank überhaupt Anleihen zum Verkaufen?
                if st.session_state.balances["London Bank"]["Assets"]["Staatsanleihen"] < betrag:
                    st.session_state.logs.append("❌ Abbruch: Bank A besitzt nicht genügend Staatsanleihen für dieses QE-Volumen!")
                    st.session_state.pending_steps = []
                    return False

            elif schritt == 2:
                # Planung: Welche Konten leuchten auf?
                st.session_state.highlights_plan = [
                    "Staatsanleihen", "Bestand Staatsanleihen",
                    "Reserve bei BoE", "Reserve London Bank"
                ]
                st.session_state.logs.append(f"🚀 QE-Programm gestartet: BoE kauft Anleihen im Wert von {betrag}£.")
            elif schritt ==3:
                # Die Bank gibt die Anleihe ab (Asset sinkt), die ZB nimmt sie auf (Asset steigt)
                st.session_state.balances["London Bank"]["Assets"]["Staatsanleihen"] -= betrag
                st.session_state.balances["Bank of England"]["Assets"]["Bestand Staatsanleihen"] += betrag

                st.session_state.highlights_red = ["Staatsanleihen"]
                st.session_state.highlights_green = ["Bestand Staatsanleihen"]
                st.session_state.logs.append(f"📜 Anleihen werden von London Bank zur Bank of England übertragen.")

            elif schritt == 4:
                # Die Zentralbank bezahlt ("druckt") neue Reserven für Bank A
                st.session_state.balances["Bank of England"]["Liabilities"]["Reserve London Bank"] += betrag
                st.session_state.balances["London Bank"]["Assets"]["Reserve bei BoE"] += betrag

                st.session_state.highlights_green = ["Reserve London Bank", "Reserve bei BoE"]
                st.session_state.logs.append(f"💧 Liquiditätsspritze: BoE schreibt London Bank neue Reserven gut.")

            elif schritt == 5:
                st.session_state.highlights_plan = []
                st.session_state.highlights_green = []
                st.session_state.highlights_red = []
                st.session_state.logs.append(f"✅ QE erfolgreich: Die London Bank ist nun liquide.")


        return True
    except Exception as e:
        st.error(f"Fehler: {e}")
        return False

