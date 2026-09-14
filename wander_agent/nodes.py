from __future__ import annotations

import functools
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
from typing import Callable, List, Optional, TypeVar

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage
from tavily import TavilyClient

from .llm_provider import get_llm
from .state import AgentState, ItineraryExtraction, Queries

logger = logging.getLogger(__name__)

T = TypeVar("T")

GATHER_REQUIREMENTS_PROMPT = (
    "Du bist ein erfahrener Wanderführer und Tourenplaner für den "
    "Schwarzwald. Fasse die Rahmenbedingungen der Tour (verfügbare Tage, "
    "Kapazität pro Tag, Wünsche) strukturiert und vollständig zusammen."
)
ANALYZE_REQUIREMENTS_PROMPT = (
    "Du bist Tourenplaner. Leite aus den Rahmenbedingungen die wichtigsten "
    "Prioritäten und Einschränkungen für die Routenwahl ab, z. B. maximale "
    "Tagesetappe, Schwierigkeitsgrad und thematische Wünsche."
)
RESEARCH_REGIONS_PROMPT = (
    "Du recherchierst Wanderrouten und Sehenswürdigkeiten in einer "
    "bestimmten Schwarzwald-Region für eine Tourenplanung. Erzeuge maximal "
    "3 Suchanfragen."
)
COMPARE_ROUTES_PROMPT = (
    "Du bist Tourenplaner. Vergleiche die recherchierten Regionen/Routen "
    "anhand der Anforderungen und schlage eine konkrete Tagesaufteilung vor. "
    "Nenne dabei unbedingt die Namen der Regionen bzw. Routen."
)
FEEDBACK_PROMPT = (
    "Du bist ein erfahrener Bergwanderer und Gutachter. Prüfe den "
    "vorgeschlagenen Tourenplan auf Realismus - Tagesetappen, Höhenmeter, "
    "Pausen, Wetterabhängigkeit - und gib konkretes Verbesserungs-Feedback."
)
RESEARCH_CRITIQUE_PROMPT = (
    "Du recherchierst Informationen, um die gegebene Kritik am Tourenplan zu "
    "adressieren, z. B. Alternativrouten, Hüttenöffnungszeiten oder "
    "Wetterlage. Erzeuge maximal 3 Suchanfragen."
)
EXTRACT_ITINERARY_PROMPT = (
    "Extrahiere aus dem folgenden Text die strukturierten Eckdaten je Tag "
    "der Tour: Strecke in km, Höhenmeter im Anstieg, geplante Wanderzeit in "
    "Stunden. Wenn ein Wert nicht eindeutig hervorgeht, lasse ihn leer statt "
    "zu raten."
)
WRITE_ITINERARY_PROMPT = (
    "Du bist Reiseautor für Wandertouren. Schreibe einen zusammenhängenden, "
    "ansprechenden Tourenbericht auf Basis von Analyse, Regionen-Recherche, "
    "Routenvergleich und Feedback - inklusive Tag-für-Tag-Gliederung."
)


def with_retries(max_attempts: int = 3, backoff_seconds: float = 2.0) -> Callable:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exc: Optional[Exception] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    logger.warning(
                        "%s fehlgeschlagen (Versuch %s/%s): %s",
                        func.__name__, attempt, max_attempts, exc,
                    )
                    if attempt < max_attempts:
                        time.sleep(backoff_seconds * attempt)
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator


def _llm(state: AgentState):
    return get_llm(provider=state.get("llm_provider", "gemini"), model=state.get("llm_model"))


def _tavily() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY ist nicht gesetzt.")
    return TavilyClient(api_key=api_key)


@with_retries()
def _invoke(llm, messages):
    return llm.invoke(messages)


def gather_requirements_node(state: AgentState) -> dict:
    df = pd.read_csv(StringIO(state["availability_csv"]))
    availability_str = df.to_string(index=False)
    combined_content = (
        f"{state['trip_request']}\n\nHier ist die Tages-Kapazität "
        f"(Stunden und Höhenmeter-Budget pro Tag):\n\n{availability_str}"
    )

    llm = _llm(state)
    response = _invoke(llm, [
        SystemMessage(content=GATHER_REQUIREMENTS_PROMPT),
        HumanMessage(content=combined_content),
    ])
    return {"trip_brief": response.content}


