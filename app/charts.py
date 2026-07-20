"""Petits composants graphiques réutilisés dans plusieurs onglets."""
from __future__ import annotations
import pandas as pd
import streamlit as st
from .theme import BLEU


def rank_histogram(dist: dict[int, int], height: int = 320) -> None:
    """Histogramme des rangs (bleu Télécom), robuste."""
    if not dist:
        st.write("Aucune donnée à afficher."); return
    s = pd.Series({f"#{k}": v for k, v in sorted(dist.items())},
                   name="Nombre d'affectations")
    s.index.name = "Rang obtenu"
    st.bar_chart(s, color=BLEU, height=height)


def rank_kpi_row(dist: dict[int, int]) -> None:
    """Tableau horizontal : une colonne KPI par rang (retours à la ligne tous les 8)."""
    items = sorted(dist.items())
    for start in range(0, len(items), 8):
        row = items[start:start + 8]
        cols = st.columns(len(row))
        for c, (k, n) in zip(cols, row):
            c.metric(f"Rang #{k}", n)
