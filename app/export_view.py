"""Onglet Export : CSV Synapse + Excel multi-onglets."""
from __future__ import annotations
import io, tempfile
from pathlib import Path
import pandas as pd
import streamlit as st
from src.reporting import export_synapse_import
from . import labels as L


def render(state) -> None:
    st.caption("Téléchargez le CSV d'import Synapse (à réinjecter dans le "
               "système d'information de la scolarité) et un rapport Excel "
               "multi-onglets récapitulant l'affectation.")
    tmp = Path(tempfile.gettempdir()) / "synapse_import.csv"
    export_synapse_import(state.campaign, state.assignment, tmp)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Télécharger le CSV pour Synapse", data=tmp.read_bytes(),
            file_name="synapse_import.csv", mime="text/csv",
            use_container_width=True,
            help="À réinjecter tel quel dans Synapse pour valider les inscriptions")
    with c2:
        st.download_button(
            "Télécharger le rapport Excel", data=_build_excel(state),
            file_name="rapport_affectation.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            help="Cinq onglets : non affectés, remplissage, statistiques "
                 "par demande, équité par élève, distribution des rangs")


def _build_excel(state) -> bytes:
    """Génère un classeur multi-onglets prêt à ouvrir dans Excel/LibreOffice."""
    buf = io.BytesIO()
    r = state.report
    filling = r.filling().assign(period=lambda d: d["period"].map(L.fmt_period))
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        r.not_assigned().to_excel(w, sheet_name="Non affectés", index=False)
        filling.to_excel(w, sheet_name="Remplissage", index=False)
        r.stats_per_demande().to_excel(w, sheet_name="Stats par demande", index=False)
        r.stats_compensation().sort_values("worst_rank", ascending=False).to_excel(
            w, sheet_name="Équité par élève", index=False)
        pd.DataFrame([(f"#{k}", v) for k, v in state.stats["rank_distribution"].items()],
                     columns=["Rang obtenu", "Nombre"]).to_excel(
            w, sheet_name="Distribution rangs", index=False)
    return buf.getvalue()
