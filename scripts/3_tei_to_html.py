import os
from pathlib import Path
import xml.etree.ElementTree as ET

def extract_tei_meta(root, ns):

    meta = {}

    # --- titolo e autore ---
    title_el = root.find(
        ".//tei:titleStmt/tei:title",
        ns
    )

    author_el = root.find(
        ".//tei:titleStmt/tei:author",
        ns
    )

    meta['titulus'] = (
        title_el.text
        if title_el is not None
        else "Untitled"
    )

    meta['auctor'] = (
        author_el.text
        if author_el is not None
        else "Anonymus"
    )

    # --- note multiple dal front ---
    note_elements = root.findall(
        ".//tei:front/tei:p[@type='notae']",
        ns
    )

    meta['notae'] = [
        n.text.strip()
        for n in note_elements
        if n.text and n.text.strip()
    ]

    # --- fonte e anno ---
    fons_el = root.find(
        ".//tei:sourceDesc//tei:title",
        ns
    )

    annus_el = root.find(
        ".//tei:sourceDesc//tei:date",
        ns
    )

    meta['fons'] = (
        fons_el.text
        if fons_el is not None
        else ""
    )

    meta['annus'] = (
        annus_el.text
        if annus_el is not None
        else ""
    )

    # --- metro ---
    metrum_el = root.find(
        ".//tei:notesStmt/tei:note[@type='metrum']",
        ns
    )

    if metrum_el is not None and metrum_el.text:

        meta['metrum'] = (
            metrum_el.text
            .replace("Metrum: ", "")
            .strip()
        )

    else:

        meta['metrum'] = "Unknown"

    return meta

def tei_to_html_logic(xml_content):

    ns = {
        'tei': 'http://www.tei-c.org/ns/1.0'
    }

    ET.register_namespace(
        '',
        'http://www.tei-c.org/ns/1.0'
    )

    try:

        root = ET.fromstring(xml_content)

    except ET.ParseError as e:

        print(f"❌ Errore di parsing XML: {e}")

        return None

    meta = extract_tei_meta(root, ns)

    # --- strofe e versi ---
    html_stanzas = []

    lg_elements = root.findall(
        ".//tei:body/tei:lg",
        ns
    )

    for lg in lg_elements:

        lg_id = lg.get(
            '{http://www.w3.org/XML/1998/namespace}id',
            ''
        )

        lg_n = lg.get('n', '')

        lg_type = lg.get('type', '')

        html_lines = []

        for l in lg.findall("tei:l", ns):

            l_id = l.get(
                '{http://www.w3.org/XML/1998/namespace}id',
                ''
            )

            l_n = l.get('n', '')

            l_type = l.get('type', '')

            l_text = l.text if l.text else ""

            line_html = (
                f'      <div class="line" '
                f'id="{l_id}" '
                f'data-n="{l_n}" '
                f'data-type="{l_type}">'

                f'<span class="line-number">{l_n}</span>'

                f'<span class="line-text">{l_text}</span>'

                f'</div>'
            )

            html_lines.append(line_html)

        stanza_html = (
            f'    <div class="stanza" '
            f'id="{lg_id}" '
            f'data-n="{lg_n}" '
            f'data-type="{lg_type}">\n'

            f'{"\n".join(html_lines)}\n'

            f'    </div>'
        )

        html_stanzas.append(stanza_html)

    # --- note HTML multiple ---
    html_notes = "\n".join(
        [
            f'            <p class="poem-notes"><em>{nota}</em></p>'
            for nota in meta['notae']
        ]
    )

    # --- HTML finale ---
    html_template = f"""<!DOCTYPE html>

<html lang="la">

<head>

    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>{meta['titulus']}</title>

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cardo:ital,wght@0,400;0,700;1,400&family=Montserrat:wght@400;700&display=swap" rel="stylesheet">    

    <link rel="stylesheet" href="style.css">

</head>

<body class="hymnus-page">

    <div class="poem-container">

        <header class="poem-meta-header">

            <h1 class="poem-title">{meta['titulus']}</h1>

            <p class="poem-author">{meta['auctor']}</p>

{html_notes}

        </header>

        <main class="poem-body">

{"\n\n".join(html_stanzas)}

            <script src="HY.js"></script>

        </main>

        <footer class="poem-footer">

            <hr>

            <p><strong>Metrum:</strong> {meta['metrum']}</p>

            <p><strong>Fons:</strong> {meta['fons']} ({meta['annus']})</p>

        </footer>

    </div>

</body>

</html>
"""

    return html_template

def run_html_batch(in_folder, out_folder):

    input_path = Path(in_folder)

    output_path = Path(out_folder)

    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    files = list(input_path.glob("*.xml"))

    print(
        f"🚀 Batch processing di "
        f"{len(files)} file XML-TEI in HTML..."
    )

    for f_path in files:

        file_id = f_path.stem

        with open(
            f_path,
            'r',
            encoding='utf-8'
        ) as f:

            html_data = tei_to_html_logic(f.read())

        if html_data:

            with open(
                output_path / (file_id + ".html"),
                'w',
                encoding='utf-8'
            ) as f:

                f.write(html_data)

            print(
                f"   ✅ {f_path.name} convertito in HTML."
            )

if __name__ == "__main__":

    run_html_batch("output_TEI", "output_HTML")
