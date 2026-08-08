import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

# ==========================================
# CARICAMENTO VARIABILI D'AMBIENTE (.env)
# ==========================================
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

FILE_PATH = os.getenv("FILE_PATH", "Hymni.xlsx")

# ==========================================
# CARICAMENTO DEI FOGLI EXCEL CON PANDAS
# ==========================================
print("Lettura del file Excel...")
excel_data = pd.ExcelFile(FILE_PATH)

df_hymni = pd.read_excel(excel_data, sheet_name="Hymni").fillna("")
df_fontes = pd.read_excel(excel_data, sheet_name="Fontes").fillna("")
df_doxologiae = pd.read_excel(excel_data, sheet_name="Doxologiae").fillna("")
df_calendarium = pd.read_excel(excel_data, sheet_name="Calendarium").fillna("")
df_festa = pd.read_excel(excel_data, sheet_name="Festa").fillna("")
df_usus = pd.read_excel(excel_data, sheet_name="Usus").fillna("")

# Conversione in liste di dizionari per Cypher
rows_hymni = df_hymni.to_dict(orient="records")
rows_fontes = df_fontes.to_dict(orient="records")
rows_doxologiae = df_doxologiae.to_dict(orient="records")
rows_calendarium = df_calendarium.to_dict(orient="records")
rows_festa = df_festa.to_dict(orient="records")
rows_usus = df_usus.to_dict(orient="records")

# ==========================================
# QUERY CYPHER PER L'IMPORTAZIONE
# ==========================================

# 1. Creazione Vincoli e Indici per Ottimizzare le Prestazioni
CYPHER_CONSTRAINTS = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (h:Hymnus) REQUIRE h.id_hymni IS UNIQUE;",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Auctor) REQUIRE a.nomen_auc IS UNIQUE;",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Metrum) REQUIRE m.metrum IS UNIQUE;",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (o:Fons) REQUIRE o.id_fontis IS UNIQUE;",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (g:Doxologia) REQUIRE g.id_doxologiae IS UNIQUE;",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Dies) REQUIRE d.id_diei IS UNIQUE;",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (f:Festum) REQUIRE f.id_festi IS UNIQUE;",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (me:Mensis) REQUIRE me.mensis IS UNIQUE;"
]

# 2. Popolamento Nodi Fons (Foglio "Fontes")
CYPHER_FONTES = """
UNWIND $rows AS row
MERGE (o:Fons {id_fontis: toString(row.ID_Fontis)})
SET o.titulus = row.Titulus,
    o.editio_fon = row.Editio,
    o.editor_fon = row.Editor,
    o.locus_fon = row.Locus,
    o.saec_fon = toString(row.Saeculum),
    o.annus_fon = toString(row.Annus),
    o.link_fon = row.Nexus_Externus
"""

# 3. Popolamento Nodi Doxologia (Foglio "Doxologiae")
CYPHER_DOXOLOGIAE = """
UNWIND $rows AS row
MERGE (g:Doxologia {id_doxologiae: toString(row.ID_Doxologiae)})
SET g.textus_dox = row.Textus,
    g.notae_dox = row.Notae
"""

# 4. Popolamento Nodi Dies, Mensis (me) e Relazione DURING (Foglio "Calendarium")
CYPHER_CALENDARIUM = """
UNWIND $rows AS row
// Creazione/Aggiornamento Nodo Dies
MERGE (d:Dies {id_diei: toString(row.ID_Diei)})
SET d.mensis = toString(row.Mensis),
    d.dies = toString(row.Dies),
    d.dies_mensis = row.Dies_Mensis,
    d.cal_rom = row.Calendarium_Romanum,
    d.lit_dom = row.Littera_Dominicalis,
    d.epacta = row.Cyclus_Epactarum

// Gestione dell'entità (me:Mensis) e relazione (d:Dies)-[:DURING]->(me:Mensis)
FOREACH (_ IN CASE WHEN row.Mensis IS NOT NULL AND toString(row.Mensis) <> '' THEN [1] ELSE [] END |
    MERGE (me:Mensis {mensis: toString(row.Mensis)})
    MERGE (d)-[:DURING]->(me)
)
"""

