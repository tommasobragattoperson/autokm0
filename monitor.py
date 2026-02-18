import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

SITES = {
    "Jolly Automobili": {"url": "https://www.gruppojollyautomobili.com/auto/km0/?orderField=enteredInStockDate&orderMode=desc", "type": "jolly"},
    "Leonori": {"url": "https://www.leonori.it/ricerca-auto-km-0/1?order=5", "type": "leonori"},
    "Romana Auto": {"url": "https://www.romana-auto.it/auto-km-0-roma/1?order=5", "type": "romana"}
}

def fetch_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    new_logs = []
    # Carichiamo i vecchi log se esistono
    if os.path.exists("updates_log.json"):
        with open("updates_log.json", "r") as f:
            new_logs = json.load(f)

    last_ids = {log['site']: log['id'] for log in reversed(new_logs)}

    for name, config in SITES.items():
        try:
            res = requests.get(config["url"], headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            car = None
            # ... (qui inserisci le logiche di estrazione get_jolly, get_leonori, get_romana che abbiamo scritto prima) ...
            
            # Esempio semplificato per brevità:
            if car and (name not in last_ids or car["id"] != last_ids[name]):
                new_logs.insert(0, {
                    "timestamp": datetime.now().strftime("%d/%m %H:%M"),
                    "site": name, "model": car["model"], "price": car["price"], "link": car["link"], "id": car["id"]
                })
        except: continue

    # Mantieni solo gli ultimi 50
    new_logs = new_logs[:50]
    with open("updates_log.json", "w") as f:
        json.dump(new_logs, f, indent=4)
    return new_logs

def generate_html(logs):
    html_template = f"""
    <html><head><style>body {{ background: #0d0d0d; color: #00ff41; font-family: monospace; padding: 20px; }}</style></head>
    <body><h1>SYSTEM MONITOR: ACTIVE</h1>
    {"".join([f"<div>[{l['timestamp']}] {l['site']}: {l['model']} - {l['price']} <a href='{l['link']}' style='color:white'>LINK</a></div>" for l in logs])}
    </body></html>
    """
    with open("index.html", "w") as f:
        f.write(html_template)

logs = fetch_data()
generate_html(logs)
