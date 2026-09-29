import requests
from datetime import datetime
from ..ligas import LIGA

def notificar_n8n(division):
    url_n8n = "https://suarezzsanti01.app.n8n.cloud/webhook-test/tabla_actualizada"
    try:
        requests.post(url_n8n, json={
            "division": division,
            "timestamp": datetime.utcnow().isoformat(),
            "url_tabla": f"{LIGA.url_publica}/tabla_posiciones/{division}"
        }, timeout=5)
        print(f"[n8n] Notificado OK — {division}")
    except Exception as e:
        print(f"[n8n] Error al notificar: {e}")