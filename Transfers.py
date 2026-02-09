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
            if schritt == 1:
                # Schritt 1: Firma kriegt Guthaben, Bank kriegt Verbindlichkeit (Einlage)
                st.session_state.balances[firma]["Assets"][asset_firma] += betrag
                st.session_state.balances[bank]["Liabilities"][liab_bank] += betrag

                st.session_state.highlights = [asset_firma, liab_bank]
                st.session_state.logs.append(f"🏦 {bank}: Schöpft Giralgeld für {firma}.")

            elif schritt == 2:
                # Schritt 2: Bank kriegt Forderung (Kredit), Firma kriegt Verbindlichkeit
                st.session_state.balances[bank]["Assets"][asset_bank] += betrag
                st.session_state.balances[firma]["Liabilities"][liab_firma] += betrag

                st.session_state.highlights = [asset_bank, liab_firma]
                st.session_state.logs.append(f"📝 {firma}: Kreditvertrag über {betrag}€ aktiviert.")

        # --- FALL B: TILGUNG & ZINSEN ---
        elif betrag < 0:
            kredit_anteil = abs(betrag)
            zins_anteil = round(kredit_anteil * interest_rate, 2)
            gesamt_abfluss = kredit_anteil + zins_anteil

            if schritt == 1:
                # Firma zahlt: Guthaben sinkt um Gesamt, Kredit sinkt um Tilgung, EK sinkt um Zins
                st.session_state.balances[firma]["Assets"][asset_firma] -= gesamt_abfluss
                st.session_state.balances[firma]["Liabilities"][liab_firma] -= kredit_anteil

                if ek_firma:
                    st.session_state.balances[firma]["Liabilities"][ek_firma] -= zins_anteil

                # Wir highlighten alle drei betroffenen Konten
                st.session_state.highlights = [asset_firma, liab_firma, ek_firma] if ek_firma else [asset_firma,
                                                                                                    liab_firma]
                st.session_state.logs.append(f"📉 {firma}: Tilgung {kredit_anteil}€ + Zins {zins_anteil}€.")

            elif schritt == 2:
                # Bank erhält: Kredit-Forderung sinkt, Einlagen-Verbindlichkeit sinkt, EK (Gewinn) steigt
                st.session_state.balances[bank]["Assets"][asset_bank] -= kredit_anteil
                st.session_state.balances[bank]["Liabilities"][liab_bank] -= gesamt_abfluss

                if ek_bank in st.session_state.balances[bank]["Liabilities"]:
                    st.session_state.balances[bank]["Liabilities"][ek_bank] += zins_anteil

                st.session_state.highlights = [asset_bank, liab_bank, ek_bank]
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
        if schritt == 1:
            guthaben = st.session_state.balances[firma]["Assets"][f"Bankguthaben bei {bank_buchstabe}"]
            if betrag > guthaben:
                st.session_state.logs.append(f"⚠️ Nicht genügend Guthaben bei {firma}!")
                st.session_state.pending_steps = []
                return False

            st.session_state.balances["Zentralbank"]["Assets"][f"Forderung {bank_firma}"] += betrag
            st.session_state.balances["Zentralbank"]["Liabilities"][f"Reserve {bank_firma}"] += betrag
            st.session_state.balances[bank_firma]["Assets"][f"Reserve bei ZB {bank_buchstabe}"] += betrag
            st.session_state.balances[bank_firma]["Liabilities"][f"Kredit bei ZB {bank_buchstabe}"] += betrag

            # Highlights für ZB-Refinanzierung
            st.session_state.highlights = [f"Reserve bei ZB {bank_buchstabe}", f"Kredit bei ZB {bank_buchstabe}", f"Forderung {bank_firma}", f"Reserve {bank_firma}"]
            st.session_state.logs.append(f"🏛️ ZB stellt {bank_firma} Reserven für die Lohnzahlung bereit.")

        # --- SCHRITT 2: Abbuchung & ZB-Umschichtung ---
        elif schritt == 2:
            st.session_state.balances[firma]["Assets"][f"Bankguthaben bei {bank_buchstabe}"] -= betrag
            st.session_state.balances[firma]["Liabilities"][f"Eigenkapital {firma}"] -= betrag

            st.session_state.balances[bank_firma]["Assets"][f"Reserve bei ZB {bank_buchstabe}"] -= betrag
            st.session_state.balances[bank_firma]["Liabilities"][f"Einlage {firma}"] -= betrag

            st.session_state.balances["Zentralbank"]["Liabilities"][f"Reserve {bank_firma}"] -= betrag
            st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank C"] += betrag

            # Highlights für den Abfluss bei Bank A/B
            st.session_state.highlights = [f"Einlage {firma}",f"Bankguthaben bei {bank_buchstabe}", f"Eigenkapital {firma}", f"Reserve Bank C",f"Reserve bei ZB {bank_buchstabe}",f"Reserve {bank_firma}"]
            st.session_state.logs.append(f"🏦 {bank_firma} bucht Lohn ab und ZB schiebt Reserven zu Bank C.")

        # --- SCHRITT 3: Gutschrift bei Beschäftigte (Bank C) ---
        elif schritt == 3:
            st.session_state.balances["Bank C"]["Assets"]["Reserve bei ZB C"] += betrag
            st.session_state.balances["Bank C"]["Liabilities"]["Einlage Beschäftigte"] += betrag
            st.session_state.balances["Beschäftigte"]["Assets"]["Bankguthaben bei C"] += betrag
            st.session_state.balances["Beschäftigte"]["Liabilities"]["Eigenkapital Beschäftigte"] += betrag

            # Highlights bei den Empfängern
            st.session_state.highlights = ["Bankguthaben bei C", "Einlage Beschäftigte", "Eigenkapital Beschäftigte","Reserve bei ZB C"]
            st.session_state.logs.append(f"👷 Bank C schreibt den Lohn den Beschäftigte gut.")

        # --- SCHRITT 4: Realwirtschaft (Arbeitskraft-Transfer) ---
        elif schritt == 4:
            # Überprüfe, ob die Beträge ankommen
            st.session_state.value_balances["Beschäftigte"]["Arbeitskraft"] -= betrag
            st.session_state.value_balances[firma]["Arbeitskraft"] += betrag

            # WICHTIG: Setze die Highlights auf "Arbeitskraft",
            # damit die Zeile in den Real-Bilanzen unter den Tabellen aufblinkt!
            st.session_state.highlights = ["Arbeitskraft"]
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

            st.session_state.highlights = ["Arbeitskraft", f"Sachvermögen {typ}"]
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

            st.session_state.highlights = [target, ek_key]
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
        if schritt == 1:
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

            # Schritt 1: Refinanzierung Bank A (Käuferbank braucht Reserven)
            st.session_state.balances["Zentralbank"]["Assets"]["Forderung Bank A"] += betrag
            st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank A"] += betrag
            st.session_state.balances["Bank A"]["Assets"]["Reserve bei ZB A"] += betrag
            st.session_state.balances["Bank A"]["Liabilities"]["Kredit bei ZB A"] += betrag

            st.session_state.highlights = ["Reserve bei ZB A", "Forderung Bank A", "Kredit bei ZB A", "Reserve Bank A"]
            st.session_state.logs.append("🏛️ ZB stellt Bank A Reserven für den Kauf bereit.")

        elif schritt == 2:
            # Schritt 2: Abbuchung UK & ZB-Umschichtung zu Bank B
            st.session_state.balances["UK"]["Assets"]["Bankguthaben bei A"] -= betrag
            st.session_state.balances["Bank A"]["Liabilities"]["Einlage UK"] -= betrag
            st.session_state.balances["Bank A"]["Assets"]["Reserve bei ZB A"] -= betrag

            st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank A"] -= betrag
            st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank B"] += betrag

            st.session_state.highlights = ["Bankguthaben bei A", "Einlage UK", "Reserve Bank B"]
            st.session_state.logs.append("🏦 Bank A bucht ab, ZB leitet Reserven an Bank B weiter.")

        elif schritt == 3:
            # Schritt 3: Gutschrift bei UI (Bank B)
            st.session_state.balances["Bank B"]["Assets"]["Reserve bei ZB B"] += betrag
            st.session_state.balances["Bank B"]["Liabilities"]["Einlage UI"] += betrag
            st.session_state.balances["UI"]["Assets"]["Bankguthaben bei B"] += betrag

            # Da UI etwas verkauft, ist der Erlös (Umsatz) gewinnwirksam
            # (In der einfachsten Form steigt das EK, später mindert der Warenabgang das EK wieder)

            st.session_state.highlights = ["Bankguthaben bei B", "Einlage UI", "Reserve bei ZB B"]
            st.session_state.logs.append("✅ UI hat die Zahlung erhalten.")

        elif schritt == 4:
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

            st.session_state.highlights = ["Sachvermögen UI", "Sachvermögen UK"]
            st.session_state.logs.append(f"📦 Investitionsgüter ({betrag}€) von UI an UK übertragen.")

        return True
    except Exception as e:
        st.error(f"Fehler beim Kauf: {e}")
        st.session_state.pending_steps = []
        return False


