"""Genera las capturas de los paneles de administrador y periodista para la landing, con la liga demo.

Uso, desde la raíz del proyecto:

    venv\\Scripts\\python.exe landing\\herramientas\\capturar_admin.py

Crea en landing/assets/img/: admin-*.webp y periodista-*.webp (1440x900).
Igual que capturar_diseno.py: siembra una SQLite temporal, levanta la demo en un puerto local y
apaga todo al terminar. Para entrar con sesión usa una ruta auxiliar que existe solo en ese
servidor temporal (no forma parte de la app).
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capturar_diseno import BASE, PUERTO, RAIZ, SALIDA, buscar_chrome, capturar  # noqa: E402
from PIL import Image  # noqa: E402

# (archivo, ruta, cuenta)
PAGINAS = [
    ("admin-panel", "/adminview", "demo@eltablon.com"),
    ("admin-estadisticas", "/cargar_estadisticas_mayores", "demo@eltablon.com"),
    ("admin-fixture", "/cargar_fixture_mayores", "demo@eltablon.com"),
    ("admin-temporadas", "/admin/temporadas", "demo@eltablon.com"),
    ("admin-periodista", "/crear_periodista", "demo@eltablon.com"),
    ("periodista-panel", "/panel_periodista", "periodista@eltablon.com"),
    ("periodista-noticia", "/cargar_noticia", "periodista@eltablon.com"),
]

SERVIDOR = f"""
from flask import redirect, request
from flask_login import login_user
from app import app
from app.models.models import Usuario

@app.route('/__entrar')
def __entrar():
    login_user(Usuario.query.filter_by(email=request.args['email']).first())
    return redirect(request.args['a'])

app.run(port={PUERTO}, debug=False)
"""


def main():
    chrome = buscar_chrome()
    trabajo = Path(tempfile.mkdtemp(prefix="eltablon_capturas_"))
    env = dict(
        os.environ, LIGA="demo", DEMO_TEMAS="1", PYTHONIOENCODING="utf-8", PYTHONPATH=str(RAIZ),
        DATABASE_URL=f"sqlite:///{trabajo.as_posix()}/demo.db", DEMO_DATABASE_URL=f"sqlite:///{trabajo.as_posix()}/demo_sesion.db",
    )
    env.pop("TEMA", None)
    servidor = None
    try:
        print("Sembrando la liga demo en una base temporal…")
        subprocess.run([sys.executable, "-m", "flask", "--app", "app", "seed-liga-demo", "--yes"], cwd=RAIZ, env=env, check=True)
        servidor = subprocess.Popen([sys.executable, "-c", SERVIDOR], cwd=RAIZ, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(40):
            try:
                urllib.request.urlopen(f"{BASE}/", timeout=2)
                break
            except Exception:
                time.sleep(0.5)
        else:
            sys.exit("La demo no respondió a tiempo.")
        for nombre, ruta, email in PAGINAS:
            entrada = f"/__entrar?email={email}&a={ruta}"
            imagen = capturar(chrome, str(trabajo / "captura.png"), entrada, 1440, 900)
            imagen.save(SALIDA / f"{nombre}.webp", quality=82, method=6)
            print(f"  {nombre}.webp")
    finally:
        if servidor:
            servidor.terminate()
        shutil.rmtree(trabajo, ignore_errors=True)


if __name__ == "__main__":
    main()
