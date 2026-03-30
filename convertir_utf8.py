import os
import chardet

# Ruta base de tu proyecto
BASE_DIR = r"C:\Users\The Oldone\Desktop\LIF"

def detect_encoding(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read()
        result = chardet.detect(raw)
        return result['encoding']

def convert_to_utf8(filepath, from_enc):
    try:
        with open(filepath, 'r', encoding=from_enc, errors='ignore') as f:
            content = f.read()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Convertido a UTF-8: {filepath}")
    except Exception as e:
        print(f"⚠️ Error al convertir {filepath}: {e}")

def main():
    extensiones = ('.py', '.txt', '.html', '.css', '.js', '.sql', '.md')
    for root, _, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(extensiones):
                full_path = os.path.join(root, file)
                enc = detect_encoding(full_path)
                if enc and enc.lower() != 'utf-8':
                    print(f"⚡ {full_path} está en {enc}, convirtiendo...")
                    convert_to_utf8(full_path, enc)

if __name__ == "__main__":
    main()