# 5. Popolamento Nodi Festum (Foglio "Festa")
CYPHER_FESTA = """
UNWIND $rows AS row
MERGE (f:Festum {id_festi: toString(row.ID_Festi)})
SET f.def_fes = row.Festum,
    f.typus_fes = row.Typus
"""

# 6. Popolamento Nodi Hymnus, Auctor, Metrum (m) e Relazioni (Foglio "Hymni")
CYPHER_HYMNI = """
UNWIND $rows AS row
// Creazione/Aggiornamento Nodo Hymnus
MERGE (h:Hymnus {id_hymni: toString(row.ID_Hymni)})
SET h.incipit = row.Incipit,
    h.strophae = row.Strophae,
    h.notae_hym = row.Notae,
    h.saec_rec = toString(row.Recognitus),
    h.exemplar = toString(row.ID_Exemplaris),
    h.locus_hym = row.Editio,
    h.rh = toString(row.RH),
    h.ahma = toString(row.AHMA),
    h.hibr = toString(row.HiBR),
    h.tdh = toString(row.TDH),
    h.ico = toString(row.ICO),
    h.link_hym = row.Nexus_Externus

// 6a. Gestione Metrum (m) e relazione (h)-[:WRITTEN_IN]->(m)
FOREACH (_ IN CASE WHEN row.Metrum IS NOT NULL AND toString(row.Metrum) <> '' THEN [1] ELSE [] END |
    MERGE (m:Metrum {metrum: toString(row.Metrum)})
    MERGE (h)-[:WRITTEN_IN]->(m)
)

// 6b. Gestione Auctor e Logica Attribuzione (WROTE / status)
// CASO 1 & 2: Autore presente (Attribuito Certo o Dubbio)
FOREACH (_ IN CASE WHEN row.Auctor IS NOT NULL AND toString(row.Auctor) <> '' THEN [1] ELSE [] END |
    MERGE (a:Auctor {nomen_auc: toString(row.Auctor)})
    ON CREATE SET a.saec_auc = toString(row.Saeculum)
    
    // Creazione arco WROTE con proprietà status
    MERGE (a)-[r:WROTE]->(h)
    SET r.status = toString(row.Status)
)

// CASO 3: Autore VUOTO e Status = 'anonymus'
FOREACH (_ IN CASE WHEN (row.Auctor IS NULL OR toString(row.Auctor) = '') AND toLower(toString(row.Status)) = 'anonymus' THEN [1] ELSE [] END |
    SET h.status = 'anonymus'
)

// CASO 4: Autore VUOTO e Status VUOTO (Incertus / Non studiato)
FOREACH (_ IN CASE WHEN (row.Auctor IS NULL OR toString(row.Auctor) = '') AND (row.Status IS NULL OR toString(row.Status) = '') THEN [1] ELSE [] END |
    SET h.status = 'incertus'
)
"""

# 7. Creazione Relazioni DERIVES_FROM tra Inni (dopo che tutti gli Hymnus sono stati creati)
CYPHER_DERIVES_FROM = """
UNWIND $rows AS row
WITH row WHERE row.ID_Exemplaris IS NOT NULL AND toString(row.ID_Exemplaris) <> ''
MATCH (h1:Hymnus {id_hymni: toString(row.ID_Hymni)})
MATCH (h2:Hymnus {id_hymni: toString(row.ID_Exemplaris)})
MERGE (h1)-[r:DERIVES_FROM]->(h2)
SET r.saec_rec = toString(row.Recognitus)
"""

