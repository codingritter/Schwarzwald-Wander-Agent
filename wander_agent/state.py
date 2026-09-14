from __future__ import annotations

import operator
from typing import Annotated, List, Optional, TypedDict

from pydantic import BaseModel, Field


class Queries(BaseModel):
    queries: List[str] = Field(default_factory=list)


class DayPlan(BaseModel):
    day_label: str
    route_name: Optional[str] = None
    distance_km: Optional[float] = None
    elevation_gain_m: Optional[float] = None
    duration_hours: Optional[float] = None
    note: Optional[str] = None


class ItineraryExtraction(BaseModel):
    days: List[DayPlan] = Field(default_factory=list)


class AgentState(TypedDict):
    trip_request: str
    regions: List[str]
    availability_csv: str
    trip_brief: str
    requirements_analysis: str
    route_comparison: str
    feedback: str
    itinerary_report: str
    content: Annotated[List[str], operator.add]
    day_plans: List[DayPlan]
    revision_number: int
    max_revisions: int
    llm_provider: str
    llm_model: Optional[str]
