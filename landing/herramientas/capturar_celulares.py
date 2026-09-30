"""Capturas de celular (390x844, x2) de páginas internas de la demo, para "Tres maneras de usar tu liga".

Uso, desde la raíz del proyecto:

    venv\Scripts\python.exe landing\herramientas\capturar_celulares.py

Crea en landing/assets/img/ <diseno>-m-<pagina>.webp. Misma mecánica que capturar_diseno.py
(SQLite temporal, demo en un puerto local, Chrome headless).
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

# (diseno, pagina, ruta)
PAGINAS = [
    ("cancha", "tabla", "/tabla_posiciones/Primera"),
    ("cancha", "fixture", "/fixture/mayores/Primera"),
    ("nocturno", "tabla", "/tabla_posiciones/Primera"),
    ("nocturno", "fixture", "/fixture/mayores/Primera"),
    ("tribuna", "tabla", "/tabla_posiciones/Primera"),
    ("tribuna", "fixture", "/fixture/mayores/Primera"),
    ("reflectores", "tabla", "/tabla_posiciones/Primera"),
    ("reflectores", "fixture", "/fixture/mayores/Primera"),
]


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
        subprocess.run([sys.executable, "-m", "flask", "--app", "app", "seed-liga-demo", "--yes"], cwd=RAIZ, env=env, check=True)
        servidor = subprocess.Popen(
            [sys.executable, "-c", f"from app import app; app.run(port={PUERTO}, debug=False)"],
            cwd=RAIZ, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        for _ in range(40):
            try:
                urllib.request.urlopen(f"{BASE}/", timeout=2)
                break
            except Exception:
                time.sleep(0.5)
        else:
            sys.exit("La demo no respondió a tiempo.")
        for diseno, pagina, ruta in PAGINAS:
            imagen = capturar(chrome, str(trabajo / "celu.png"), f"{ruta}?tema={diseno}&embed=1", 390, 844, escala=2, en_marco=True)
            imagen.save(SALIDA / f"{diseno}-m-{pagina}.webp", quality=82, method=6)
            print(f"  {diseno}-m-{pagina}.webp")
    finally:
        if servidor:
            servidor.terminate()
        shutil.rmtree(trabajo, ignore_errors=True)


if __name__ == "__main__":
    main()
