import json
from pathlib import Path
import xml.etree.ElementTree as ET

def build_incipit_index(tei_folder, output_folder):
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    ET.register_namespace('', 'http://www.tei-c.org/ns/1.0')

    out_path = Path(output_folder)
    out_path.mkdir(parents=True, exist_ok=True)

    incipit_index = []
    input_path = Path(tei_folder)
    files = list(input_path.glob("*.xml"))

    print(f"📦 Generazione indice degli incipit da {len(files)} file XML-TEI...")

    for f_path in files:
        file_id = f_path.stem
        html_filename = f"{file_id}.html"

        try:
            root = ET.parse(str(f_path)).getroot()
        except Exception as e:
            print(f"❌ Errore con {f_path.name}: {e}")
            continue

        titulus = root.find(".//tei:titleStmt/tei:title", ns)
        auctor = root.find(".//tei:titleStmt/tei:author", ns)
        metrum = root.find(".//tei:notesStmt/tei:note[@type='metrum']", ns)
        fons = root.find(".//tei:sourceDesc//tei:title", ns)
        annus = root.find(".//tei:sourceDesc//tei:date", ns)

        titulus_txt = titulus.text.strip() if titulus is not None else "Untitled"
        auctor_txt = auctor.text.strip() if auctor is not None else "Anonymus"
        metrum_txt = metrum.text.replace("Metrum: ", "").strip() if metrum is not None else "Unknown"
        fons_txt = fons.text.strip() if fons is not None else "Unknown"
        annus_txt = annus.text.strip() if annus is not None else ""

        incipit_clean = titulus_txt.rstrip(',.;:') 

        incipit_index.append({
            "incipit": incipit_clean,
            "file": html_filename,
            "auctor": auctor_txt,
            "metrum": metrum_txt,
            "fons": fons_txt,
            "annus": annus_txt
        })

    output_file = "01_incipit_index.json"

    with open(out_path / output_file, 'w', encoding='utf-8') as jf:
        json.dump(incipit_index, jf, ensure_ascii=False, indent=2)

    print(f"✅ File '{output_file}' creato in {output_folder}.")

if __name__ == "__main__":
    build_incipit_index("output_TEI", "output_HTML")
