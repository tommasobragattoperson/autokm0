import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# Configurazione siti
SITES = {
    "Jolly Automobili": {"url": "https://www.gruppojollyautomobili.com/auto/km0/?orderField=enteredInStockDate&orderMode=desc", "type": "jolly"},
    "Leonori": {"url": "https://www.leonori.it/ricerca-auto-km-0/1?order=5", "type": "leonori"},
    "Romana Auto": {"url": "https://www.romana-auto.it/auto-km-0-roma/1?order=5", "type": "romana"}
}

LOG_FILE = "updates_log.json"

def fetch_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    logs = []
    
    # Carichiamo i vecchi log se esistono
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)

    # Dizionario per controllare l'ultimo ID visto per ogni sito
    last_ids = {log['site']: log['id'] for log in reversed(logs)}
    new_found = False

    for name, config in SITES.items():
        try:
            res = requests.get(config["url"], headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            car = None

            # --- LOGICA JOLLY ---
            if config["type"] == "jolly":
                script = soup.find('script', class_='yoast-schema-graph')
                if script:
                    graph = json.loads(script.string).get('@graph', [])
                    item_list = next((i for i in graph if i.get('@type') == 'ItemList'), None)
                    if item_list and item_list.get('itemListElement'):
                        c = item_list['itemListElement'][0]['item']
                        car = {
                            "id": str(c.get('sku')),
                            "model": c.get('name'),
                            "price": f"€ {c.get('offers',{}).get('price')}",
                            "link": c.get('url')
                        }

            # --- LOGICA LEONORI ---
            elif config["type"] == "leonori":
                el = soup.select_one('.contenitore-annunci .annuncio')
                if el:
                    link_tag = el.select_one('a.stretched-link')
                    car = {
                        "id": link_tag['href'].split('-')[-1],
                        "model": el.select_one('h3').text.strip(),
                        "price": el.select_one('.text-primary').text.strip(),
                        "link": "https://www.leonori.it" + link_tag['href']
                    }

            # --- LOGICA ROMANA AUTO ---
            elif config["type"] == "romana":
                el = soup.select_one('.dettagli')
                if el:
                    title = el.select_one('.title').text.strip()
                    link_tag = el.find_previous('a') or el.find_parent('a')
                    link = "https://www.romana-auto.it" + link_tag['href'] if link_tag else ""
                    car = {
                        "id": link.split('/')[-1] or title,
                        "model": title,
                        "price": el.select_one('.prezzofinale').text.strip(),
                        "link": link
                    }

            # Se abbiamo trovato un'auto e l'ID è diverso dall'ultimo salvato
            if car and (name not in last_ids or car["id"] != last_ids[name]):
                logs.insert(0, {
                    "timestamp": datetime.now().strftime("%d/%m %H:%M"),
                    "site": name,
                    "model": car["model"],
                    "price": car["price"],
                    "link": car["link"],
                    "id": car["id"]
                })
                new_found = True
        except Exception as e:
            print(f"Errore su {name}: {e}")

    # Salva solo se ci sono novità (per non riscrivere il file inutilmente)
    if new_found:
        logs = logs[:50] # Mantieni solo gli ultimi 50 log
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4)
    
    return logs

def generate_html(logs):
    # Genera la lista di div per le auto
    entries_html = ""
    for l in logs:
        entries_html += f"""
        <div style='margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 5px;'>
            <span style='color: #888;'>[{l['timestamp']}]</span> 
            <b style='color: #ff00ff;'>{l['site']}</b>: 
            <span style='color: #9cdcfe;'>{l['model']}</span> - 
            <b style='color: #ffff00;'>{l['price']}</b> 
            <a href='{l['link']}' target='_blank' style='color:white; font-size: 0.8em; margin-left:10px;'>[LINK]</a>
        </div>"""

    # Se non ci sono log, mostriamo un messaggio di sistema
    if not logs:
        entries_html = "<div>[SYSTEM] In attesa del primo aggiornamento...</div>"

    html_template = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <title>Monitor Auto KM0</title>
        <style>
            body {{ background: #0d0d0d; color: #00ff41; font-family: 'Courier New', monospace; padding: 20px; line-height: 1.4; }}
            h1 {{ border-bottom: 2px solid #00ff41; padding-bottom: 10px; font-size: 1.5em; }}
            .status {{ color: #888; font-size: 0.8em; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <h1>> SYSTEM_MONITOR_ACTIVE_</h1>
        <div class="status">Ultimo controllo: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</div>
        {entries_html}
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

# Esecuzione
logs = fetch_data()
generate_html(logs)
