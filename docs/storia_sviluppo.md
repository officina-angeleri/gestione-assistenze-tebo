# Gestione Assistenze Tebo — Storia dello Sviluppo

> Documento centrale di tracciamento per il progetto **Gestione Assistenze Tebo**.
> Aggiornato: 20 Febbraio 2026 — **Versione 1.0**

---

## 1. Panoramica del Progetto

**Gestione Assistenze Tebo** (noto anche come "Sistema V5 Dinamico") è un'applicazione desktop per la gestione degli interventi tecnici di assistenza sui prodotti aziendali. Include funzionalità avanzate di "Esploso Tecnico" interattivo, permettendo la selezione visiva dei componenti direttamente dalle planimetrie/disegni tecnici.

| Elemento | Dettaglio |
|---|---|
| **Linguaggio** | Python 3 |
| **GUI Framework** | PySide6 (Qt) |
| **Database** | SQLite (locale, `gestione_assistenze.db`) |
| **ORM** | SQLAlchemy |
| **Repository** | `officina-angeleri/gestione-assistenze-tebo` (GitHub) |
| **Branch principale** | `main` |

---

## 2. Struttura del Progetto

```text
gestione-assistenze-tebo/
├── main.py              # Entry point, configurazione tema e avvio GUI
├── database.py          # Modelli SQLAlchemy (Intervento, ComponenteIntervento)
├── registry.py          # Logica gestione file sorgente (PDF, coordinate JSON, metadati)
├── .gitignore           # Esclusioni standard per Python/Venv
├── docs/
│   ├── storia_sviluppo.md   # Questo file
├── gui/
│   ├── main_window.py   # Finestra principale ed UI per i rapporti tecnici
│   └── map_viewer.py    # Modulo QGraphicsView avanzato per l'esploso interattivo
└── Disegni/             # Cartella contenente i disegni (PDF/PNG), e file dati .json
```

---

## 3. Gestione Dati e Coordinate (Registry)

Il progetto utilizza un approccio basato su file per i metadati dei componenti, accoppiato al database relazionale per le assistenze. Il modulo `registry.py` si occupa di scansionare la cartella `disegni/` alla ricerca di:
- **Disegni tecnici**: File PDF o PNG che rappresentano l'esploso del prodotto.
- **Dati componenti**: File `.data.json` che mappano il numero di posizione del componente al relativo `Codice` e `Descrizione`.
- **Coordinate**: File `.coords.json` salvati dal modulo di *Calibrazione* della GUI per mappare esattamente dove si trovano i singoli componenti sull'immagine dell'esploso.

---

## 4. Schema Database

### Tabella `interventi`
Tabella principale per i rapporti di assistenza tecnica.
- `id` (PK auto)
- `prodotto` (String): Sigla del prodotto (es. "VA50_500")
- `data` (DateTime): Data e ora dell'intervento
- `ore_lavoro` (Float): Tempo impiegato
- `note_tecniche` (Text): Dettagli sull'intervento
- `descrizione` (Text): Oggetto dell'intervento

### Tabella `componenti_intervento`
Tabella relazionale (1:N) che lega le parti sostituite al relativo intervento.
- `id` (PK auto)
- `intervento_id` (FK → interventi.id)
- `numero_componente` (Integer): Posizione sull'esploso
- `codice_componente` (String)
- `descrizione_componente` (String)
- `quantita` (Float)
- `sostituito` (Boolean)
- `note` (String)

---

## 5. Funzionalità Implementate (v1.0)

- [x] **Gestione Interventi**: Elenco cronologico interventi filtrabili per prodotto con interfaccia utente principale `MainWindow`.
- [x] **Rapporto Tecnico interattivo**: Finestra `NewInterventionDialog` divisa in form di testo a sinistra ed esploso a destra.
- [x] **Mappa componenti clickabile**: Tramite `ProductMapView` e `ClickableScene` è possibile aggiungere i componenti da sostituire semplicemente cliccando sui pallini numerati nell'immagine del prodotto. Componenti dotati di hover, tooltips, e indicazione visiva.
- [x] **Modalità Calibrazione**: Un interruttore ("Abilita Calibrazione") permette di trascinare numerini sull'immagine per mappare le coordinate X,Y di ogni componente nel file JSON.
- [x] **Zoom & Pan professionale**: La mappa dispone di zoom con rotellina centratamente al mouse e panning trascinando con il tasto destro, supportando anche il reset di adattamento vista automatico sul ridimensionamento.

---

## 6. Prossimi Passi Possibili

- [ ] Implementazione moduli di ricerca approfonditi sulle assistenze effettuate.
- [ ] Esportazione dei rapporti in PDF o stampa diretta.
- [ ] Dialoghi di configurazione per modificare i percorsi dei "Disegni" dal DB o da Settings UI.
- [ ] Possibile integrazione dati anagrafici con il progetto principale `gestionale-tebo`.
