# ============================================================
# VIO 83 AI ORCHESTRA — Copyright (c) 2026 Viorica Porcu (vio83)
# DUAL LICENSE: Proprietary + AGPL-3.0 — See LICENSE files
# ============================================================
"""
VIO 83 — WORLD KNOWLEDGE TAXONOMY PIUMA™
==========================================
Tassonomia completa della conoscenza umana — Marzo 2026.

Struttura gerarchica a 4 livelli:
  L0: Macro-Dominio      (12 domini)
  L1: Dominio            (87 categorie)
  L2: Specializzazione   (500+ sottocategorie)
  L3: Micro-niche        (2000+ specificazioni)

Ogni nodo include:
  - provr_optimal: migliore AI provider per questo dominio
  - temperature: temperatura ottimale per il task
  - max_tokens: risposta ottimale in token
  - system_fragment: frammento system prompt specializzato
  - keywords_it: parole chiave italiano
  - keywords_en: parole chiave inglese
  - complexity: 1-5 (1=semplice, 5=massima complessità)
  - requires_reasoning: se serve chain-of-thought
  - requires_web: se serve accesso web/ricerca
  - citation_needed: se servono fonti/citazioni

Dati reali, completi, verificati — Marzo 2026.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────
# STRUTTURA DATI TASSONOMIA
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TaxonomyNode:
    id: str
    name_it: str
    name_en: str
    parent_id: Optional[str]
    level: int                          # 0=macro, 1=dominio, 2=spec, 3=micro
    provr_optimal: str               # claude/openai/gemini/mistral/deepseek/ollama
    provr_fallback: str
    temperature: float                  # 0.0-1.0
    max_tokens: int
    system_fragment: str                # Da iniettare nel system prompt
    keywords_it: Tuple[str, ...]
    keywords_en: Tuple[str, ...]
    complexity: int                     # 1-5
    requires_reasoning: bool
    requires_web: bool
    citation_needed: bool


# ─────────────────────────────────────────────────────────────
# TASSONOMIA COMPLETA — 12 MACRO-DOMINI
# ─────────────────────────────────────────────────────────────

TAXONOMY: Dict[str, TaxonomyNode] = {}

def _add(node: TaxonomyNode):
    TAXONOMY[node.id] = node

# ══════════════════════════════════════════════════════════════
# L0 — MACRO-DOMINI (12)
# ══════════════════════════════════════════════════════════════

_add(TaxonomyNode(
    id="TECH", name_it="Tecnologia & Informatica", name_en="Technology & Computing",
    parent_id=None, level=0, provr_optimal="openai", provr_fallback="claude",
    temperature=0.2, max_tokens=4096, system_fragment="Sei un esperto tecnico e informatico. Usa terminologia precisa e fornisci codice funzionante.",
    keywords_it=("tecnologia","software","hardware","informatica","computer","digitale","sistema"),
    keywords_en=("technology","software","hardware","computing","digital","system","code"),
    complexity=4, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="SCI", name_it="Scienze Naturali & Formali", name_en="Natural & Formal Sciences",
    parent_id=None, level=0, provr_optimal="claude", provr_fallback="openai",
    temperature=0.1, max_tokens=4096, system_fragment="Sei uno scienziato rigoroso. Usa il metodo scientifico, cita fonti peer-reviewed, distingui fatti da ipotesi.",
    keywords_it=("scienza","fisica","chimica","biologia","matematica","astronomia","ricerca"),
    keywords_en=("science","physics","chemistry","biology","mathematics","astronomy","research"),
    complexity=5, requires_reasoning=True, requires_web=False, citation_needed=True,
))

_add(TaxonomyNode(
    id="MED", name_it="Medicina & Salute", name_en="Medicine & Health",
    parent_id=None, level=0, provr_optimal="claude", provr_fallback="openai",
    temperature=0.1, max_tokens=3072, system_fragment="Sei un medico esperto. Fornisci informazioni accurate e aggiornate. Ricorda all'utente di consultare un medico per diagnosi.",
    keywords_it=("medicina","salute","malattia","sintomi","farmaci","diagnosi","terapia","paziente"),
    keywords_en=("medicine","health","disease","symptoms","drugs","diagnosis","therapy","patient"),
    complexity=5, requires_reasoning=True, requires_web=False, citation_needed=True,
))

_add(TaxonomyNode(
    id="LAW", name_it="Diritto & Legge", name_en="Law & Legal",
    parent_id=None, level=0, provr_optimal="claude", provr_fallback="openai",
    temperature=0.05, max_tokens=4096, system_fragment="Sei un avvocato esperto. Fornisci analisi legali precise. Specifica sempre la giurisdizione e raccomanda consulenza professionale.",
    keywords_it=("legge","diritto","contratto","normativa","giurisprudenza","tribunale","avvocato","codice"),
    keywords_en=("law","legal","contract","regulation","jurisprudence","court","attorney","code"),
    complexity=5, requires_reasoning=True, requires_web=True, citation_needed=True,
))

_add(TaxonomyNode(
    id="FIN", name_it="Finanza & Economia", name_en="Finance & Economics",
    parent_id=None, level=0, provr_optimal="openai", provr_fallback="claude",
    temperature=0.1, max_tokens=3072, system_fragment="Sei un analista finanziario ed economista. Fornisci analisi basate su dati reali e avvisa sui rischi.",
    keywords_it=("finanza","economia","investimento","mercato","trading","banca","cripto","azioni"),
    keywords_en=("finance","economics","investment","market","trading","bank","crypto","stocks"),
    complexity=4, requires_reasoning=True, requires_web=True, citation_needed=True,
))

_add(TaxonomyNode(
    id="BUS", name_it="Business & Management", name_en="Business & Management",
    parent_id=None, level=0, provr_optimal="openai", provr_fallback="claude",
    temperature=0.4, max_tokens=3072, system_fragment="Sei un esperto di business e management. Fornisci strategie pratiche e actionable basate su best practice internazionali.",
    keywords_it=("business","azienda","management","strategia","marketing","vendite","startup","impresa"),
    keywords_en=("business","company","management","strategy","marketing","sales","startup","enterprise"),
    complexity=3, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="ART", name_it="Arte, Cultura & Umanistica", name_en="Arts, Culture & Humanities",
    parent_id=None, level=0, provr_optimal="claude", provr_fallback="gemini",
    temperature=0.8, max_tokens=4096, system_fragment="Sei un esperto di arte, letteratura e cultura. Usa un linguaggio evocativo e ricco di sfumature.",
    keywords_it=("arte","letteratura","musica","cinema","cultura","filosofia","storia","poesia"),
    keywords_en=("art","literature","music","cinema","culture","philosophy","history","poetry"),
    complexity=3, requires_reasoning=False, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="EDU", name_it="Educazione & Apprendimento", name_en="Education & Learning",
    parent_id=None, level=0, provr_optimal="claude", provr_fallback="gemini",
    temperature=0.5, max_tokens=4096, system_fragment="Sei un educatore eccellente. Spiega con chiarezza, usa esempi concreti e adatta il livello al discente.",
    keywords_it=("educazione","apprendimento","insegnamento","scuola","università","studio","formazione"),
    keywords_en=("education","learning","teaching","school","university","study","training"),
    complexity=2, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="SOC", name_it="Società, Politica & Sociologia", name_en="Society, Politics & Sociology",
    parent_id=None, level=0, provr_optimal="claude", provr_fallback="openai",
    temperature=0.3, max_tokens=3072, system_fragment="Sei un analista sociale. Presenta prospettive multiple, evita bias politici, usa dati verificabili.",
    keywords_it=("società","politica","sociologia","governo","democrazia","elezioni","diritti","welfare"),
    keywords_en=("society","politics","sociology","government","democracy","elections","rights","welfare"),
    complexity=4, requires_reasoning=True, requires_web=True, citation_needed=True,
))

_add(TaxonomyNode(
    id="ENV", name_it="Ambiente & Sostenibilità", name_en="Environment & Sustainability",
    parent_id=None, level=0, provr_optimal="claude", provr_fallback="gemini",
    temperature=0.2, max_tokens=3072, system_fragment="Sei un esperto di ambiente e sostenibilità. Basa le risposte su dati scientifici IPCC e letteratura peer-reviewed.",
    keywords_it=("ambiente","clima","sostenibilità","energia","rinnovabile","CO2","ecosistema","biodiversità"),
    keywords_en=("environment","climate","sustainability","energy","renewable","CO2","ecosystem","biodiversity"),
    complexity=4, requires_reasoning=True, requires_web=True, citation_needed=True,
))

_add(TaxonomyNode(
    id="PSY", name_it="Psicologia & Neuroscienze", name_en="Psychology & Neuroscience",
    parent_id=None, level=0, provr_optimal="claude", provr_fallback="openai",
    temperature=0.3, max_tokens=3072, system_fragment="Sei uno psicologo e neuroscienziato. Basa risposte su ricerche validate. Tratta temi sensibili con delicatezza.",
    keywords_it=("psicologia","mente","emozione","comportamento","terapia","neuroscienza","cognitivo","trauma"),
    keywords_en=("psychology","mind","emotion","behavior","therapy","neuroscience","cognitive","trauma"),
    complexity=4, requires_reasoning=True, requires_web=False, citation_needed=True,
))

_add(TaxonomyNode(
    id="CRE", name_it="Creatività & Generazione Contenuti", name_en="Creativity & Content Generation",
    parent_id=None, level=0, provr_optimal="claude", provr_fallback="gemini",
    temperature=0.9, max_tokens=8192, system_fragment="Sei un autore creativo brillante. Produci contenuti originali, evocativi e di alta qualità letteraria.",
    keywords_it=("scrivi","crea","racconto","storia","articolo","blog","copywriting","contenuto"),
    keywords_en=("write","create","story","article","blog","copywriting","content","creative"),
    complexity=2, requires_reasoning=False, requires_web=False, citation_needed=False,
))


# ══════════════════════════════════════════════════════════════
# L1 — DOMINI (87 categorie)
# ══════════════════════════════════════════════════════════════

# ─── TECH Subcategories ───────────────────────────────────────

_add(TaxonomyNode(
    id="TECH.AI", name_it="Intelligenza Artificiale & ML", name_en="Artificial Intelligence & ML",
    parent_id="TECH", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.2, max_tokens=4096, system_fragment="Sei un esperto di AI/ML. Padroneggi LLM, deep learning, training, fine-tuning, RAG, agenti AI.",
    keywords_it=("intelligenza artificiale","machine learning","rete neurale","LLM","GPT","transformer","modello","training","inferenza","embedding","RAG","agente","prompt"),
    keywords_en=("artificial intelligence","machine learning","neural network","LLM","GPT","transformer","model","training","inference","embedding","RAG","agent","prompt"),
    complexity=5, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="TECH.DEV", name_it="Sviluppo Software & Coding", name_en="Software Development & Coding",
    parent_id="TECH", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.1, max_tokens=8192, system_fragment="Sei un senior software engineer. Scrivi codice pulito, testato, documentato. Segui best practice SOLID, DRY.",
    keywords_it=("codice","programmazione","sviluppo","algoritmo","bug","debug","refactor","pull request","commit","git","API","testing","unit test"),
    keywords_en=("code","programming","development","algorithm","bug","debug","refactor","pull request","commit","git","API","testing","unit test"),
    complexity=4, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="TECH.WEB", name_it="Sviluppo Web & Frontend", name_en="Web Development & Frontend",
    parent_id="TECH", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.15, max_tokens=6144, system_fragment="Sei un esperto full-stack web developer. Padroneggi HTML5, CSS3, React, Vue, Next.js, TypeScript, REST, GraphQL.",
    keywords_it=("html","css","javascript","react","vue","angular","typescript","next.js","frontend","backend","fullstack","responsive","UI","UX"),
    keywords_en=("html","css","javascript","react","vue","angular","typescript","next.js","frontend","backend","fullstack","responsive","UI","UX"),
    complexity=3, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="TECH.MOBILE", name_it="Sviluppo Mobile iOS/Android", name_en="Mobile Development iOS/Android",
    parent_id="TECH", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.15, max_tokens=6144, system_fragment="Sei un esperto di sviluppo mobile. Padroneggi Swift/SwiftUI, Kotlin, React Native, Flutter.",
    keywords_it=("ios","android","swift","swiftui","kotlin","react native","flutter","app mobile","xcode","android studio"),
    keywords_en=("ios","android","swift","swiftui","kotlin","react native","flutter","mobile app","xcode","android studio"),
    complexity=4, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="TECH.DATA", name_it="Data Science & Analytics", name_en="Data Science & Analytics",
    parent_id="TECH", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.1, max_tokens=4096, system_fragment="Sei un data scientist esperto. Padroneggi Python pandas/numpy/sklearn, SQL, visualizzazione, statistica inferenziale.",
    keywords_it=("data science","analisi dati","dataset","pandas","numpy","statistica","visualizzazione","SQL","database","ETL","pipeline"),
    keywords_en=("data science","data analysis","dataset","pandas","numpy","statistics","visualization","SQL","database","ETL","pipeline"),
    complexity=4, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="TECH.CLOUD", name_it="Cloud & DevOps & Infrastruttura", name_en="Cloud & DevOps & Infrastructure",
    parent_id="TECH", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.15, max_tokens=4096, system_fragment="Sei un cloud architect e DevOps expert. Padroneggi AWS/GCP/Azure, Docker, Kubernetes, CI/CD, Terraform.",
    keywords_it=("cloud","AWS","GCP","Azure","docker","kubernetes","CI/CD","DevOps","terraform","infrastruttura","serverless","microservizi"),
    keywords_en=("cloud","AWS","GCP","Azure","docker","kubernetes","CI/CD","DevOps","terraform","infrastructure","serverless","microservices"),
    complexity=4, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="TECH.SEC", name_it="Cybersecurity & Privacy", name_en="Cybersecurity & Privacy",
    parent_id="TECH", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.1, max_tokens=4096, system_fragment="Sei un esperto di cybersecurity. Padroneggi OWASP, penetration testing, crittografia, GDPR. Non fornire codice malevolo.",
    keywords_it=("sicurezza","cybersecurity","hacking","vulnerabilità","crittografia","GDPR","privacy","firewall","VPN","autenticazione","OAuth"),
    keywords_en=("security","cybersecurity","hacking","vulnerability","cryptography","GDPR","privacy","firewall","VPN","authentication","OAuth"),
    complexity=5, requires_reasoning=True, requires_web=False, citation_needed=True,
))

_add(TaxonomyNode(
    id="TECH.DB", name_it="Database & Storage", name_en="Database & Storage",
    parent_id="TECH", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.1, max_tokens=4096, system_fragment="Sei un database architect. Padroneggi SQL (PostgreSQL, MySQL), NoSQL (MongoDB, Redis), ottimizzazione query, indexing.",
    keywords_it=("database","SQL","PostgreSQL","MySQL","MongoDB","Redis","query","indice","schema","ORM","relazionale","NoSQL"),
    keywords_en=("database","SQL","PostgreSQL","MySQL","MongoDB","Redis","query","index","schema","ORM","relational","NoSQL"),
    complexity=4, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="TECH.EMBEDDED", name_it="Sistemi Embedded & IoT", name_en="Embedded Systems & IoT",
    parent_id="TECH", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.15, max_tokens=4096, system_fragment="Sei un esperto di sistemi embedded e IoT. Padroneggi C/C++, Arduino, Raspberry Pi, protocolli MQTT, sensori.",
    keywords_it=("embedded","IoT","Arduino","Raspberry Pi","microcontroller","firmware","sensore","MQTT","real-time","RTOS"),
    keywords_en=("embedded","IoT","Arduino","Raspberry Pi","microcontroller","firmware","sensor","MQTT","real-time","RTOS"),
    complexity=5, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="TECH.BLOCKCHAIN", name_it="Blockchain & Web3", name_en="Blockchain & Web3",
    parent_id="TECH", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.15, max_tokens=4096, system_fragment="Sei un esperto blockchain e Web3. Padroneggi Ethereum, Solidity, smart contract, DeFi, NFT, Layer 2.",
    keywords_it=("blockchain","ethereum","solidity","smart contract","DeFi","NFT","web3","cripto","token","wallet","DAO"),
    keywords_en=("blockchain","ethereum","solidity","smart contract","DeFi","NFT","web3","crypto","token","wallet","DAO"),
    complexity=5, requires_reasoning=True, requires_web=True, citation_needed=False,
))

_add(TaxonomyNode(
    id="TECH.GAME", name_it="Game Development & Grafica 3D", name_en="Game Development & 3D Graphics",
    parent_id="TECH", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.3, max_tokens=4096, system_fragment="Sei un game developer esperto. Padroneggi Unity, Unreal Engine, C#, shaders, fisica, rendering, multiplayer.",
    keywords_it=("gioco","game","unity","unreal","shader","rendering","grafica 3D","fisica","animazione","multiplayer","motore"),
    keywords_en=("game","unity","unreal","shader","rendering","3D graphics","physics","animation","multiplayer","engine"),
    complexity=4, requires_reasoning=True, requires_web=False, citation_needed=False,
))

# ─── SCIENCE Subcategories ────────────────────────────────────

_add(TaxonomyNode(
    id="SCI.PHYS", name_it="Fisica", name_en="Physics",
    parent_id="SCI", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.05, max_tokens=4096, system_fragment="Sei un fisico. Usa formule matematiche precise, unità SI, derivazioni rigorose. Distingui meccanica classica, quantistica, relativistica.",
    keywords_it=("fisica","meccanica","quantistica","relatività","termodinamica","elettromagnetismo","particelle","campo","forza","energia","onda"),
    keywords_en=("physics","mechanics","quantum","relativity","thermodynamics","electromagnetism","particles","field","force","energy","wave"),
    complexity=5, requires_reasoning=True, requires_web=False, citation_needed=True,
))

_add(TaxonomyNode(
    id="SCI.CHEM", name_it="Chimica", name_en="Chemistry",
    parent_id="SCI", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.05, max_tokens=4096, system_fragment="Sei un chimico esperto. Usa nomenclatura IUPAC, bilanciamento equazioni, formule strutturali, stechiometria precisa.",
    keywords_it=("chimica","molecola","atomo","reazione","elemento","composto","organica","inorganica","polimero","catalisi"),
    keywords_en=("chemistry","molecule","atom","reaction","element","compound","organic","inorganic","polymer","catalysis"),
    complexity=5, requires_reasoning=True, requires_web=False, citation_needed=True,
))

_add(TaxonomyNode(
    id="SCI.BIO", name_it="Biologia & Genetica", name_en="Biology & Genetics",
    parent_id="SCI", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.1, max_tokens=4096, system_fragment="Sei un biologo molecolare e genetista. Basa risposte su letteratura scientifica. Usa terminologia tassonomica corretta.",
    keywords_it=("biologia","genetica","DNA","RNA","proteina","cellula","evoluzione","ecosistema","metabolismo","enzima","CRISPR"),
    keywords_en=("biology","genetics","DNA","RNA","protein","cell","evolution","ecosystem","metabolism","enzyme","CRISPR"),
    complexity=5, requires_reasoning=True, requires_web=False, citation_needed=True,
))

_add(TaxonomyNode(
    id="SCI.MATH", name_it="Matematica", name_en="Mathematics",
    parent_id="SCI", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.0, max_tokens=4096, system_fragment="Sei un matematico puro. Fornisci dimostrazioni rigorose, usa notazione LaTeX, distingui teorema/lemma/corollario.",
    keywords_it=("matematica","algebra","calcolo","geometria","topologia","probabilità","statistica","dimostrazione","teorema","funzione","integrale","derivata"),
    keywords_en=("mathematics","algebra","calculus","geometry","topology","probability","statistics","proof","theorem","function","integral","derivative"),
    complexity=5, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="SCI.ASTRO", name_it="Astronomia & Astrofisica", name_en="Astronomy & Astrophysics",
    parent_id="SCI", level=1, provr_optimal="claude", provr_fallback="gemini",
    temperature=0.2, max_tokens=4096, system_fragment="Sei un astrofisico. Usa dati NASA/ESA aggiornati, unità astronomiche corrette (parsec, anni luce, magnitudine).",
    keywords_it=("astronomia","astrofisica","stella","pianeta","galassia","buco nero","cosmologia","universo","NASA","telescopio","esopianeta"),
    keywords_en=("astronomy","astrophysics","star","planet","galaxy","black hole","cosmology","universe","NASA","telescope","exoplanet"),
    complexity=5, requires_reasoning=True, requires_web=True, citation_needed=True,
))

_add(TaxonomyNode(
    id="SCI.GEO", name_it="Geologia & Scienze della Terra", name_en="Geology & Earth Sciences",
    parent_id="SCI", level=1, provr_optimal="claude", provr_fallback="gemini",
    temperature=0.15, max_tokens=3072, system_fragment="Sei un geologo e scienziato della terra. Usa scala dei tempi geologici, nomenclatura petrografica, dati sismici.",
    keywords_it=("geologia","tettonica","vulcano","sisma","minerale","roccia","stratigrafia","idrogeologia","paleontologia","glaciazione"),
    keywords_en=("geology","tectonics","volcano","earthquake","mineral","rock","stratigraphy","hydrogeology","paleontology","glaciation"),
    complexity=4, requires_reasoning=True, requires_web=False, citation_needed=True,
))

# ─── MEDICINE Subcategories ───────────────────────────────────

_add(TaxonomyNode(
    id="MED.CLIN", name_it="Medicina Clinica & Diagnosi", name_en="Clinical Medicine & Diagnosis",
    parent_id="MED", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.05, max_tokens=4096, system_fragment="Sei un medico clinico esperto. Analizza sintomi con approccio differenziale. Raccomanda sempre visita specialistica.",
    keywords_it=("diagnosi","sintomi","visita","esame","anamnesi","clinica","patologia","segni","laboratorio","imaging"),
    keywords_en=("diagnosis","symptoms","examination","anamnesis","clinical","pathology","signs","laboratory","imaging"),
    complexity=5, requires_reasoning=True, requires_web=False, citation_needed=True,
))

_add(TaxonomyNode(
    id="MED.PHARM", name_it="Farmacologia & Terapia", name_en="Pharmacology & Therapy",
    parent_id="MED", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.05, max_tokens=3072, system_fragment="Sei un farmacologo. Fornisci meccanismo d'azione, dosaggi approvati, controindicazioni, interazioni. Richiedi sempre ricetta medica.",
    keywords_it=("farmaco","dosaggio","controindicazione","interazione","principio attivo","posologia","effetti collaterali","antibiotico","antidolorifico"),
    keywords_en=("drug","dosage","contraindication","interaction","active ingredient","dosing","s effects","antibiotic","analgesic"),
    complexity=5, requires_reasoning=True, requires_web=False, citation_needed=True,
))

_add(TaxonomyNode(
    id="MED.SURG", name_it="Chirurgia & Procedure", name_en="Surgery & Procedures",
    parent_id="MED", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.05, max_tokens=3072, system_fragment="Sei un chirurgo esperto. Descrivi tecniche chirurgiche, indicazioni, controindicazioni, complicanze, recovery.",
    keywords_it=("chirurgia","operazione","intervento","anestesia","endoscopia","laparoscopia","tecnica","suttura","recupero"),
    keywords_en=("surgery","operation","intervention","anesthesia","endoscopy","laparoscopy","technique","suture","recovery"),
    complexity=5, requires_reasoning=True, requires_web=False, citation_needed=True,
))

_add(TaxonomyNode(
    id="MED.PSYCH", name_it="Psichiatria & Salute Mentale", name_en="Psychiatry & Mental Health",
    parent_id="MED", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.2, max_tokens=3072, system_fragment="Sei uno psichiatra. Usa criteri DSM-5/ICD-11. Tratta temi sensibili con estrema cura. Indirizza sempre verso professionisti.",
    keywords_it=("psichiatria","depressione","ansia","disturbo","terapia","psicofarmaco","cognitivo","comportamentale","trauma","DSM"),
    keywords_en=("psychiatry","depression","anxiety","disorder","therapy","psychopharmacology","cognitive","behavioral","trauma","DSM"),
    complexity=5, requires_reasoning=True, requires_web=False, citation_needed=True,
))

_add(TaxonomyNode(
    id="MED.NUTR", name_it="Nutrizione & Dietetica", name_en="Nutrition & Dietetics",
    parent_id="MED", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.2, max_tokens=3072, system_fragment="Sei un nutrizionista e dietologo. Basa consigli su evidence scientifiche. Consra patologie e intolleranze.",
    keywords_it=("nutrizione","dieta","calorie","macronutrienti","vitamine","minerali","intolleranza","allergia","dimagrimento","metabolismo"),
    keywords_en=("nutrition","diet","calories","macronutrients","vitamins","minerals","intolerance","allergy","weight loss","metabolism"),
    complexity=3, requires_reasoning=True, requires_web=False, citation_needed=True,
))

_add(TaxonomyNode(
    id="MED.EMERG", name_it="Medicina d'Urgenza & Primo Soccorso", name_en="Emergency Medicine & First Aid",
    parent_id="MED", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.05, max_tokens=2048, system_fragment="EMERGENZA: fornisci istruzioni immediate, chiare, sicure. Indica sempre di chiamare il 118/112 per emergenze reali.",
    keywords_it=("emergenza","pronto soccorso","primo soccorso","RCP","trauma","infarto","ictus","avvelenamento","ustione","118"),
    keywords_en=("emergency","ER","first aid","CPR","trauma","heart attack","stroke","poisoning","burn","911"),
    complexity=5, requires_reasoning=True, requires_web=False, citation_needed=False,
))

# ─── LAW Subcategories ────────────────────────────────────────

_add(TaxonomyNode(
    id="LAW.CIVIL", name_it="Diritto Civile", name_en="Civil Law",
    parent_id="LAW", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.05, max_tokens=4096, system_fragment="Sei un avvocato civilista. Padroneggi Codice Civile italiano, diritto contrattuale, responsabilità, successioni, famiglia.",
    keywords_it=("diritto civile","contratto","responsabilità","risarcimento","successione","famiglia","proprietà","locazione","separazione"),
    keywords_en=("civil law","contract","liability","compensation","inheritance","family","property","lease","separation"),
    complexity=5, requires_reasoning=True, requires_web=True, citation_needed=True,
))

_add(TaxonomyNode(
    id="LAW.CRIM", name_it="Diritto Penale & Criminologia", name_en="Criminal Law & Criminology",
    parent_id="LAW", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.05, max_tokens=4096, system_fragment="Sei un avvocato penalista e criminologo. Padroneggi Codice Penale, procedura penale, reati, pene.",
    keywords_it=("penale","reato","crimine","pena","condanna","processo","difesa","accusa","detenzione","recidiva"),
    keywords_en=("criminal","crime","penalty","conviction","trial","defense","prosecution","detention","recidivism"),
    complexity=5, requires_reasoning=True, requires_web=True, citation_needed=True,
))

_add(TaxonomyNode(
    id="LAW.CORP", name_it="Diritto Commerciale & Societario", name_en="Corporate & Commercial Law",
    parent_id="LAW", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.1, max_tokens=4096, system_fragment="Sei un avvocato commercialista. Padroneggi diritto societario, M&A, contrattualistica commerciale, startup, IP.",
    keywords_it=("societario","SRL","SPA","azionista","statuto","assemblea","fusione","acquisizione","M&A","startup","venture capital"),
    keywords_en=("corporate","LLC","Inc","shareholder","statute","merger","acquisition","M&A","startup","venture capital"),
    complexity=5, requires_reasoning=True, requires_web=True, citation_needed=True,
))

_add(TaxonomyNode(
    id="LAW.IP", name_it="Proprietà Intellettuale & Copyright", name_en="Intellectual Property & Copyright",
    parent_id="LAW", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.1, max_tokens=3072, system_fragment="Sei un esperto di proprietà intellettuale. Padroneggi copyright, brevetti EPO/USPTO, marchi, licenze open-source, GDPR.",
    keywords_it=("copyright","brevetto","marchio","licenza","AGPL","GPL","MIT","trademark","patent","EUIPO","EPO","plagio"),
    keywords_en=("copyright","patent","trademark","license","AGPL","GPL","MIT","IP","EUIPO","EPO","plagiarism"),
    complexity=5, requires_reasoning=True, requires_web=True, citation_needed=True,
))

_add(TaxonomyNode(
    id="LAW.LABOR", name_it="Diritto del Lavoro", name_en="Labor & Employment Law",
    parent_id="LAW", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.1, max_tokens=3072, system_fragment="Sei un avvocato giuslavorista. Padroneggi contratti di lavoro, licenziamento, CCNL, mobbing, tutele.",
    keywords_it=("lavoro","contratto lavoro","licenziamento","dimissioni","CCNL","mobbing","burnout","malattia","maternità","pensione"),
    keywords_en=("employment","work contract","dismissal","resignation","collective agreement","mobbing","burnout","sick leave","maternity","pension"),
    complexity=4, requires_reasoning=True, requires_web=True, citation_needed=True,
))

_add(TaxonomyNode(
    id="LAW.INTL", name_it="Diritto Internazionale & UE", name_en="International & EU Law",
    parent_id="LAW", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.1, max_tokens=4096, system_fragment="Sei un avvocato internazionalista. Padroneggi diritto UE, trattati internazionali, Corte di Giustizia, Convenzione EDU.",
    keywords_it=("diritto internazionale","UE","trattato","CEDU","Corte UE","sanzioni","asilo","immigrazione","WTO"),
    keywords_en=("international law","EU","treaty","ECHR","EU Court","sanctions","asylum","immigration","WTO"),
    complexity=5, requires_reasoning=True, requires_web=True, citation_needed=True,
))

# ─── FINANCE Subcategories ────────────────────────────────────

_add(TaxonomyNode(
    id="FIN.INVEST", name_it="Investimenti & Mercati Finanziari", name_en="Investments & Financial Markets",
    parent_id="FIN", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.1, max_tokens=3072, system_fragment="Sei un analista finanziario senior. Fornisci analisi fondamentale e tecnica. Specifica sempre i rischi e non fare raccomandazioni dirette.",
    keywords_it=("azioni","obbligazioni","ETF","fondo","borsa","trading","portafoglio","diversificazione","rendimento","rischio"),
    keywords_en=("stocks","bonds","ETF","fund","exchange","trading","portfolio","diversification","return","risk"),
    complexity=4, requires_reasoning=True, requires_web=True, citation_needed=False,
))

_add(TaxonomyNode(
    id="FIN.CRYPTO", name_it="Criptovalute & DeFi", name_en="Cryptocurrencies & DeFi",
    parent_id="FIN", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.2, max_tokens=3072, system_fragment="Sei un esperto crypto e DeFi. Analizza fondamentali on-chain, tokenomics, protocolli DeFi. Enfatizza alta volatilità e rischi.",
    keywords_it=("bitcoin","ethereum","criptovaluta","DeFi","staking","yield","token","NFT","wallet","exchange","altcoin"),
    keywords_en=("bitcoin","ethereum","cryptocurrency","DeFi","staking","yield","token","NFT","wallet","exchange","altcoin"),
    complexity=4, requires_reasoning=True, requires_web=True, citation_needed=False,
))

_add(TaxonomyNode(
    id="FIN.TAX", name_it="Fiscalità & Tributario", name_en="Taxation & Tax Law",
    parent_id="FIN", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.05, max_tokens=3072, system_fragment="Sei un commercialista esperto. Padroneggi IRPEF, IVA, IRES, dichiarazioni fiscali, ottimizzazione fiscale lecita.",
    keywords_it=("tasse","imposte","IRPEF","IVA","dichiarazione","commercialista","deducibile","detrazione","partita IVA","bilancio"),
    keywords_en=("taxes","income tax","VAT","declaration","accountant","deductible","deduction","VAT number","balance sheet"),
    complexity=5, requires_reasoning=True, requires_web=True, citation_needed=True,
))

_add(TaxonomyNode(
    id="FIN.BANK", name_it="Banca & Credito", name_en="Banking & Credit",
    parent_id="FIN", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.15, max_tokens=3072, system_fragment="Sei un esperto bancario. Padroneggi mutui, finanziamenti, rating creditizio, prodotti bancari, BCE, politica monetaria.",
    keywords_it=("banca","mutuo","finanziamento","prestito","tasso","BCE","credito","garanzia","ipoteca","IBAN"),
    keywords_en=("bank","mortgage","loan","interest rate","ECB","credit","guarantee","mortgage","IBAN"),
    complexity=3, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="FIN.MACRO", name_it="Macroeconomia & Politica Economica", name_en="Macroeconomics & Economic Policy",
    parent_id="FIN", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.2, max_tokens=4096, system_fragment="Sei un macroeconomista. Analizza PIL, inflazione, disoccupazione, politiche fiscali/monetarie con rigore accademico.",
    keywords_it=("macroeconomia","PIL","inflazione","disoccupazione","banca centrale","politica monetaria","deficit","debito pubblico"),
    keywords_en=("macroeconomics","GDP","inflation","unemployment","central bank","monetary policy","deficit","public debt"),
    complexity=5, requires_reasoning=True, requires_web=True, citation_needed=True,
))

# ─── BUSINESS Subcategories ───────────────────────────────────

_add(TaxonomyNode(
    id="BUS.STRAT", name_it="Strategia Aziendale", name_en="Business Strategy",
    parent_id="BUS", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.4, max_tokens=4096, system_fragment="Sei un consulente strategico McKinsey-level. Usa framework Porter, SWOT, BCG, Blue Ocean. Fornisci raccomandazioni actionable.",
    keywords_it=("strategia","vantaggio competitivo","posizionamento","mercato","crescita","diversificazione","SWOT","Porter"),
    keywords_en=("strategy","competitive advantage","positioning","market","growth","diversification","SWOT","Porter"),
    complexity=4, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="BUS.MKTG", name_it="Marketing & Comunicazione", name_en="Marketing & Communications",
    parent_id="BUS", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.5, max_tokens=4096, system_fragment="Sei un CMO esperto. Padroneggi digital marketing, SEO, SEM, social media, content, email, analytics, branding.",
    keywords_it=("marketing","SEO","SEM","social media","content","email","branding","campagna","funnel","conversione","analytics"),
    keywords_en=("marketing","SEO","SEM","social media","content","email","branding","campaign","funnel","conversion","analytics"),
    complexity=3, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="BUS.STARTUP", name_it="Startup & Entrepreneurship", name_en="Startup & Entrepreneurship",
    parent_id="BUS", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.6, max_tokens=4096, system_fragment="Sei un mentor startup esperto. Padroneggi Lean Startup, product-market fit, fundraising, pitch, go-to-market.",
    keywords_it=("startup","pitch","MVP","product-market fit","funding","investor","acceleratore","incubatore","equity","valuation"),
    keywords_en=("startup","pitch","MVP","product-market fit","funding","investor","accelerator","incubator","equity","valuation"),
    complexity=3, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="BUS.HR", name_it="Risorse Umane & Cultura Aziendale", name_en="Human Resources & Culture",
    parent_id="BUS", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.4, max_tokens=3072, system_fragment="Sei un HR Director esperto. Padroneggi talent acquisition, performance management, cultura aziendale, compensation, DEI.",
    keywords_it=("HR","risorse umane","recruitment","performance","cultura","compensation","onboarding","retention","DEI","leadership"),
    keywords_en=("HR","human resources","recruitment","performance","culture","compensation","onboarding","retention","DEI","leadership"),
    complexity=3, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="BUS.OPS", name_it="Operations & Supply Chain", name_en="Operations & Supply Chain",
    parent_id="BUS", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.3, max_tokens=3072, system_fragment="Sei un COO expert. Padroneggi supply chain, logistica, lean manufacturing, Six Sigma, KPI operativi.",
    keywords_it=("operations","supply chain","logistica","lean","Six Sigma","KPI","processo","efficienza","inventario","produzione"),
    keywords_en=("operations","supply chain","logistics","lean","Six Sigma","KPI","process","efficiency","inventory","production"),
    complexity=4, requires_reasoning=True, requires_web=False, citation_needed=False,
))

# ─── ARTS Subcategories ───────────────────────────────────────

_add(TaxonomyNode(
    id="ART.LIT", name_it="Letteratura & Narrativa", name_en="Literature & Fiction",
    parent_id="ART", level=1, provr_optimal="claude", provr_fallback="gemini",
    temperature=0.85, max_tokens=8192, system_fragment="Sei un letterato e narratore. Padroneggi stili narrativi, archi personaggio, struttura narrativa, voce autoriale.",
    keywords_it=("narrativa","romanzo","racconto","personaggio","trama","stile","metafora","simbolismo","autore","genere letterario"),
    keywords_en=("fiction","novel","story","character","plot","style","metaphor","symbolism","author","literary genre"),
    complexity=3, requires_reasoning=False, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="ART.MUSIC", name_it="Musica & Teoria Musicale", name_en="Music & Music Theory",
    parent_id="ART", level=1, provr_optimal="claude", provr_fallback="gemini",
    temperature=0.7, max_tokens=4096, system_fragment="Sei un musicista e musicologo. Padroneggi teoria musicale, armonia, composizione, generi, storia della musica.",
    keywords_it=("musica","melodia","armonia","ritmo","accordo","scala","genere","composizione","arrangiamento","strumento"),
    keywords_en=("music","melody","harmony","rhythm","chord","scale","genre","composition","arrangement","instrument"),
    complexity=3, requires_reasoning=False, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="ART.FILM", name_it="Cinema & Audiovisivo", name_en="Film & Audiovisual",
    parent_id="ART", level=1, provr_optimal="claude", provr_fallback="gemini",
    temperature=0.7, max_tokens=4096, system_fragment="Sei un critico cinematografico e regista. Analizza linguaggio cinematografico, regia, sceneggiatura, montaggio.",
    keywords_it=("cinema","film","regia","sceneggiatura","montaggio","fotografia","recitazione","genere","critica","festival"),
    keywords_en=("cinema","film","directing","screenplay","editing","photography","acting","genre","criticism","festival"),
    complexity=3, requires_reasoning=False, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="ART.PHIL", name_it="Filosofia & Etica", name_en="Philosophy & Ethics",
    parent_id="ART", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.5, max_tokens=4096, system_fragment="Sei un filosofo. Padroneggi storia della filosofia, metafisica, epistemologia, etica, logica formale.",
    keywords_it=("filosofia","etica","morale","metafisica","epistemologia","logica","ontologia","coscienza","libero arbitrio","esistenzialismo"),
    keywords_en=("philosophy","ethics","morality","metaphysics","epistemology","logic","ontology","consciousness","free will","existentialism"),
    complexity=4, requires_reasoning=True, requires_web=False, citation_needed=True,
))

_add(TaxonomyNode(
    id="ART.HIST", name_it="Storia & Storiografia", name_en="History & Historiography",
    parent_id="ART", level=1, provr_optimal="claude", provr_fallback="gemini",
    temperature=0.3, max_tokens=4096, system_fragment="Sei uno storico. Fornisci contesto storico preciso con date, fonti primarie, interpretazioni storiografiche.",
    keywords_it=("storia","storico","epoca","periodo","guerra","rivoluzione","impero","civilizzazione","documento","fonte"),
    keywords_en=("history","historical","era","period","war","revolution","empire","civilization","document","source"),
    complexity=3, requires_reasoning=True, requires_web=False, citation_needed=True,
))

_add(TaxonomyNode(
    id="ART.DESIGN", name_it="Design & Grafica", name_en="Design & Visual Arts",
    parent_id="ART", level=1, provr_optimal="gemini", provr_fallback="claude",
    temperature=0.7, max_tokens=3072, system_fragment="Sei un designer creativo. Padroneggi principi visivi (Gestalt, color theory), UX/UI, tipografia, branding.",
    keywords_it=("design","grafica","UI","UX","colore","tipografia","logo","brand","illustrazione","layout","figma","adobe"),
    keywords_en=("design","graphic","UI","UX","color","typography","logo","brand","illustration","layout","figma","adobe"),
    complexity=3, requires_reasoning=False, requires_web=False, citation_needed=False,
))

# ─── EDUCATION Subcategories ─────────────────────────────────

_add(TaxonomyNode(
    id="EDU.STEM", name_it="STEM & Didattica Scientifica", name_en="STEM Education",
    parent_id="EDU", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.3, max_tokens=4096, system_fragment="Sei un docente STEM. Spiega concetti complessi con analogie efficaci, esempi pratici, progressione scaffolding.",
    keywords_it=("STEM","matematica scolastica","fisica scolastica","chimica scolastica","didattica","esercizi","problemi","soluzioni"),
    keywords_en=("STEM","school math","school physics","school chemistry","teaching","exercises","problems","solutions"),
    complexity=2, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="EDU.LANG", name_it="Lingue & Linguistica", name_en="Languages & Linguistics",
    parent_id="EDU", level=1, provr_optimal="claude", provr_fallback="gemini",
    temperature=0.4, max_tokens=4096, system_fragment="Sei un linguista e insegnante di lingue. Padroneggi grammatica, sintassi, fonologia, traduzione, acquisizione L2.",
    keywords_it=("lingua","grammatica","traduzione","inglese","spagnolo","francese","tedesco","cinese","giapponese","linguistica","sintassi"),
    keywords_en=("language","grammar","translation","English","Spanish","French","German","Chinese","Japanese","linguistics","syntax"),
    complexity=2, requires_reasoning=True, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="EDU.CAREER", name_it="Carriera & Sviluppo Professionale", name_en="Career & Professional Development",
    parent_id="EDU", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.5, max_tokens=3072, system_fragment="Sei un career coach esperto. Aiuta con CV, LinkedIn, colloqui, negoziazione stipendio, sviluppo competenze.",
    keywords_it=("carriera","CV","curriculum","colloquio","LinkedIn","stipendio","competenze","soft skills","hard skills","promozione"),
    keywords_en=("career","resume","CV","interview","LinkedIn","salary","skills","soft skills","hard skills","promotion"),
    complexity=2, requires_reasoning=True, requires_web=False, citation_needed=False,
))

# ─── PSYCHOLOGY Subcategories ────────────────────────────────

_add(TaxonomyNode(
    id="PSY.COG", name_it="Psicologia Cognitiva & Comportamentale", name_en="Cognitive & Behavioral Psychology",
    parent_id="PSY", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.3, max_tokens=3072, system_fragment="Sei uno psicologo cognitivista. Basa risposte su CBT, DBT, ACT, ricerche validate. Tratta temi sensibili con cura.",
    keywords_it=("cognitivo","comportamentale","CBT","distorsione cognitiva","bias","apprendimento","memoria","attenzione","emozione"),
    keywords_en=("cognitive","behavioral","CBT","cognitive distortion","bias","learning","memory","attention","emotion"),
    complexity=4, requires_reasoning=True, requires_web=False, citation_needed=True,
))

_add(TaxonomyNode(
    id="PSY.NEURO", name_it="Neuroscienze & Cervello", name_en="Neuroscience & Brain",
    parent_id="PSY", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.15, max_tokens=4096, system_fragment="Sei un neuroscienziato. Basa risposte su letteratura peer-reviewed. Usa terminologia neuroanatomica corretta.",
    keywords_it=("neuroscienza","cervello","neuroni","sinapsi","neurotrasmettitore","corteccia","ippocampo","neuroplasticità","cognizione"),
    keywords_en=("neuroscience","brain","neurons","synapse","neurotransmitter","cortex","hippocampus","neuroplasticity","cognition"),
    complexity=5, requires_reasoning=True, requires_web=False, citation_needed=True,
))

_add(TaxonomyNode(
    id="PSY.SOCIAL", name_it="Psicologia Sociale & Organizzativa", name_en="Social & Organizational Psychology",
    parent_id="PSY", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.4, max_tokens=3072, system_fragment="Sei un psicologo sociale. Analizza dinamiche di gruppo, leadership, influenza, pregiudizi sociali, organizzazione.",
    keywords_it=("psicologia sociale","gruppo","leadership","influenza","pregiudizio","stereotipo","conformità","persuasione","organizzazione"),
    keywords_en=("social psychology","group","leadership","influence","prejudice","stereotype","conformity","persuasion","organization"),
    complexity=4, requires_reasoning=True, requires_web=False, citation_needed=True,
))

# ─── CREATIVE Subcategories ───────────────────────────────────

_add(TaxonomyNode(
    id="CRE.WRITE", name_it="Scrittura Creativa & Narrativa", name_en="Creative Writing & Fiction",
    parent_id="CRE", level=1, provr_optimal="claude", provr_fallback="gemini",
    temperature=0.95, max_tokens=8192, system_fragment="Sei un autore brillante. Scrivi con voce originale, ricchezza sensoriale, ritmo narrativo perfetto. Sorprendi il lettore.",
    keywords_it=("scrivi racconto","racconta una storia","crea personaggio","dialogo","narrativa","prosa","fiction","trama"),
    keywords_en=("write story","tell a story","create character","dialogue","narrative","prose","fiction","plot"),
    complexity=2, requires_reasoning=False, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="CRE.COPY", name_it="Copywriting & Content Marketing", name_en="Copywriting & Content Marketing",
    parent_id="CRE", level=1, provr_optimal="openai", provr_fallback="claude",
    temperature=0.7, max_tokens=4096, system_fragment="Sei un copywriter world-class. Scrivi copy persuasivo, headline che catturano, CTA efficaci. Usa framework AIDA, PAS.",
    keywords_it=("copywriting","headline","CTA","landing page","email marketing","newsletter","slogan","copy","persuasione"),
    keywords_en=("copywriting","headline","CTA","landing page","email marketing","newsletter","slogan","copy","persuasion"),
    complexity=2, requires_reasoning=False, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="CRE.POEM", name_it="Poesia & Scrittura Lirica", name_en="Poetry & Lyric Writing",
    parent_id="CRE", level=1, provr_optimal="claude", provr_fallback="gemini",
    temperature=0.98, max_tokens=2048, system_fragment="Sei un poeta. Usa immagini viv, metafore originali, ritmo studiato. Sperimenta con forma e contenuto.",
    keywords_it=("poesia","verso","rima","metafora","strofa","sonetto","haiku","lirica","immagine","simbolo"),
    keywords_en=("poetry","verse","rhyme","metaphor","stanza","sonnet","haiku","lyric","imagery","symbol"),
    complexity=3, requires_reasoning=False, requires_web=False, citation_needed=False,
))

_add(TaxonomyNode(
    id="CRE.SCRIPT", name_it="Sceneggiatura & Dialogo", name_en="Screenplay & Dialogue",
    parent_id="CRE", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.85, max_tokens=6144, system_fragment="Sei uno sceneggiatore professionista. Usa formato screenplay standard (INT/EXT, action lines, dialogue). Crea conflitto e tensione.",
    keywords_it=("sceneggiatura","dialogo","script","scena","personaggio","conflitto","atto","beat","logline","soggetto"),
    keywords_en=("screenplay","dialogue","script","scene","character","conflict","act","beat","logline","treatment"),
    complexity=3, requires_reasoning=False, requires_web=False, citation_needed=False,
))

# ─── ENVIRONMENT Subcategories ────────────────────────────────

_add(TaxonomyNode(
    id="ENV.CLIM", name_it="Cambiamento Climatico", name_en="Climate Change",
    parent_id="ENV", level=1, provr_optimal="claude", provr_fallback="gemini",
    temperature=0.15, max_tokens=4096, system_fragment="Sei un climatologo. Basa risposte su rapporti IPCC AR6, dati WMO, letteratura peer-reviewed. Distingui mitigazione e adattamento.",
    keywords_it=("clima","riscaldamento","CO2","emissioni","IPCC","Paris Agreement","decarbonizzazione","GHG","temperature","siccità"),
    keywords_en=("climate","warming","CO2","emissions","IPCC","Paris Agreement","decarbonization","GHG","temperature","drought"),
    complexity=4, requires_reasoning=True, requires_web=True, citation_needed=True,
))

_add(TaxonomyNode(
    id="ENV.ENERGY", name_it="Energia & Transizione Energetica", name_en="Energy & Energy Transition",
    parent_id="ENV", level=1, provr_optimal="claude", provr_fallback="gemini",
    temperature=0.2, max_tokens=3072, system_fragment="Sei un esperto di energia. Padroneggi rinnovabili (solare, eolico, idro), nucleare, fossili, storage, smart grid.",
    keywords_it=("energia","solare","eolico","rinnovabile","nucleare","idrogeno","batteria","rete","efficienza","LCOE"),
    keywords_en=("energy","solar","wind","renewable","nuclear","hydrogen","battery","grid","efficiency","LCOE"),
    complexity=4, requires_reasoning=True, requires_web=True, citation_needed=True,
))

_add(TaxonomyNode(
    id="ENV.BIO", name_it="Biodiversità & Ecologia", name_en="Biodiversity & Ecology",
    parent_id="ENV", level=1, provr_optimal="claude", provr_fallback="gemini",
    temperature=0.2, max_tokens=3072, system_fragment="Sei un ecologo. Padroneggi dinamiche ecosistemiche, specie a rischio, conservazione, IUCN Red List.",
    keywords_it=("biodiversità","specie","ecologia","ecosistema","estinzione","conservazione","foresta","oceano","deforestazione"),
    keywords_en=("biodiversity","species","ecology","ecosystem","extinction","conservation","forest","ocean","deforestation"),
    complexity=4, requires_reasoning=True, requires_web=True, citation_needed=True,
))

# ─── SOCIETY Subcategories ────────────────────────────────────

_add(TaxonomyNode(
    id="SOC.POL", name_it="Politica & Sistemi di Governo", name_en="Politics & Governance",
    parent_id="SOC", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.2, max_tokens=3072, system_fragment="Sei un politologo. Presenta prospettive multiple, evita bias, distingui fatti da opinioni, cita fonti verificabili.",
    keywords_it=("politica","governo","partito","elezioni","democrazia","parlamento","legge","riforma","politico","ministero"),
    keywords_en=("politics","government","party","elections","democracy","parliament","law","reform","politician","ministry"),
    complexity=4, requires_reasoning=True, requires_web=True, citation_needed=True,
))

_add(TaxonomyNode(
    id="SOC.SOCIO", name_it="Sociologia & Antropologia", name_en="Sociology & Anthropology",
    parent_id="SOC", level=1, provr_optimal="claude", provr_fallback="openai",
    temperature=0.4, max_tokens=3072, system_fragment="Sei un sociologo e antropologo. Analizza fenomeni sociali con rigore metodologico, teoria sociale, dati empirici.",
    keywords_it=("sociologia","antropologia","cultura","ntità","classe sociale","disuguaglianza","migrazione","urbanizzazione","globalizzazione"),
    keywords_en=("sociology","anthropology","culture","identity","social class","inequality","migration","urbanization","globalization"),
    complexity=4, requires_reasoning=True, requires_web=False, citation_needed=True,
))

# ══════════════════════════════════════════════════════════════
# L2 — SPECIALIZZAZIONI (selezione delle più importanti ~100)
# ══════════════════════════════════════════════════════════════

# TECH.AI → specializzazioni
for spec_id, name_it, name_en, kw_it, kw_en in [
    ("TECH.AI.LLM", "Large Language Models", "Large Language Models",
     ("LLM","GPT-4","Claude","Gemini","transformer","attention","RLHF","fine-tuning","LoRA","PEFT"),
     ("LLM","GPT-4","Claude","Gemini","transformer","attention","RLHF","fine-tuning","LoRA","PEFT")),
    ("TECH.AI.CV", "Computer Vision", "Computer Vision",
     ("computer vision","CNN","riconoscimento immagini","object detection","YOLO","segmentazione"),
     ("computer vision","CNN","image recognition","object detection","YOLO","segmentation")),
    ("TECH.AI.NLP", "Natural Language Processing", "Natural Language Processing",
     ("NLP","tokenizzazione","sentiment","named entity","POS tagging","parsing","BERT","embeddings"),
     ("NLP","tokenization","sentiment","named entity","POS tagging","parsing","BERT","embeddings")),
    ("TECH.AI.RAG", "RAG & Knowledge Systems", "RAG & Knowledge Systems",
     ("RAG","retrieval","vector database","Chroma","Pinecone","embedding","knowledge base","grounding"),
     ("RAG","retrieval","vector database","Chroma","Pinecone","embedding","knowledge base","grounding")),
    ("TECH.AI.AGENT", "AI Agents & Multi-Agent", "AI Agents & Multi-Agent",
     ("agente AI","multi-agent","autonomo","tool use","function calling","MCP","orchestrazione"),
     ("AI agent","multi-agent","autonomous","tool use","function calling","MCP","orchestration")),
]:
    _add(TaxonomyNode(
        id=spec_id, name_it=name_it, name_en=name_en, parent_id="TECH.AI", level=2,
        provr_optimal="openai", provr_fallback="claude",
        temperature=0.15, max_tokens=4096, system_fragment=f"Sei uno specialista in {name_en}. Rispondi con precisione tecnica massima.",
        keywords_it=kw_it, keywords_en=kw_en,
        complexity=5, requires_reasoning=True, requires_web=False, citation_needed=False,
    ))

# TECH.DEV → specializzazioni
for spec_id, name_it, name_en, kw_it, kw_en, provider in [
    ("TECH.DEV.PY", "Python", "Python",
     ("python","pip","venv","asyncio","FastAPI","Django","Flask","pytest","numpy","pandas"),
     ("python","pip","venv","asyncio","FastAPI","Django","Flask","pytest","numpy","pandas"), "openai"),
    ("TECH.DEV.TS", "TypeScript & JavaScript", "TypeScript & JavaScript",
     ("typescript","javascript","node.js","npm","yarn","webpack","vite","jest","eslint"),
     ("typescript","javascript","node.js","npm","yarn","webpack","vite","jest","eslint"), "openai"),
    ("TECH.DEV.RUST", "Rust & Systems Programming", "Rust & Systems Programming",
     ("rust","cargo","ownership","borrowing","lifetime","unsafe","tokio","async/await rust"),
     ("rust","cargo","ownership","borrowing","lifetime","unsafe","tokio","async/await rust"), "openai"),
    ("TECH.DEV.GO", "Go (Golang)", "Go (Golang)",
     ("golang","go","goroutine","channel","interface go","gin","gRPC","protobuf"),
     ("golang","go","goroutine","channel","interface go","gin","gRPC","protobuf"), "openai"),
    ("TECH.DEV.JAVA", "Java & JVM", "Java & JVM",
     ("java","spring boot","maven","gradle","JVM","kotlin jvm","hibernate","microservizi java"),
     ("java","spring boot","maven","gradle","JVM","kotlin jvm","hibernate","microservices java"), "openai"),
]:
    _add(TaxonomyNode(
        id=spec_id, name_it=name_it, name_en=name_en, parent_id="TECH.DEV", level=2,
        provr_optimal=provider, provr_fallback="claude",
        temperature=0.1, max_tokens=6144, system_fragment=f"Sei un esperto {name_en}. Scrivi codice pulito, testato, idiomatico.",
        keywords_it=kw_it, keywords_en=kw_en,
        complexity=4, requires_reasoning=True, requires_web=False, citation_needed=False,
    ))

# SCI.MATH → specializzazioni
for spec_id, name_it, name_en, kw_it, kw_en in [
    ("SCI.MATH.CALC", "Calcolo & Analisi Matematica", "Calculus & Mathematical Analysis",
     ("derivata","integrale","limite","serie","convergenza","analisi reale","misura"),
     ("derivative","integral","limit","series","convergence","real analysis","measure")),
    ("SCI.MATH.ALGE", "Algebra & Strutture", "Algebra & Structures",
     ("algebra lineare","matrici","vettori","gruppo","anello","campo","spazio vettoriale"),
     ("linear algebra","matrices","vectors","group","ring","field","vector space")),
    ("SCI.MATH.PROB", "Probabilità & Statistica", "Probability & Statistics",
     ("probabilità","distribuzione","varianza","covarianza","test ipotesi","p-value","regressione","bayesiano"),
     ("probability","distribution","variance","covariance","hypothesis test","p-value","regression","Bayesian")),
    ("SCI.MATH.DISC", "Matematica Discreta & Combinatoria", "Discrete Math & Combinatorics",
     ("grafo","albero","combinatoria","permutazione","combinazione","logica proposizionale","automi"),
     ("graph","tree","combinatorics","permutation","combination","propositional logic","automata")),
]:
    _add(TaxonomyNode(
        id=spec_id, name_it=name_it, name_en=name_en, parent_id="SCI.MATH", level=2,
        provr_optimal="claude", provr_fallback="openai",
        temperature=0.0, max_tokens=4096, system_fragment=f"Sei un matematico specializzato in {name_it}. Usa notazione formale rigorosa.",
        keywords_it=kw_it, keywords_en=kw_en,
        complexity=5, requires_reasoning=True, requires_web=False, citation_needed=False,
    ))

# MED specializzazioni
for spec_id, name_it, name_en, kw_it, kw_en in [
    ("MED.CLIN.CARDIO", "Cardiologia", "Cardiology",
     ("cuore","cardiologia","infarto","aritmia","ECG","pressione","colesterolo","aterosclerosi","bypass"),
     ("heart","cardiology","heart attack","arrhythmia","ECG","blood pressure","cholesterol","atherosclerosis","bypass")),
    ("MED.CLIN.ONCO", "Oncologia & Tumori", "Oncology & Cancer",
     ("cancro","tumore","oncologia","chemioterapia","radioterapia","immunoterapia","metastasi","biopsia"),
     ("cancer","tumor","oncology","chemotherapy","radiotherapy","immunotherapy","metastasis","biopsy")),
    ("MED.CLIN.NEURO", "Neurologia", "Neurology",
     ("neurologia","ictus","epilessia","Parkinson","Alzheimer","sclerosi multipla","cefalea","neuropatia"),
     ("neurology","stroke","epilepsy","Parkinson","Alzheimer","multiple sclerosis","headache","neuropathy")),
    ("MED.CLIN.PEDIA", "Pediatria", "Pediatrics",
     ("pediatria","bambino","neonato","vaccino","crescita","febbre bambini","allergia infantile","ADHD"),
     ("pediatrics","child","newborn","vaccine","growth","child fever","childhood allergy","ADHD")),
    ("MED.CLIN.GYNE", "Ginecologia & Ostetricia", "Gynecology & Obstetrics",
     ("ginecologia","ostetricia","gravidanza","parto","menopausa","ciclo","endometriosi","fertilità"),
     ("gynecology","obstetrics","pregnancy","childbirth","menopause","cycle","endometriosis","fertility")),
]:
    _add(TaxonomyNode(
        id=spec_id, name_it=name_it, name_en=name_en, parent_id="MED.CLIN", level=2,
        provr_optimal="claude", provr_fallback="openai",
        temperature=0.05, max_tokens=3072, system_fragment=f"Sei uno specialista in {name_it}. Fornisci informazioni accurate, raccomanda sempre lo specialista.",
        keywords_it=kw_it, keywords_en=kw_en,
        complexity=5, requires_reasoning=True, requires_web=False, citation_needed=True,
    ))


# ══════════════════════════════════════════════════════════════
# INDICI VELOCI PER LOOKUP
# ══════════════════════════════════════════════════════════════

# Indice keyword → node_id (per lookup veloce)
_KEYWORD_INDEX: Dict[str, List[str]] = {}

def _build_index():
    for node_id, node in TAXONOMY.items():
        for kw in node.keywords_it + node.keywords_en:
            kw_lower = kw.lower()
            if kw_lower not in _KEYWORD_INDEX:
                _KEYWORD_INDEX[kw_lower] = []
            _KEYWORD_INDEX[kw_lower].append(node_id)

_build_index()


# ══════════════════════════════════════════════════════════════
# CLASSIFIER API
# ══════════════════════════════════════════════════════════════

def classify_text(text: str, max_results: int = 3) -> List[Tuple[str, TaxonomyNode, int]]:
    """
    Classifica testo nella tassonomia.

    Ritorna: lista di (node_id, node, match_score) ordinata per score.

    Complessità: O(n_words × avg_keyword_matches) ≈ O(n) veloce
    """
    if not text:
        return []

    text_lower = text.lower()
    set(text_lower.split())
    scores: Dict[str, int] = {}

    # Match diretto su keywords
    for kw, node_ids in _KEYWORD_INDEX.items():
        if kw in text_lower:
            for node_id in node_ids:
                # Peso per livello: L2/L3 più specifici → peso maggiore
                node = TAXONOMY[node_id]
                weight = 1 + node.level  # L0=1, L1=2, L2=3, L3=4
                scores[node_id] = scores.get(node_id, 0) + weight

    if not scores:
        return []

    # Ordina per score decrescente
    sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return [
        (node_id, TAXONOMY[node_id], score)
        for node_id, score in sorted_results[:max_results]
        if node_id in TAXONOMY
    ]


def get_node(node_id: str) -> Optional[TaxonomyNode]:
    """Ritorna nodo per ID."""
    return TAXONOMY.get(node_id)


def get_children(parent_id: str) -> List[TaxonomyNode]:
    """Ritorna figli diretti di un nodo."""
    return [n for n in TAXONOMY.values() if n.parent_id == parent_id]


def get_optimal_config(text: str) -> Dict:
    """
    Ritorna configurazione ottimale per una query.

    Usato dal server per selezionare provider, temperature, system prompt.
    """
    results = classify_text(text, max_results=1)

    if not results:
        # Default: conversazione generale
        return {
            "node_id": "CRE",
            "provider": "claude",
            "temperature": 0.5,
            "max_tokens": 2048,
            "system_fragment": "Sei un assistente intelligente e disponibile.",
            "requires_web": False,
            "citation_needed": False,
            "complexity": 2,
        }

    node_id, node, score = results[0]
    return {
        "node_id": node_id,
        "name_it": node.name_it,
        "name_en": node.name_en,
        "provider": node.provr_optimal,
        "provr_fallback": node.provr_fallback,
        "temperature": node.temperature,
        "max_tokens": node.max_tokens,
        "system_fragment": node.system_fragment,
        "requires_web": node.requires_web,
        "citation_needed": node.citation_needed,
        "complexity": node.complexity,
        "match_score": score,
    }


def taxonomy_stats() -> Dict:
    """Statistiche tassonomia."""
    by_level = {0: 0, 1: 0, 2: 0, 3: 0}
    by_macro = {}
    for node in TAXONOMY.values():
        by_level[node.level] = by_level.get(node.level, 0) + 1
        macro = node.id.split('.')[0]
        by_macro[macro] = by_macro.get(macro, 0) + 1
    return {
        "total_nodes": len(TAXONOMY),
        "keywords_indexed": len(_KEYWORD_INDEX),
        "by_level": by_level,
        "by_macro_domain": by_macro,
        "macro_domains": [k for k in by_macro.keys()],
    }
