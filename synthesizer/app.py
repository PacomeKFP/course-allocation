"""Générateur de jeux de données synthétiques Synapse.

Génère un fichier « étudiants » + un fichier « vœux campagne » compatibles
avec le pipeline d'affectation principal.
"""
from __future__ import annotations
import io, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from synthesizer.generator import ProfileMix, CampaignMix, generate_all
from app.theme import apply_theme, header

st.set_page_config(page_title="Générateur de campagne fictive — 2A",
                   layout="wide", initial_sidebar_state="expanded")
apply_theme()
header("Générateur de campagne fictive",
       "Produit des jeux de données Synapse cohérents pour tester le solveur")

with st.sidebar:
    st.markdown("### Composition de la promotion")
    n_total = st.slider("Taille totale", 20, 500, 200)
    pct_appr = st.slider("Apprentis (%)", 0, 40, 10) / 100
    pct_eng = st.slider("Anglophones (%)", 0, 40, 15) / 100
    pct_pei = st.slider("Auditeurs PEI (%)", 0, 20, 0) / 100
    st.markdown("### Pondération des groupes de filière")
    st.caption("Simule des promotions déséquilibrées entre groupes A / B / C.")
    w_a = st.slider("Groupe A", 0, 5, 1)
    w_b = st.slider("Groupe B", 0, 5, 1)
    w_c = st.slider("Groupe C", 0, 5, 1)
    st.markdown("### Génération des vœux")
    n_voeux_min = st.slider("Minimum de vœux par demande", 1, 8, 2)
    n_voeux_max = st.slider("Maximum de vœux par demande", n_voeux_min, 14, 8)
    pct_vides = st.slider("Part de demandes non exprimées (%)", 0, 30, 2,
                          help="Simule les élèves non concernés par certaines demandes") / 100
    seed = st.number_input("Graine aléatoire", value=42, min_value=0)
    generer = st.button("Générer la campagne", type="primary", use_container_width=True)

if generer or "gen" not in st.session_state:
    if generer:
        profile = ProfileMix(n_total=n_total, pct_apprentis=pct_appr,
                             pct_anglophones=pct_eng, pct_auditeurs_pei=pct_pei,
                             weights_group={"A": w_a, "B": w_b, "C": w_c},
                             seed=int(seed))
        campaign = CampaignMix(n_voeux_min=n_voeux_min, n_voeux_max=n_voeux_max,
                                pct_demandes_vides=pct_vides, seed=int(seed))
        with st.spinner("Génération en cours…"):
            st.session_state.gen = generate_all(profile, campaign)
    else:
        st.info("Ajustez les paramètres à gauche puis cliquez sur "
                "**Générer la campagne**.")
        st.stop()

students, campaign_df = st.session_state.gen

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Étudiants", len(students))
c2.metric("Apprentis", int((students["Régime Inscrip."] == "Apprentis").sum()))
c3.metric("Anglophones", int((students["Francophone"] == "NON").sum()))
c4.metric("Auditeurs PEI", int((students["Régime Inscrip."] == "Auditeur libre").sum()))
c5.metric("Lignes de vœux", len(campaign_df))

tabs = st.tabs(["Aperçu étudiants", "Aperçu vœux", "Téléchargement"])

with tabs[0]:
    st.dataframe(students, use_container_width=True, hide_index=True, height=440)

with tabs[1]:
    demandes = campaign_df["IDDemande"].unique()
    sel = st.selectbox("Filtrer sur une demande", ["Toutes"] + list(demandes))
    view = campaign_df if sel == "Toutes" else campaign_df[campaign_df["IDDemande"] == sel]
    st.dataframe(view, use_container_width=True, hide_index=True, height=440)


def _csv(df):
    buf = io.StringIO()
    df.to_csv(buf, sep=";", index=False)
    return buf.getvalue().encode("utf-8-sig")


with tabs[2]:
    st.caption("Ces deux fichiers se rechargent directement dans l'application "
               "principale d'affectation.")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("Étudiants (etudiants_anonymises.csv)",
                           data=_csv(students),
                           file_name="etudiants_anonymises.csv", mime="text/csv",
                           use_container_width=True)
    with c2:
        st.download_button("Campagne de vœux (structure-export.csv)",
                           data=_csv(campaign_df),
                           file_name="campagne_synthetique.csv", mime="text/csv",
                           use_container_width=True)