# 8. Popolamento Relazioni ed Eventuali Proprietà dal Foglio "Usus"
CYPHER_USUS = """
UNWIND $rows AS row

// 8a. Relazione (f:Festum)-[:USES_HYMN]->(h:Hymnus) + aggiornamento proprietà specifiche di Festum
FOREACH (_ IN CASE WHEN row.ID_Festi IS NOT NULL AND toString(row.ID_Festi) <> '' AND row.ID_Hymni IS NOT NULL AND toString(row.ID_Hymni) <> '' THEN [1] ELSE [] END |
    MERGE (f:Festum {id_festi: toString(row.ID_Festi)})
    MERGE (h:Hymnus {id_hymni: toString(row.ID_Hymni)})
    MERGE (f)-[:USES_HYMN]->(h)
    
    // Aggiornamento proprietà specifiche da Usus sul nodo Festum
    SET f.festum = row.Festum,
        f.officium = row.Officium,
        f.notae_off = row.Notae
)

// 8b. Relazione (f:Festum)-[:ON_DATE]->(d:Dies)
FOREACH (_ IN CASE WHEN row.ID_Festi IS NOT NULL AND toString(row.ID_Festi) <> '' AND row.Dies IS NOT NULL AND toString(row.Dies) <> '' THEN [1] ELSE [] END |
    MERGE (f:Festum {id_festi: toString(row.ID_Festi)})
    MERGE (d:Dies {id_diei: toString(row.Dies)})
    MERGE (f)-[:ON_DATE]->(d)
)

// 8c. Relazione (f:Festum)-[:ATTESTED_IN]->(o:Fons)
FOREACH (_ IN CASE WHEN row.ID_Festi IS NOT NULL AND toString(row.ID_Festi) <> '' AND row.ID_Fontis IS NOT NULL AND toString(row.ID_Fontis) <> '' THEN [1] ELSE [] END |
    MERGE (f:Festum {id_festi: toString(row.ID_Festi)})
    MERGE (o:Fons {id_fontis: toString(row.ID_Fontis)})
    MERGE (f)-[:ATTESTED_IN]->(o)
)

// 8d. Relazione (h:Hymnus)-[:ATTESTED_IN]->(o:Fons)
FOREACH (_ IN CASE WHEN row.ID_Hymni IS NOT NULL AND toString(row.ID_Hymni) <> '' AND row.ID_Fontis IS NOT NULL AND toString(row.ID_Fontis) <> '' THEN [1] ELSE [] END |
    MERGE (h:Hymnus {id_hymni: toString(row.ID_Hymni)})
    MERGE (o:Fons {id_fontis: toString(row.ID_Fontis)})
    MERGE (h)-[:ATTESTED_IN]->(o)
)

// 8e. Relazione (h:Hymnus)-[:HAS_DOXOLOGY]->(g:Doxologia)
FOREACH (_ IN CASE WHEN row.ID_Hymni IS NOT NULL AND toString(row.ID_Hymni) <> '' AND row.ID_Doxologiae IS NOT NULL AND toString(row.ID_Doxologiae) <> '' THEN [1] ELSE [] END |
    MERGE (h:Hymnus {id_hymni: toString(row.ID_Hymni)})
    MERGE (g:Doxologia {id_doxologiae: toString(row.ID_Doxologiae)})
    MERGE (h)-[:HAS_DOXOLOGY]->(g)
)
"""

# ==========================================
# ESECUZIONE IMPORTAZIONE
# ==========================================
def run_import():
    if not NEO4J_PASSWORD:
        raise ValueError("ERRORE: La password di Neo4j non è stata impostata. Verifica il file .env!")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        print("1/8. Creazione vincoli di unicità...")
        for constraint in CYPHER_CONSTRAINTS:
            session.run(constraint)

        print("2/8. Importazione Fontes...")
        session.run(CYPHER_FONTES, rows=rows_fontes)

        print("3/8. Importazione Doxologiae...")
        session.run(CYPHER_DOXOLOGIAE, rows=rows_doxologiae)

        print("4/8. Importazione Calendarium (Dies, Mensis [me] e DURING)...")
        session.run(CYPHER_CALENDARIUM, rows=rows_calendarium)

        print("5/8. Importazione Festa...")
        session.run(CYPHER_FESTA, rows=rows_festa)

        print("6/8. Importazione Hymni, Auctores, Metra [m] e Attribuzioni...")
        session.run(CYPHER_HYMNI, rows=rows_hymni)

        print("7/8. Importazione Relazioni DERIVES_FROM tra Inni...")
        session.run(CYPHER_DERIVES_FROM, rows=rows_hymni)

        print("8/8. Importazione Foglio Usus e relazioni complessive...")
        session.run(CYPHER_USUS, rows=rows_usus)

    driver.close()
    print(" Importazione completata con successo!")

if __name__ == "__main__":
    run_import()