def analyze_requirements_node(state: AgentState) -> dict:
    llm = _llm(state)
    response = _invoke(llm, [
        SystemMessage(content=ANALYZE_REQUIREMENTS_PROMPT),
        HumanMessage(content=state["trip_brief"]),
    ])
    return {"requirements_analysis": response.content}


def _research_one_region(llm, region: str) -> List[str]:
    queries = llm.with_structured_output(Queries).invoke([
        SystemMessage(content=RESEARCH_REGIONS_PROMPT),
        HumanMessage(content=region),
    ])
    tavily = _tavily()
    found: List[str] = []
    for q in queries.queries:
        response = tavily.search(query=q, max_results=2)
        found.extend(r["content"] for r in response["results"])
    return found


def research_regions_node(state: AgentState) -> dict:
    llm = _llm(state)
    regions = state["regions"]
    new_content: List[str] = []

    with ThreadPoolExecutor(max_workers=min(4, max(1, len(regions)))) as pool:
        futures = {
            pool.submit(_research_one_region, llm, region): region
            for region in regions
        }
        for future in as_completed(futures):
            region = futures[future]
            try:
                new_content.extend(future.result())
            except Exception as exc:
                logger.warning("Recherche zu %s fehlgeschlagen: %s", region, exc)

    return {"content": new_content}


def compare_routes_node(state: AgentState) -> dict:
    content = "\n\n".join(state["content"] or [])
    llm = _llm(state)
    response = _invoke(llm, [
        SystemMessage(content=f"{COMPARE_ROUTES_PROMPT}\n\nRecherchematerial:\n{content}"),
        HumanMessage(
            content=f"{state['trip_request']}\n\nHier ist die Anforderungsanalyse:\n\n{state['requirements_analysis']}"
        ),
    ])
    return {
        "route_comparison": response.content,
        "revision_number": state.get("revision_number", 1) + 1,
    }


def research_critique_node(state: AgentState) -> dict:
    llm = _llm(state)
    queries = llm.with_structured_output(Queries).invoke([
        SystemMessage(content=RESEARCH_CRITIQUE_PROMPT),
        HumanMessage(content=state["feedback"]),
    ])
    tavily = _tavily()
    new_content: List[str] = []
    for q in queries.queries:
        response = tavily.search(query=q, max_results=2)
        new_content.extend(r["content"] for r in response["results"])
    return {"content": new_content}


def collect_feedback_node(state: AgentState) -> dict:
    llm = _llm(state)
    response = _invoke(llm, [
        SystemMessage(content=FEEDBACK_PROMPT),
        HumanMessage(content=state["route_comparison"]),
    ])
    return {"feedback": response.content}


def extract_itinerary_node(state: AgentState) -> dict:
    llm = _llm(state)
    source_text = f"{state['requirements_analysis']}\n\n{state['route_comparison']}"
    try:
        extraction = llm.with_structured_output(ItineraryExtraction).invoke([
            SystemMessage(content=EXTRACT_ITINERARY_PROMPT),
            HumanMessage(content=source_text),
        ])
        return {"day_plans": extraction.days}
    except Exception as exc:
        logger.warning("Etappen-Extraktion fehlgeschlagen, Diagramm wird übersprungen: %s", exc)
        return {"day_plans": []}


def write_itinerary_node(state: AgentState) -> dict:
    llm = _llm(state)
    response = _invoke(llm, [
        SystemMessage(content=WRITE_ITINERARY_PROMPT),
        HumanMessage(content=state["route_comparison"]),
    ])
    return {"itinerary_report": response.content}


def should_continue(state: AgentState) -> str:
    if state["revision_number"] > state["max_revisions"]:
        return "extract_itinerary"
    return "collect_feedback"
