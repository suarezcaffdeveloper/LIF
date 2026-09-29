"""Genera las imágenes de un diseño para la landing, con la liga demo.

Uso, desde la raíz del proyecto:

    venv\\Scripts\\python.exe landing\\herramientas\\capturar_diseno.py cuaderno

Crea en landing/assets/img/:
  var-<diseno>-original.webp y var-<diseno>-<color>.webp (los seis colores del selector, 1200x750)
  <diseno>-m-home.webp (celular, 780x1688)

No toca ninguna base de datos real: siembra una SQLite temporal con la liga ficticia, levanta la
demo en un puerto local, saca las capturas con Chrome y lo apaga todo al terminar.
Requiere Google Chrome instalado y Pillow (ya está en requirements.txt).
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "landing" / "assets" / "img"
PUERTO = 5056
BASE = f"http://127.0.0.1:{PUERTO}"
COLORES = {"original": "", "naranja": "e2731f", "violeta": "6b54d6", "rojo": "d42e5b", "turquesa": "0e8f8f", "azul": "3d6bff"}
CANDIDATOS_CHROME = [
    os.environ.get("CHROME", ""),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def buscar_chrome():
    for ruta in CANDIDATOS_CHROME:
        if ruta and Path(ruta).exists():
            return ruta
    sys.exit("No encontré Google Chrome. Definí la variable de entorno CHROME con la ruta del ejecutable.")


def capturar(chrome, destino, ruta, ancho, alto, escala=1, en_marco=False):
    """Captura `ruta` de la demo. Con en_marco=True la carga dentro de un marco del ancho pedido
    (Chrome headless no baja de ~500 px de ancho, así se consigue un celular real de 390 px)."""
    tmp = Path(destino).with_suffix(".html")
    if en_marco:
        tmp.write_text(
            f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;overflow:hidden}}'
            f'iframe{{border:0;width:{ancho}px;height:{alto}px;display:block}}</style><iframe src="{BASE}{ruta}"></iframe>',
            encoding="utf-8",
        )
        url = tmp.as_uri()
    else:
        url = BASE + ruta
    subprocess.run(
        [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-prefers-reduced-motion",
         f"--window-size={max(ancho, 500)},{alto}", f"--force-device-scale-factor={escala}",
         "--virtual-time-budget=9000", f"--screenshot={destino}", url],
        capture_output=True, timeout=180, check=True,
    )
    tmp.unlink(missing_ok=True)
    return Image.open(destino).convert("RGB").crop((0, 0, ancho * escala, alto * escala))


def main():
    if len(sys.argv) != 2:
        sys.exit("Uso: capturar_diseno.py <diseno>   (por ejemplo: cuaderno)")
    diseno = sys.argv[1].strip().lower()
    if not (RAIZ / "app" / "themes" / diseno / "templates").is_dir():
        sys.exit(f"No existe el diseño {diseno!r} en app/themes/.")
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
        print("Levantando la demo…")
        servidor = subprocess.Popen(
            [sys.executable, "-c", f"from app import app; app.run(port={PUERTO}, debug=False)"],
            cwd=RAIZ, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        for _ in range(40):
            try:
                urllib.request.urlopen(f"{BASE}/?tema={diseno}&embed=1", timeout=2)
                break
            except Exception:
                time.sleep(0.5)
        else:
            sys.exit("La demo no respondió a tiempo.")

        SALIDA.mkdir(parents=True, exist_ok=True)
        for nombre, hexa in COLORES.items():
            ruta = f"/?tema={diseno}&embed=1" + (f"&marca={urllib.parse.quote('#' + hexa)}" if hexa else "")
            imagen = capturar(chrome, str(trabajo / "captura.png"), ruta, 1440, 900)
            imagen.resize((1200, 750), Image.LANCZOS).save(SALIDA / f"var-{diseno}-{nombre}.webp", quality=80, method=6)
            print(f"  var-{diseno}-{nombre}.webp")
        celu = capturar(chrome, str(trabajo / "celu.png"), f"/?tema={diseno}&embed=1", 390, 844, escala=2, en_marco=True)
        celu.save(SALIDA / f"{diseno}-m-home.webp", quality=82, method=6)
        print(f"  {diseno}-m-home.webp")
        print("Listo. Las imágenes quedaron en", SALIDA)
    finally:
        if servidor:
            servidor.terminate()
        shutil.rmtree(trabajo, ignore_errors=True)


if __name__ == "__main__":
    main()
