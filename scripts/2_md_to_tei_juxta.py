import os
import re
from pathlib import Path

def transform_logic(md_content, file_id):
    parts = md_content.split('---')
    if len(parts) < 3: 
        return None
    
    body_text = parts[2].strip()
    
    stanzas = re.split(r'\n\s*\n', body_text)
    xml_stanzas = []
    global_counter = 1
    
    for i, stanza in enumerate(stanzas, 1):
        lines = [l.strip() for l in stanza.split('\n') if l.strip()]
        if not lines:
            continue
            
        lg_tag = f'      <lg n="{i}" xml:id="{file_id}_{i}">'
        xml_ls = []
        
        for line in lines:
            clean_line = line.lower()
            clean_line = re.sub(r'[^\w\s]', '', clean_line)
            clean_line = " ".join(clean_line.split())
            
            xml_ls.append(f'        <l n="{global_counter}" xml:id="{file_id}_{i}_{global_counter}">{clean_line}</l>')
            global_counter += 1
            
        xml_stanzas.append(lg_tag + "\n" + "\n".join(xml_ls) + "\n      </lg>")
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="{file_id}">
  <text>
    <body>
{"\n".join(xml_stanzas)}
    </body>
  </text>
</TEI>"""

def run_batch(in_folder, out_folder):
    input_path = Path(in_folder)
    output_path = Path(out_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    
    files = list(input_path.glob("*.md"))
    print(f"🚀 Batch processing di {len(files)} file per Juxta...")
    
    for f_path in files:
        file_id = f_path.stem
        with open(f_path, 'r', encoding='utf-8') as f:
            xml_data = transform_logic(f.read(), file_id)
            
        if xml_data:
            with open(output_path / f"{file_id}.xml", 'w', encoding='utf-8') as f:
                f.write(xml_data)
            print(f"   ✅ {f_path.name} semplificato per collazione.")

if __name__ == "__main__":
    run_batch("input_MD", "output_TEI_Juxta")