def kauf_konsum_prozess(betrag, schritt,r,vk):
    try:
        if schritt == 1:
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

            # Interbanken-Refinanzierung (Bank C braucht Reserven)
            st.session_state.balances["Zentralbank"]["Assets"]["Forderung Bank C"] += betrag
            st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank C"] += betrag
            st.session_state.balances["Bank C"]["Assets"]["Reserve bei ZB C"] += betrag
            st.session_state.balances["Bank C"]["Liabilities"]["Kredit bei ZB C"] += betrag

            st.session_state.highlights = ["Reserve bei ZB C", "Reserve Bank C","Kredit bei ZB C","Forderung Bank C"]
            st.session_state.logs.append("🏛️ Bank C besorgt sich Reserven für den Konsum.")

        elif schritt == 2:
            # Abbuchung Beschäftigte & ZB-Transfer zu Bank A
            st.session_state.balances["Beschäftigte"]["Assets"]["Bankguthaben bei C"] -= betrag
            st.session_state.balances["Bank C"]["Liabilities"]["Einlage Beschäftigte"] -= betrag
            st.session_state.balances["Bank C"]["Assets"]["Reserve bei ZB C"] -= betrag

            st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank C"] -= betrag
            st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank A"] += betrag

            st.session_state.highlights = ["Bankguthaben bei C", "Reserve Bank A","Reserve Bank C","Einlage Beschäftigte","Reserve bei ZB C"]
            st.session_state.logs.append("🏦 Geld fließt von Bank C zu Bank A.")

        elif schritt == 3:
            # Gutschrift bei UK
            st.session_state.balances["Bank A"]["Assets"]["Reserve bei ZB A"] += betrag
            st.session_state.balances["Bank A"]["Liabilities"]["Einlage UK"] += betrag
            st.session_state.balances["UK"]["Assets"]["Bankguthaben bei A"] += betrag

            st.session_state.highlights = ["Bankguthaben bei A", "Einlage UK","Reserve bei ZB A"]
            st.session_state.logs.append("💰 UK verbucht Verkaufserlös.")

        elif schritt == 4:
            # Warenübergabe
            st.session_state.value_balances["UK"]["Warenbestand"] -= betrag
            st.session_state.balances["UK"]["Assets"]["Warenbestand UK"] -= betrag
            st.session_state.balances["Beschäftigte"]["Assets"]["Gebrauchsvermögen B"] += betrag
            st.session_state.value_balances["Beschäftigte"]["Gebrauchsvermögen B"] += betrag

            st.session_state.highlights = ["Warenbestand UK", "Gebrauchsvermögen B"]
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
        # --- FALL 1: UNTERNEHMEN (Bleibt wie gehabt) ---
        if typ in ["UK", "UI"]:
            bank_id = "A" if typ == "UK" else "B"
            bank_name = f"Bank {bank_id}"
            if schritt == 1:
                if st.session_state.balances[typ]["Assets"][f"Bankguthaben bei {bank_id}"] < betrag:
                    st.session_state.logs.append(f"⚠️ {typ} hat nicht genug Guthaben!")
                    st.session_state.pending_steps = []
                    return False
                st.session_state.balances[typ]["Assets"][f"Bankguthaben bei {bank_id}"] -= betrag
                st.session_state.balances[typ]["Liabilities"][f"Eigenkapital {typ}"] -= betrag
                st.session_state.highlights = [f"Bankguthaben bei {bank_id}", f"Eigenkapital {typ}"]
            elif schritt == 2:
                st.session_state.balances[bank_name]["Liabilities"][f"Einlage {typ}"] -= betrag
                st.session_state.balances[bank_name]["Liabilities"][f"Einlage Unternehmer {typ}"] += betrag
                st.session_state.balances["Eigentümer"]["Assets"][f"Guthaben bei {bank_id}"] += betrag
                st.session_state.balances["Eigentümer"]["Liabilities"][f"Eigenk. Eigentümer {typ}"] += betrag

                st.session_state.highlights = [f"Guthaben bei {bank_id}",f"Einlage Unternehmer {typ}",f"Einlage {typ}"
                    ,f"Eigenk. Eigentümer {typ}"]

        # --- FALL 2: BANKEN A & B (Überweisung an Bank C) ---
        elif typ in ["Bank A", "Bank B"]:
            bank_id = typ.split()[-1]  # "A" oder "B"
            ek_name = f"Eigenkapital {bank_id}"

            if schritt == 1:
                if st.session_state.balances[typ]["Liabilities"][ek_name] < betrag:
                    st.session_state.logs.append(f"⚠️ {typ} hat zu wenig EK!")
                    st.session_state.pending_steps = []
                    return False

                # Bank A/B mindert EK und besorgt sich ZB-Reserven für den Transfer zu Bank C
                st.session_state.balances[typ]["Liabilities"][ek_name] -= betrag
                st.session_state.balances["Zentralbank"]["Assets"][f"Forderung {typ}"] += betrag
                st.session_state.balances["Zentralbank"]["Liabilities"][f"Reserve {typ}"] += betrag
                st.session_state.balances[typ]["Assets"][f"Reserve bei ZB {bank_id}"] += betrag
                st.session_state.balances[typ]["Liabilities"][f"Kredit bei ZB {bank_id}"] += betrag

                st.session_state.highlights = [ek_name, f"Reserve bei ZB {bank_id}",f"Forderung {typ}",f"Reserve bei ZB {bank_id}",f"Kredit bei ZB {bank_id}"]
                st.session_state.logs.append(f"🏛️ {typ} deklariert Dividende und besorgt Reserven.")

            elif schritt == 2:
                # Transfer der Reserven von Bank A/B zu Bank C bei der ZB
                st.session_state.balances[typ]["Assets"][f"Reserve bei ZB {bank_id}"] -= betrag
                st.session_state.balances["Zentralbank"]["Liabilities"][f"Reserve {typ}"] -= betrag
                st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank C"] += betrag

                # Gutschrift bei Bank C für den Bankbesitzer
                st.session_state.balances["Bank C"]["Assets"]["Reserve bei ZB C"] += betrag
                st.session_state.balances["Bank C"]["Liabilities"]["Einlage Bankbesitzer"] += betrag

                # Update Eigentümer
                st.session_state.balances["Eigentümer"]["Assets"]["Guthaben bei C"] += betrag
                st.session_state.balances["Eigentümer"]["Liabilities"]["Eigenk. Bankenbesitzer"] += betrag

                st.session_state.highlights = ["Reserve Bank C", "Einlage Bankbesitzer", "Guthaben bei C","Eigenk. Bankenbesitzer","Reserve Bank C",f"Reserve {typ}",f"Reserve bei ZB {bank_id}"]
                st.session_state.logs.append(f"💸 Dividende von {typ} floss über die ZB an den Besitzer bei Bank C.")

        # --- FALL 3: BANK C (Interne Ausschüttung) ---
        elif typ == "Bank C":
            if schritt == 1:
                if st.session_state.balances["Bank C"]["Liabilities"]["Eigenkapital C"] < betrag:
                    st.session_state.logs.append("⚠️ Bank C hat zu wenig EK!")
                    st.session_state.pending_steps = []
                    return False

                # Interner Passivtausch: EK C -> Einlage Bankbesitzer
                st.session_state.balances["Bank C"]["Liabilities"]["Eigenkapital C"] -= betrag
                st.session_state.balances["Bank C"]["Liabilities"]["Einlage Bankbesitzer"] += betrag

                st.session_state.balances["Eigentümer"]["Assets"]["Guthaben bei C"] += betrag
                st.session_state.balances["Eigentümer"]["Liabilities"]["Eigenk. Bankenbesitzer"] += betrag

                st.session_state.highlights = ["Eigenkapital C", "Einlage Bankbesitzer", "Guthaben bei C","Eigenk. Bankenbesitzer"]
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

        if schritt == 1:
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

            if von_bank_id != "A":
                st.session_state.balances["Zentralbank"]["Assets"][f"Forderung {bank_name_von}"] += betrag
                st.session_state.balances["Zentralbank"]["Liabilities"][f"Reserve {bank_name_von}"] += betrag
                st.session_state.balances[bank_name_von]["Assets"][f"Reserve bei ZB {von_bank_id}"] += betrag
                st.session_state.balances[bank_name_von]["Liabilities"][f"Kredit bei ZB {von_bank_id}"] += betrag
                st.session_state.highlights = [f"Reserve bei ZB {von_bank_id}", f"Forderung {bank_name_von}"]
                st.session_state.logs.append(f"🏛️ ZB stellt {bank_name_von} Reserven bereit.")
            else:
                st.session_state.logs.append(f"🛒 Interner Kauf: Eigentümer zahlt innerhalb von Bank A.")

        elif schritt == 2:
            st.session_state.balances["Eigentümer"]["Assets"][f"Guthaben bei {von_bank_id}"] -= betrag
            st.session_state.balances[bank_name_von]["Liabilities"][einlage_key_bank] -= betrag

            if von_bank_id != "A":
                st.session_state.balances[bank_name_von]["Assets"][f"Reserve bei ZB {von_bank_id}"] -= betrag
                st.session_state.balances["Zentralbank"]["Liabilities"][f"Reserve {bank_name_von}"] -= betrag
                st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank A"] += betrag
                st.session_state.highlights = ["Reserve Bank A", einlage_key_bank]
                st.session_state.logs.append(f"🏦 Reserven fließen von {bank_name_von} zu Bank A.")
            else:
                st.session_state.highlights = [einlage_key_bank]

        elif schritt == 3:
            # --- DER FIX: Reserven nur erhöhen, wenn sie von einer ANDEREN Bank kommen ---
            if von_bank_id != "A":
                st.session_state.balances["Bank A"]["Assets"]["Reserve bei ZB A"] += betrag
                st.session_state.highlights = ["Bankguthaben bei A", "Einlage UK", "Reserve bei ZB A"]
            else:
                # Interner Transfer: Keine ZB-Reserven involviert!
                st.session_state.highlights = ["Bankguthaben bei A", "Einlage UK"]

            st.session_state.balances["Bank A"]["Liabilities"]["Einlage UK"] += betrag
            st.session_state.balances["UK"]["Assets"]["Bankguthaben bei A"] += betrag
            st.session_state.logs.append("💰 UK erhält Verkaufserlös bei Bank A.")

        elif schritt == 4:
            st.session_state.value_balances["UK"]["Warenbestand"] -= betrag
            st.session_state.balances["UK"]["Assets"]["Warenbestand UK"] -= betrag
            st.session_state.balances["Eigentümer"]["Assets"]["Gebrauchsvermögen E"] += betrag

            # Hier vorsicht mit dem Key-Namen in value_balances:
            if "Gebrauchsvermögen E" in st.session_state.value_balances["Eigentümer"]:
                st.session_state.value_balances["Eigentümer"]["Gebrauchsvermögen E"] += betrag

            st.session_state.highlights = ["Warenbestand UK", "Gebrauchsvermögen E"]
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
            st.session_state.highlights += [reserve_key, kredit_key, zb_forderung_key, zb_reserve_key]

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
    """Schritt 1 -3: Bank leiht sich Reserven bei der ZB"""
    b_id = bank_name.split()[-1]  # "A" oder "B"

    try:
        if schritt == 1:
            st.session_state.highlights_action = []
            st.session_state.highlights_plan = [f"Forderung {bank_name}", f"Kredit bei ZB {b_id}",f"Reserve bei ZB {b_id}", f"Reserve {bank_name}"]
        elif schritt == 2:
            # ZB Forderung hoch, Bank Verbindlichkeit hoch
            st.session_state.balances["Zentralbank"]["Assets"][f"Forderung {bank_name}"] += betrag
            st.session_state.balances[bank_name]["Liabilities"][f"Kredit bei ZB {b_id}"] += betrag
            st.session_state.highlights_action = [f"Forderung {bank_name}", f"Kredit bei ZB {b_id}"]
            st.session_state.logs.append(f"🏛️ {bank_name} nimmt ZB-Kredit auf (+{betrag}).")

        elif schritt == 3:
            # ZB schreibt Reserven gut
            st.session_state.balances[bank_name]["Assets"][f"Reserve bei ZB {b_id}"] += betrag
            st.session_state.balances["Zentralbank"]["Liabilities"][f"Reserve {bank_name}"] += betrag
            st.session_state.highlights_action = [f"Reserve bei ZB {b_id}", f"Reserve {bank_name}"]
        elif schritt == 4:
            st.session_state.highlights_plan = []
            st.session_state.logs.append(f"💰 Reserven wurden {bank_name} gutgeschrieben.")
    except KeyError as e:
        st.error(f"Fehler: Das Konto {e} wurde nicht gefunden! Überprüfe die Initialisierung.")
        st.session_state.pending_steps = []



