"""App Streamlit minimale pour explorer une instance et un résultat.

Lancer :
    streamlit run app/streamlit_app.py

Strictement séparée de ``src/`` : ne fait qu'appeler des fonctions publiques.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Rendre ``src/`` importable sans installer le projet.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
from src.preprocess import load
from src.report import (distribution_rangs, non_affectes, remplissage,
                        equite_par_groupe, resume, export_assignment)
from src import algo_rsd, algo_flow, algo_mip, algo_hungarian, algo_da, algo_aceei
from src.model import Assignment

ALGOS = {a.NAME: a for a in (algo_rsd, algo_flow, algo_mip, algo_hungarian, algo_da, algo_aceei)}

st.set_page_config(page_title="Affectation cours 2A", layout="wide")
st.title("Affectation des élèves aux cours électifs")

# ---- Sidebar : chargement + choix d'algo ---------------------------------
with st.sidebar:
    st.header("Instance")
    data_dir = st.text_input("Dossier de données", "data")
    if not Path(data_dir).exists():
        st.error(f"Dossier introuvable : {data_dir}")
        st.stop()
    inst = load(data_dir)
    st.write(f"{len(inst.students)} élèves · {len(inst.occurrences)} occ · {len(inst.blocs)} blocs")
    algo_name = st.selectbox("Algorithme", list(ALGOS))
    run_btn = st.button("Lancer l'algo", type="primary")

# ---- Exécution ----------------------------------------------------------
if run_btn or "assignment" not in st.session_state:
    if run_btn:
        with st.spinner(f"Résolution avec {algo_name}…"):
            st.session_state.assignment = ALGOS[algo_name].solve(inst)
            st.session_state.algo_name = algo_name
    else:
        st.info("Choisissez un algo et cliquez sur « Lancer l'algo » à gauche.")
        st.stop()

a: Assignment = st.session_state.assignment

# ---- Onglets -------------------------------------------------------------
tabs = st.tabs(["Récap", "Distribution des rangs", "Non-affectés",
                "Remplissage", "Équité", "Affectations (éditable)"])

with tabs[0]:
    r = resume(inst, a)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Taux d'affectation", f"{r['taux_affectation']*100:.1f}%")
    c2.metric("1er choix", f"{r['part_1er_choix']*100:.1f}%")
    c3.metric("Top-3", f"{r['part_top3']*100:.1f}%")
    c4.metric("Rang moyen", f"{r['rang_moyen']:.2f}")

with tabs[1]:
    d = distribution_rangs(inst, a)
    st.bar_chart(d)

with tabs[2]:
    na = non_affectes(inst, a)
    st.write(f"{len(na)} paires (élève, bloc) non affectées.")
    st.dataframe(na, use_container_width=True)

with tabs[3]:
    rem = remplissage(inst, a)
    st.dataframe(rem, use_container_width=True)

with tabs[4]:
    st.dataframe(equite_par_groupe(inst, a), use_container_width=True)

with tabs[5]:
    st.caption("Éditez la colonne `id_occ` puis cliquez sur « Recalculer ». "
               "Les modifications ne sont pas validées contre les contraintes.")
    df = pd.DataFrame([
        {"eleveID": s.id_eleve, "bloc": b, "id_occ": a[s.id_eleve][b] or ""}
        for s in inst.students for b in inst.blocs
    ])
    edited = st.data_editor(df, use_container_width=True, hide_index=True,
                            num_rows="fixed", key="editor")
    if st.button("Recalculer les métriques sur l'édition"):
        new: Assignment = {s.id_eleve: {b: None for b in inst.blocs} for s in inst.students}
        for _, row in edited.iterrows():
            oid = row["id_occ"].strip() if row["id_occ"] else None
            new[row["eleveID"]][row["bloc"]] = oid or None
        st.session_state.assignment = new
        st.rerun()
    if st.download_button("Télécharger l'affectation (CSV)",
                          data=edited.to_csv(sep=";", index=False),
                          file_name=f"assignment_{st.session_state.algo_name}.csv",
                          mime="text/csv"):
        pass
