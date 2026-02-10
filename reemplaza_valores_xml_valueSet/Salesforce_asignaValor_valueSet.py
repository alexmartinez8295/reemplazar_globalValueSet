import xml.etree.ElementTree as ET
import argparse
import os
import csv
import json


# ---------------------------
# Cargar reemplazos
# ---------------------------
def load_replacements(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".csv":
        return load_from_csv(file_path)
    elif ext == ".json":
        return load_from_json(file_path)
    else:
        raise ValueError("Formato no soportado. Usa CSV o JSON")


def load_from_csv(file_path):
    replacements = {}
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "original" not in reader.fieldnames or "replacement" not in reader.fieldnames:
            raise ValueError("El CSV debe tener columnas: original,replacement")

        for row in reader:
            if row["original"] and row["replacement"]:
                replacements[row["original"].strip()] = row["replacement"].strip()

    return replacements


def load_from_json(file_path):
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("El JSON debe ser un objeto clave-valor")

    return {k.strip(): v.strip() for k, v in data.items()}


# ---------------------------
# Procesar XML
# ---------------------------
def process_xml(input_file, output_dir, replacements, dry_run=False):
    tree = ET.parse(input_file)
    root = tree.getroot()

    # Detectar namespace Salesforce
    ns = {}
    if root.tag.startswith("{"):
        uri = root.tag.split("}")[0].strip("{")
        ns["sf"] = uri

        # 👉 evita ns0 en la salida
        ET.register_namespace("", uri)

    replaced = 0
    not_found = 0

    values = root.findall("sf:customValue", ns)
    print(f"🔎 customValue encontrados: {len(values)}")

    for cv in values:
        label = cv.find("sf:fullName", ns)
        if label is None or not label.text:
            continue

        original = label.text.strip()

        if original in replacements:
            if not dry_run:
                label.text = replacements[original]
            replaced += 1
        else:
            not_found += 1

    print(f"✅ Reemplazados: {replaced}")
    print(f"⚠️ No encontrados: {not_found}")

    if dry_run:
        print("🧪 DRY-RUN activado: no se generó archivo")
        return

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(
        output_dir,
        os.path.basename(input_file).replace(".xml", "_converted.xml")
    )

    tree.write(output_file, encoding="UTF-8", xml_declaration=True)
    print(f"📄 Archivo generado: {output_file}")


# ---------------------------
# CLI
# ---------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reemplazo de labels en GlobalValueSet (Salesforce)"
    )
    parser.add_argument("xml", help="XML GlobalValueSet de entrada")
    parser.add_argument(
        "-r", "--replacements",
        required=True,
        help="Archivo CSV o JSON con reemplazos"
    )
    parser.add_argument(
        "--out",
        default="output",
        help="Directorio de salida"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula el reemplazo sin generar archivo"
    )

    args = parser.parse_args()

    replacements = load_replacements(args.replacements)
    print(f"📥 Reemplazos cargados: {len(replacements)}")

    process_xml(
        args.xml,
        args.out,
        replacements,
        dry_run=args.dry_run
    )
