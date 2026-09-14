from __future__ import annotations

import logging

import streamlit as st
from dotenv import load_dotenv

from wander_agent.graph import build_graph
from wander_agent.report_export import report_to_markdown_bytes, report_to_pdf_bytes
from wander_agent.visualization import distance_per_day_chart, elevation_duration_chart

load_dotenv()
logging.basicConfig(level=logging.INFO)

NODE_LABELS = {
    "gather_requirements": "Rahmenbedingungen erfassen",
    "analyze_requirements": "Anforderungen analysieren",
    "research_regions": "Regionen recherchieren",
    "compare_routes": "Routen vergleichen",
    "collect_feedback": "Feedback einholen",
    "research_critique": "Kritik recherchieren",
    "extract_itinerary": "Etappen extrahieren",
    "write_itinerary": "Tourenbericht schreiben",
}
TOTAL_STEPS = len(NODE_LABELS)

EXAMPLE_AVAILABILITY_CSV = (
    "day,date,max_hours,max_elevation_gain_m\n"
    "1,2026-10-03,6,700\n"
    "2,2026-10-04,7,900\n"
    "3,2026-10-05,5,400\n"
)


def main() -> None:
    st.set_page_config(page_title="Schwarzwald-Wander-Agent", layout="wide")
    st.title("Schwarzwald-Wander-Agent")
    st.caption("Recherchiert Regionen, vergleicht Routen und plant eine mehrtägige Tour anhand deiner Tages-Kapazität.")

    with st.sidebar:
        st.header("Einstellungen")
        provider = st.radio(
            "LLM-Provider",
            options=["gemini", "ollama"],
            help=(
                "Gemini nutzt die kostenlose Gemini API. Ollama läuft komplett "
                "lokal ohne API-Key, braucht aber ein laufendes Ollama mit "
                "heruntergeladenem Modell."
            ),
        )
        model_name = st.text_input(
            "Modellname (optional)",
            value="",
            help="Leer lassen für den Standard (Gemini: gemini-3.6-flash, Ollama: llama3.2).",
        )
        max_revisions = st.number_input("Max. Revisionen", min_value=1, value=2)

    trip_request = st.text_input(
        "Tourenwunsch",
        "Plane eine 3-tägige Wanderung im Südschwarzwald mit Aussichtspunkten und "
        "mindestens einem Wasserfall, moderate Schwierigkeit.",
    )
    regions_raw = st.text_area(
        "Zu vergleichende Regionen/Routen (eine pro Zeile)",
        "Feldberg / Belchen\nWutachschlucht\nHochschwarzwald-Seen",
    )
    st.caption("CSV mit Tages-Kapazität (Stunden und Höhenmeter-Budget je Tag). Beispiel unten vorausgefüllt, gern anpassen.")
    availability_csv = st.text_area("Tages-Kapazität (CSV)", EXAMPLE_AVAILABILITY_CSV, height=120)

    if st.button("Tour planen", type="primary"):
        regions = [r.strip() for r in regions_raw.split("\n") if r.strip()]
        if not regions:
            st.warning("Bitte mindestens eine Region angeben.")
            return
        if not availability_csv.strip():
            st.warning("Bitte die Tages-Kapazität als CSV angeben.")
            return

        initial_state = {
            "trip_request": trip_request,
            "regions": regions,
            "availability_csv": availability_csv,
            "max_revisions": int(max_revisions),
            "revision_number": 1,
            "content": [],
            "trip_brief": "",
            "requirements_analysis": "",
            "route_comparison": "",
            "feedback": "",
            "itinerary_report": "",
            "day_plans": [],
            "llm_provider": provider,
            "llm_model": model_name or None,
        }

        graph = build_graph()
        progress = st.progress(0.0, text="Starte...")
        status_box = st.empty()
        final_state: dict = {}

        try:
            step = 0
            for update in graph.stream(initial_state):
                node_name = next(iter(update))
                step += 1
                progress.progress(min(step / TOTAL_STEPS, 1.0), text=NODE_LABELS.get(node_name, node_name))
                status_box.write(f"Abgeschlossen: {NODE_LABELS.get(node_name, node_name)}")
                final_state.update(update[node_name])

            progress.progress(1.0, text="Fertig")

            if final_state.get("itinerary_report"):
                st.subheader("Tourenbericht")
                st.markdown(final_state["itinerary_report"])

                day_plans = final_state.get("day_plans") or []
                distance_fig = distance_per_day_chart(day_plans)
                elevation_fig = elevation_duration_chart(day_plans)
                if distance_fig or elevation_fig:
                    st.subheader("Etappen im Diagramm")
                    cols = st.columns(2)
                    if distance_fig:
                        cols[0].pyplot(distance_fig)
                    if elevation_fig:
                        cols[1].pyplot(elevation_fig)
                else:
                    st.caption("Für ein Diagramm konnten keine strukturierten Etappen-Daten extrahiert werden.")

                col_a, col_b = st.columns(2)
                col_a.download_button(
                    "Als Markdown herunterladen",
                    data=report_to_markdown_bytes(final_state["itinerary_report"]),
                    file_name="tourenplan.md",
                    mime="text/markdown",
                )
                col_b.download_button(
                    "Als PDF herunterladen",
                    data=report_to_pdf_bytes("Schwarzwald-Tourenplan", final_state["itinerary_report"]),
                    file_name="tourenplan.pdf",
                    mime="application/pdf",
                )
            else:
                st.error("Der Agent hat keinen Tourenbericht erzeugt.")

        except Exception as exc:
            st.error(f"Ein Fehler ist aufgetreten: {exc}")


if __name__ == "__main__":
    main()
