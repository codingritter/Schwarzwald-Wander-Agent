from __future__ import annotations

from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np

from .state import DayPlan


def distance_per_day_chart(day_plans: List[DayPlan]) -> Optional[plt.Figure]:
    usable = [d for d in day_plans if d.distance_km is not None]
    if not usable:
        return None

    fig, ax = plt.subplots(figsize=(7, 4))
    labels = [d.day_label for d in usable]
    values = [d.distance_km for d in usable]
    ax.bar(labels, values, color="#4C72B0")
    ax.set_ylabel("Strecke (km)")
    ax.set_title("Tagesetappen im Vergleich")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    return fig


def elevation_duration_chart(day_plans: List[DayPlan]) -> Optional[plt.Figure]:
    usable = [
        d for d in day_plans
        if d.elevation_gain_m is not None or d.duration_hours is not None
    ]
    if not usable:
        return None

    labels = [d.day_label for d in usable]
    elevation = [d.elevation_gain_m or 0 for d in usable]
    duration = [d.duration_hours or 0 for d in usable]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(7, 4))
    ax1.bar(x - width / 2, elevation, width, label="Höhenmeter (m)", color="#55A868")
    ax1.set_ylabel("Höhenmeter (m)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=30, ha="right")

    ax2 = ax1.twinx()
    ax2.bar(x + width / 2, duration, width, label="Wanderzeit (h)", color="#C44E52")
    ax2.set_ylabel("Wanderzeit (h)")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    ax1.set_title("Höhenmeter und Wanderzeit je Tag")
    fig.tight_layout()
    return fig
