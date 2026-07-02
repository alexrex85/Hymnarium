import json
import unicodedata
from pathlib import Path
import xml.etree.ElementTree as ET

def normalize(text):
    """
    Normalizza una stringa:
    - minuscole
    - rimozione accenti/segni diacritici
    """
    text = unicodedata.normalize("NFD", text)
    text = "".join(
        c for c in text
        if unicodedata.category(c) != "Mn"
    )
    return text.lower().strip()

def build_search_index(tei_folder, output_folder):
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

    ET.register_namespace(
        '',
        'http://www.tei-c.org/ns/1.0'
    )

    out_path = Path(output_folder)
    out_path.mkdir(
        parents=True,
        exist_ok=True
    )

    search_index = []

    input_path = Path(tei_folder)
    files = sorted(
        input_path.glob("*.xml")
    )

    print(
        f"📦 Generazione indice analitico dei versi da {len(files)} file XML-TEI..."
    )

    for f_path in files:
        file_id = f_path.stem
        html_filename = f"{file_id}.html"

        try:
            root = ET.parse(
                str(f_path)
            ).getroot()
        except Exception as e:
            print(
                f"❌ Errore con {f_path.name}: {e}"
            )
            continue

        # --------------------------------------------------
        # METADATI DELL'INNO
        # --------------------------------------------------
        titulus = root.find(
            ".//tei:titleStmt/tei:title",
            ns
        )

        auctor = root.find(
            ".//tei:titleStmt/tei:author",
            ns
        )

        metrum = root.find(
            ".//tei:notesStmt/tei:note[@type='metrum']",
            ns
        )

        fons = root.find(
            ".//tei:sourceDesc//tei:title",
            ns
        )

        annus = root.find(
            ".//tei:sourceDesc//tei:date",
            ns
        )

        titulus_txt = (
            titulus.text.strip()
            if titulus is not None and titulus.text
            else "Untitled"
        )

        auctor_txt = (
            auctor.text.strip()
            if auctor is not None and auctor.text
            else "Anonymus"
        )

        metrum_txt = (
            metrum.text.replace(
                "Metrum: ",
                ""
            ).strip()
            if metrum is not None and metrum.text
            else "Unknown"
        )

        fons_txt = (
            fons.text.strip()
            if fons is not None and fons.text
            else "Unknown"
        )

        annus_txt = (
            annus.text.strip()
            if annus is not None and annus.text
            else ""
        )

        if annus_txt and annus_txt not in fons_txt:
            fons_indicizzata = (
                f"{fons_txt} ({annus_txt})"
            )
        else:
            fons_indicizzata = fons_txt

        # --------------------------------------------------
        # STROFE
        # --------------------------------------------------
        for lg in root.findall(
            ".//tei:body//tei:lg",
            ns
        ):
            stropha_n = lg.get(
                "n",
                ""
            )

            stropha_type = lg.get(
                "type",
                ""
            )

            # ----------------------------------------------
            # VERSI
            # ----------------------------------------------
            for l in lg.findall(
                "./tei:l",
                ns
            ):
                l_id = l.get(
                    '{http://www.w3.org/XML/1998/namespace}id',
                    ''
                )

                l_n = l.get(
                    'n',
                    ''
                )

                l_type = l.get(
                    'type',
                    ''
                )

                l_text = "".join(
                    l.itertext()
                ).strip()

                search_index.append({
                    "id": l_id,
                    "hymnus_id": file_id,
                    "file": html_filename,
                    "titulus": titulus_txt,
                    "auctor": auctor_txt,
                    "metrum": metrum_txt,
                    "fons": fons_indicizzata,
                    "stropha_n": stropha_n,
                    "stropha_type": stropha_type,
                    "versus_n": l_n,
                    "versus_type": l_type,
                    "locus": f"str. {stropha_n}, v. {l_n}",
                    "textus": l_text,
                    "textus_norm": normalize(l_text)
                })

    # Questa sezione è allineata all'interno della funzione per salvare il file DOPO il ciclo for
    output_file = "02_search_index.json"

    with open(
        out_path / output_file,
        'w',
        encoding='utf-8'
    ) as jf:
        json.dump(
            search_index,
            jf,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"✅ File '{output_file}' creato in {output_folder}."
    )
    print(
        f"📚 Indicizzati {len(search_index)} versi."
    )

# Punto di ingresso dello script corretto con i dunder (double underscore) __
if __name__ == "__main__":
    build_search_index(
        "output_TEI",
        "output_HTML"
    )