def interbank_transfer(betrag, sender, empfaenger, bank_sender, bank_empfaenger, speed, schritt):
    """Schritt 3 bis 7: Der eigentliche Transfer"""
    s_id = bank_sender.split()[-1]
    e_id = bank_empfaenger.split()[-1]
    s_num = sender.split()[-1]
    e_num = empfaenger.split()[-1]

    try:
        # Prüfung nur im ersten Schritt des Transfers
        if schritt == 1:
            guthaben = st.session_state.balances[sender]["Assets"][f"Bankguthaben bei {s_id}"]
            reserven = st.session_state.balances[bank_sender]["Assets"][f"Reserve bei ZB {s_id}"]

            if betrag > guthaben:
                st.session_state.logs.append(f"⚠️ {sender} hat zu wenig Guthaben!")
                st.session_state.pending_steps = []
                return False
            if betrag > reserven:
                st.session_state.logs.append(f"⚠️ {bank_sender} hat zu wenig Reserven für den Transfer!")
                st.session_state.pending_steps = []
                return False

        # Logik-Mapping: Schritt 1 hier entspricht deinem alten Schritt 3 usw.
        if schritt == 1:  # Abbuchung Sender
            st.session_state.highlights_plan = [f"Bankguthaben bei {s_id}", f"Einlage {sender}",f"Reserve {bank_sender}", f"Reserve bei ZB {s_id}"
                                                ,f"Reserve {bank_empfaenger}", f"Reserve bei ZB {e_id}",f"Bankguthaben bei {e_id}", f"Einlage {empfaenger}"
                                                ,f"Sachvermögen {s_num}", f"Sachvermögen {e_num}"]
        elif schritt == 2:
            st.session_state.balances[sender]["Assets"][f"Bankguthaben bei {s_id}"] -= betrag
            st.session_state.balances[bank_sender]["Liabilities"][f"Einlage {sender}"] -= betrag
            st.session_state.highlights_action = [f"Bankguthaben bei {s_id}", f"Einlage {sender}"]
            st.session_state.logs.append(f"🏦 {bank_sender} bucht bei {sender} ab.")

        elif schritt == 3:  # Reserven bei Sender-Bank weg
            st.session_state.balances[bank_sender]["Assets"][f"Reserve bei ZB {s_id}"] -= betrag
            st.session_state.balances["Zentralbank"]["Liabilities"][f"Reserve {bank_sender}"] -= betrag
            st.session_state.highlights_action = [f"Reserve {bank_sender}", f"Reserve bei ZB {s_id}"]

        elif schritt == 4:  # Reserven bei Empfänger-Bank dazu
            st.session_state.balances["Zentralbank"]["Liabilities"][f"Reserve {bank_empfaenger}"] += betrag
            st.session_state.balances[bank_empfaenger]["Assets"][f"Reserve bei ZB {e_id}"] += betrag
            st.session_state.highlights_action = [f"Reserve {bank_empfaenger}", f"Reserve bei ZB {e_id}"]
            st.session_state.logs.append(f"🏦 ZB schichtet Reserven zu {bank_empfaenger} um.")

        elif schritt == 5:  # Gutschrift Empfänger
            st.session_state.balances[bank_empfaenger]["Liabilities"][f"Einlage {empfaenger}"] += betrag
            st.session_state.balances[empfaenger]["Assets"][f"Bankguthaben bei {e_id}"] += betrag
            st.session_state.highlights_action = [f"Bankguthaben bei {e_id}", f"Einlage {empfaenger}"]
            st.session_state.logs.append(f"✅ {empfaenger} erhält Gutschrift.")

        elif schritt == 6:  # Waren/Sachwert
            st.session_state.balances[empfaenger]["Assets"][f"Sachvermögen {e_num}"] -= betrag
            st.session_state.balances[sender]["Assets"][f"Sachvermögen {s_num}"] += betrag
            st.session_state.highlights_action = [f"Sachvermögen {s_num}", f"Sachvermögen {e_num}"]
        elif schritt == 7:
            st.session_state.highlights_plan = []
            st.session_state.logs.append(f"📦 Sachvermögen übertragen.")


    except KeyError as e:
        st.error(f"Fehler: Das Konto {e} wurde nicht gefunden! Überprüfe die Initialisierung.")
        st.session_state.pending_steps = []


