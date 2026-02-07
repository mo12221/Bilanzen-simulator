# Game_play.py

def get_mission(round_number):
    missions = {
        1: {
            "title": "Runde 1: Ohne Zins",
            "task": "UI: Stelle Beschäftigte für 1000€ ein. UK: Stelle Beschäftigte für 500€ ein und kaufe Maschienen für 2000€!",
            "required_actions": ["kredit_uk", "lohn_uk"]
        },
        2: {
            "title": "Runde 2: Mit Zins",
            "task": "Gleiches Spiel, doch stelle nun den Zins auf 5%!",
            "required_actions": ["kredit_ui", "lohn_ui"]
        },
        3: {
            "title": "Runde 3: Konsolidierung",
            "task": "Zahle einen Teil des Kredits von UK zurück (-5.000€).",
            "required_actions": ["kredit_uk"]
        }
    }
    return missions.get(round_number, {"title": "Freies Spiel", "task": "Handle nach eigenem Ermessen.", "required_actions": []})