# Schwarzwald-Wander-Agent

Ein LangGraph-Agent, der aus einem Tourenwunsch, mehreren zu vergleichenden Schwarzwald-Regionen und einer Tages-Kapazität (verfügbare Stunden, Höhenmeter-Budget pro Tag) automatisiert eine recherchierte, mehrtägige Wanderroute plant: Rahmenbedingungen erfassen, analysieren, Regionen recherchieren (Tavily-Websuche), Routen vergleichen, über eine Feedback-Revisionsschleife verbessern und als Tourenbericht mit Etappen-Diagrammen ausgeben.

## Screenshots

**Formular und generierter Tourenbericht**

<img src="screenshots/formular-und-bericht.png" width="700" alt="Formular und Tourenbericht">

**Tag-für-Tag-Gliederung mit Etappendaten**

<img src="screenshots/tagesetappen.png" width="700" alt="Tagesetappen">

**Diagramme und Export**

<img src="screenshots/diagramme-und-export.png" width="700" alt="Diagramme und Export">

## Architektur & Herkunft

Die Grundarchitektur - ein LangGraph-Reflection-Agent (erzeugen → recherchieren → vergleichen → Feedback-Revisionsschleife → finaler Output) - stammt aus einer Übung im Udemy-Kurs [AI Engineer Bootcamp 2026: LLMs, RAG, AI Agents & Vector DBs](https://www.udemy.com/course/llm-engineering/), dort als Finanzvergleichs-Agent umgesetzt. Übernommen wurde nur dieses Architekturmuster - Domäne, State-Modell, alle Prompts und die strukturierte Extraktion sind komplett neu für die Tourenplanung geschrieben.

Gegenüber dem Kursmuster ergänzt:

- Wahl zwischen Gemini API und lokalem Ollama-Modell zur Laufzeit
- Parallele Regionen-Recherche per `ThreadPoolExecutor` statt sequenziell
- Neuer Node `extract_itinerary`: strukturierte Etappen-Daten (Strecke, Höhenmeter, Zeit) statt reinem Fließtext
- Diagramme, Markdown-/PDF-Export
- Retry-Logik für LLM-/Tavily-Aufrufe
- Modularisierung in einzelne Dateien statt einer Kursdatei

## Setup

```bash
git clone <repo-url>
cd schwarzwald-wander-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# GEMINI_API_KEY und TAVILY_API_KEY in .env eintragen
```

Gemini-Key: kostenlos über [Google AI Studio](https://aistudio.google.com/). Tavily-Key: kostenlos über [tavily.com](https://tavily.com/) (begrenztes Freikontingent). Für `provider=ollama` wird zusätzlich ein lokal laufendes [Ollama](https://ollama.com/) mit heruntergeladenem Modell benötigt (z. B. `ollama pull llama3.2`) - ein Tavily-Key bleibt trotzdem nötig, da die Websuche unabhängig vom LLM-Provider läuft.

### Streamlit-Oberfläche

```bash
streamlit run app.py
```

Tourenwunsch, Regionen und Tages-Kapazität sind mit einem Beispiel vorausgefüllt und direkt im Formular editierbar.

### Tests

```bash
pytest
```