def prozess_kredit_intro(betrag, interest_rate, firma, bank, speed, schritt):
    # Extrahiert das "A" oder "B" aus "Bank A"
    bank_buchstabe = bank.split()[-1]

    # Extrahiert die "1" oder "2" aus "Kunde 1"
    # Falls es "Kunde 1" ist, wird kunde_id zu "1"
    kunde_id = firma.split()[-1] if "Kunde" in firma else firma

    # --- DYNAMISCHE KONTENNAMEN ---
    asset_firma = f"Bankguthaben bei {bank_buchstabe}"
    liab_firma = f"Kredit bei {bank_buchstabe}"

    # In deiner Intro-Bilanz heißen die Konten "Kredite Kunde 1" und "Einlage Kunde 1"
    asset_bank = f"Kredite {firma}"
    liab_bank = f"Einlage {firma}"

    # In deiner Intro-Bilanz heißt es "Eigenkapital 1" oder "Eigenkapital 2"
    ek_name_firma = f"Eigenkapital {kunde_id}"
    ek_name_bank = f"Eigenkapital {bank_buchstabe}"

    try:
        # --- FALL A: KREDITAUFNAHME (GELDSCHÖPFUNG) ---
        if betrag > 0:
            if schritt == 1:
                st.session_state.highlights_plan = [asset_firma, liab_bank,asset_bank, liab_firma]
            elif schritt == 2:
                # Buchung bei der Firma (Aktiva hoch, Passiva bei Bank hoch)
                st.session_state.balances[firma]["Assets"][asset_firma] += betrag
                st.session_state.balances[bank]["Liabilities"][liab_bank] += betrag
                st.session_state.highlights_action = [asset_firma, liab_bank]
                st.session_state.logs.append(f"🏦 {bank}: Schöpft Giralgeld für {firma}.")

            elif schritt == 3:
                # Buchung bei der Bank (Forderung hoch, Verbindlichkeit Firma hoch)
                st.session_state.balances[bank]["Assets"][asset_bank] += betrag
                st.session_state.balances[firma]["Liabilities"][liab_firma] += betrag
                st.session_state.highlights_action = [asset_bank, liab_firma]

            elif schritt ==4:
                st.session_state.highlights_plan = []
                st.session_state.logs.append(f"📝 {firma}: Kreditvertrag über {betrag}€ unterzeichnet.")

        # --- FALL B: TILGUNG & ZINSEN ---
        elif betrag < 0:
            kredit_anteil = abs(betrag)
            zins_anteil = round(kredit_anteil * interest_rate, 2)
            gesamt_abfluss = kredit_anteil + zins_anteil

            if schritt == 1:
                st.session_state.highlights_plan = [asset_firma, liab_bank,asset_bank, liab_firma,ek_name_firma,ek_name_bank]

            if schritt == 2:
                # 1. Bankguthaben sinkt um Tilgung + Zins
                st.session_state.balances[firma]["Assets"][asset_firma] -= gesamt_abfluss

                # 2. Die Kredit-Schuld sinkt NUR um den Tilgungsanteil
                st.session_state.balances[firma]["Liabilities"][liab_firma] -= kredit_anteil

                # 3. Der Zinsanteil wird vom Eigenkapital abgezogen
                # Wir nutzen hier ek_name_firma (z.B. "Eigenkapital 1")
                st.session_state.balances[firma]["Liabilities"][ek_name_firma] -= zins_anteil

                # Highlights für die Bilanz setzen
                st.session_state.highlights_action = [asset_firma, liab_firma, ek_name_firma]
                st.session_state.logs.append(f"📉 {firma}: Zahlt {kredit_anteil}€ Tilgung und {zins_anteil}€ Zinsen.")
            elif schritt == 3:
                # Bank erhält: Kredit-Forderung weg, Einlagen-Verbindlichkeit weg, EK steigt (Zinsertrag)
                st.session_state.balances[bank]["Assets"][asset_bank] -= kredit_anteil
                st.session_state.balances[bank]["Liabilities"][liab_bank] -= gesamt_abfluss

                if ek_name_bank in st.session_state.balances[bank]["Liabilities"]:
                    st.session_state.balances[bank]["Liabilities"][ek_name_bank] += zins_anteil

                st.session_state.highlights_action = [asset_bank, liab_bank,ek_name_bank]
            elif schritt == 4:
                st.session_state.highlights_plan = []
                st.session_state.logs.append(f"🏛️ {bank}: Zinsertrag verbucht und Geldmenge reduziert.")

        return True

    except KeyError as e:
        st.error(f"Konto-Fehler im Intro: {e} nicht gefunden. Prüfe die Namen in der Initialisierung!")
        st.session_state.pending_steps = []
        return False

