import os
import re
from pathlib import Path

# --- registro metrico: da aggiornare se si aggiungono nuovi tipi di strofe! ---
METRIC_REGISTRY = {
    "Dimetrum iambicum": {
        "lg_type": "tetrastichon_iambicum", 
        "l_types": ["dimeter_iambicus"]
    },
    "Trimetrum iambicum": {
        "lg_type": "pentastichon_iambicum", 
        "l_types": ["trimeter_iambicus", "trimeter_iambicus", "trimeter_iambicus", "trimeter_iambicus", "trimeter_iambicus"]
    },
    "Sapphicum": {
        "lg_type": "strophe_sapphica", 
        "l_types": ["hendecasyllabus_sapphicus", "hendecasyllabus_sapphicus", "hendecasyllabus_sapphicus", "adonius"]
    },
    "Tetrametrum trochaicum catalepticum": {
        "lg_type": "tristichon_trochaicum", 
        "l_types": ["dimeter_trochaicus", "dimeter_trochaicus_catalepticus", "dimeter_trochaicus", "dimeter_trochaicus_catalepticus", "dimeter_trochaicus", "dimeter_trochaicus_catalepticus"]
    },
    "Hendecasyllabum Alcaicum": {
        "lg_type": "tetrastichon_alcaicum", 
        "l_types": ["hendecasyllabus_alcaicus", "hendecasyllabus_alcaicus", "hendecasyllabus_alcaicus", "hendecasyllabus_alcaicus"]
    },
    "Alcaicum": {
        "lg_type": "strophe_alcaica", 
        "l_types": ["hendecasyllabus_alcaicus", "hendecasyllabus_alcaicus", "enneasyllabus_alcaicus", "decasyllabus_alcaicus"]
    },
    "Asclepiadeum II": {
        "lg_type": "strophe_asclepiadea_II", 
        "l_types": ["asclepiadeus_minor", "asclepiadeus_minor", "asclepiadeus_minor", "glyconius"]
    },
    "Asclepiadeum III": {
        "lg_type": "strophe_asclepiadea_III", 
        "l_types": ["asclepiadeus_minor", "asclepiadeus_minor", "pherecratius", "glyconius"]
    }
}

def transform_logic(md_content, file_id):

    parts = md_content.split('---')

    if len(parts) < 3:
        return None

    meta = {
        line.split(':', 1)[0].strip():
        line.split(':', 1)[1].strip()
        for line in parts[1].strip().split('\n')
        if ':' in line
    }

    m_key = meta.get("Metrum", "Iambicum")

    m_cfg = METRIC_REGISTRY.get(
        m_key,
        {
            "lg_type": "unknown_strophe",
            "l_types": ["versus"]
        }
    )

    titulus = meta.get('Titulus', '')

    raw_notae = meta.get('Notae', '')

    note_items = [
        n.strip()
        for n in raw_notae.split(';')
        if n.strip()
    ]

    notes_xml = "\n".join(
        [
            f'        <note type="commentarius">{n}</note>'
            for n in note_items
        ]
    )

    front_notes_xml = "\n".join(
        [
            f'      <p type="notae">{n}</p>'
            for n in note_items
        ]
    )

    header = f"""  <teiHeader>

    <fileDesc>

      <titleStmt>

        <title>{titulus}</title>

        <author>{meta.get('Auctor', '')}</author>

        <respStmt>
          <resp>Collegit et adnotavit</resp>
          <name>{meta.get('Curator', '')}</name>
        </respStmt>

      </titleStmt>

      <publicationStmt>

        <publisher>Repositorium Hymnorum Latinorum</publisher>

      </publicationStmt>

      <notesStmt>

        <note type="metrum">Metrum: {m_key}</note>

{notes_xml}

      </notesStmt>

      <sourceDesc>

        <bibl>
          <title>{meta.get('Fons', '')}</title>
          <date>{meta.get('Annus', '')}</date>
        </bibl>

      </sourceDesc>

    </fileDesc>

  </teiHeader>"""

    body_text = parts[2].strip()

    stanzas = re.split(r'\n\s*\n', body_text)

    xml_stanzas = []

    global_counter = 1

    for i, stanza in enumerate(stanzas, 1):

        lines = [
            l.strip()
            for l in stanza.split('\n')
            if l.strip()
        ]

        lg_tag = (
            f'      <lg n="{i}" '
            f'type="{m_cfg["lg_type"]}" '
            f'xml:id="{file_id}_{i}">'
        )

        xml_ls = []

        for j, line in enumerate(lines):

            types = m_cfg["l_types"]

            l_type = (
                types[j]
                if j < len(types)
                else types[-1]
            )

            xml_ls.append(
                f'        <l '
                f'n="{global_counter}" '
                f'type="{l_type}" '
                f'xml:id="{file_id}_{i}_{global_counter}">'
                f'{line}'
                f'</l>'
            )

            global_counter += 1

        xml_stanzas.append(
            lg_tag
            + "\n"
            + "\n".join(xml_ls)
            + "\n      </lg>"
        )

    return f"""<?xml version="1.0" encoding="UTF-8"?>

<TEI xmlns="http://www.tei-c.org/ns/1.0"
     xml:id="{file_id}"
     xml:lang="la">

{header}

  <text>

    <front>

{front_notes_xml}

    </front>

    <body>

      <head type="incipit">{titulus}</head>

{"\n".join(xml_stanzas)}

    </body>

    <back>

      <div type="fons">
        <p type="titulus">{meta.get('Fons', '')}</p>
        <p type="annus">{meta.get('Annus', '')}</p>
      </div>

      <div type="metrum">
        <p type="metrum">Metrum: {m_key}</p>
      </div>

    </back>

  </text>

</TEI>"""

def run_batch(in_folder, out_folder):

    input_path = Path(in_folder)

    output_path = Path(out_folder)

    output_path.mkdir(parents=True, exist_ok=True)

    files = list(input_path.glob("*.md"))

    print(f"🚀 Batch processing di {len(files)} file...")

    for f_path in files:

        file_id = f_path.stem

        with open(f_path, 'r', encoding='utf-8') as f:
            xml_data = transform_logic(f.read(), file_id)

        if xml_data:

            with open(
                output_path / (file_id + ".xml"),
                'w',
                encoding='utf-8'
            ) as f:
                f.write(xml_data)

            print(f"   ✅ {f_path.name} convertito.")

if __name__ == "__main__":

    run_batch("input_MD", "output_TEI")