"""Staatsfinanzierung"""
def staat_prozess(aktion, betrag, schritt):
    try:
        if aktion == "Kredit ZB":
            if schritt == 1:
                st.session_state.balances["Bank A"]["Liabilities"]["Kredit bei ZB"] += betrag
                st.session_state.balances["Zentralbank"]["Assets"]["Forderung Bank A"] += betrag
                st.session_state.highlights = ["Kredit bei ZB", "Forderung Bank A"]
                st.session_state.logs.append(f"Kredit: {betrag}€ Kredit erzeugt.")
            if schritt == 2:
                st.session_state.balances["Bank A"]["Assets"]["Reserve bei ZB"] += betrag
                st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank A"] += betrag
                st.session_state.highlights = ["Reserve Bank A", "Reserve bei ZB"]
                st.session_state.logs.append(f"Kredit: {betrag}€ Reserve erzeugt.")
        elif aktion == "erzeugen":
            st.session_state.balances["Staat"]["Assets"]["Anleihen Eigenbestand"] += betrag
            st.session_state.balances["Staat"]["Liabilities"]["Staatsanleihen (Gesamt)"] += betrag
            st.session_state.highlights = ["Anleihen Eigenbestand", "Staatsanleihen (Gesamt)"]
            st.session_state.logs.append(f"📜 Staat: {betrag}€ Anleihen im Eigenbestand erzeugt.")

        elif aktion == "verkaufen":
            if schritt == 1:
                st.session_state.balances["Bank A"]["Assets"]["Reserve bei ZB"] -= betrag
                st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank A"] -= betrag
                st.session_state.highlights = ["Reserve bei ZB", "Reserve Bank A"]
                st.session_state.logs.append(f"🏛️ Verkauf Schritt 1: Bank zahlt Geld.")
            elif schritt == 2:
                st.session_state.balances["Zentralbank"]["Liabilities"]["Guthaben Staat"] += betrag
                st.session_state.balances["Staat"]["Assets"]["Guthaben bei ZB"] += betrag
                st.session_state.highlights = ["Guthaben Staat","Guthaben bei ZB"]
                st.session_state.logs.append(f"🏛️ Verkauf Schritt 2: Zentralbank tauscht Reserven.")
            elif schritt == 3:
                st.session_state.balances["Staat"]["Assets"]["Anleihen Eigenbestand"] -= betrag
                st.session_state.balances["Bank A"]["Assets"]["Staatsanleihen"] += betrag
                st.session_state.highlights = ["Anleihen Eigenbestand", "Staatsanleihen"]
                st.session_state.logs.append(f"🏛️ Verkauf Schritt 3: Staat verkauft die Anleihe.")

        elif aktion == "lohn":
            if schritt == 1:
                st.session_state.balances["Staat"]["Assets"]["Guthaben bei ZB"] -= betrag
                st.session_state.balances["Staat"]["Liabilities"]["Eigenkapital Staat"] -= betrag
                st.session_state.balances["Zentralbank"]["Liabilities"]["Guthaben Staat"] -= betrag
                st.session_state.highlights = ["Guthaben bei ZB", "Eigenkapital Staat", "Guthaben Staat"]
                st.session_state.logs.append(f"💸 Lohn Schritt 1: Staat weist ZB zur Zahlung an.")
            elif schritt == 2:
                st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank A"] += betrag
                st.session_state.balances["Bank A"]["Assets"]["Reserve bei ZB"] += betrag
                st.session_state.highlights = ["Reserve bei ZB","Reserve Bank A"]
                st.session_state.logs.append(f"💸 Lohn Schritt 2: Zentralbank tauscht Reserven.")

            elif schritt == 3:
                st.session_state.balances["Bank A"]["Liabilities"]["Einlage Bürger"] += betrag
                st.session_state.balances["Bürger"]["Assets"]["Bankguthaben"] += betrag
                st.session_state.balances["Bürger"]["Liabilities"]["Eigenkapital Bürger"] += betrag
                st.session_state.highlights = ["Bankguthaben", "Einlage Bürger", "Eigenkapital Bürger"]
                st.session_state.logs.append(f"💸 Lohn Schritt 3: Bürger erhält Giralgeld.")

        elif aktion == "steuern":
            if schritt == 1:
                st.session_state.balances["Bank A"]["Liabilities"]["Einlage Bürger"] -= betrag
                st.session_state.balances["Bürger"]["Assets"]["Bankguthaben"] -= betrag
                st.session_state.balances["Bürger"]["Liabilities"]["Eigenkapital Bürger"] -= betrag
                st.session_state.highlights = ["Bankguthaben", "Einlage Bürger", "Eigenkapital Bürger"]
                st.session_state.logs.append(f"💸 Steuern Schritt 1: Bürger zahlt Steuern.")
            elif schritt == 2:
                st.session_state.balances["Zentralbank"]["Liabilities"]["Reserve Bank A"] -= betrag
                st.session_state.balances["Bank A"]["Assets"]["Reserve bei ZB"] -= betrag
                st.session_state.highlights = ["Reserve bei ZB", "Reserve Bank A"]
                st.session_state.logs.append(f"💸 Steuern Schritt 2: Zentralbank tauscht Reserven.")

            elif schritt == 3:
                st.session_state.balances["Staat"]["Assets"]["Guthaben bei ZB"] += betrag
                st.session_state.balances["Staat"]["Liabilities"]["Eigenkapital Staat"] += betrag
                st.session_state.balances["Zentralbank"]["Liabilities"]["Guthaben Staat"] += betrag
                st.session_state.highlights = ["Guthaben bei ZB", "Eigenkapital Staat", "Guthaben Staat"]
                st.session_state.logs.append(f"💸 Steuern Schritt 3: Staat erhält Reserven.")
        return True
    except Exception as e:
        st.error(f"Fehler: {e}")
        return False

