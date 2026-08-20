"""Mini-app Streamlit pour analyser les vœux non assignables."""
from __future__ import annotations
from helpers import load_campaign_paths, unassignable_by_feasibility, reconstruct_timetable_for
from pathlib import Path
import sys
import tempfile
import streamlit as st
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main():
    st.title("Analyse des vœux non assignés — mini-app")
    students_default = REPO / 'data' / 'samples' / 'etudiants_anonymises.csv'
    campaign_default = REPO / 'data' / 'samples' / 'campagne_synthetique.csv'
    ecue_default = REPO / 'src' / 'data' / 'default_ecue.csv'

    students_path = st.sidebar.file_uploader('Students CSV', type=['csv'])
    campaign_path = st.sidebar.file_uploader('Campaign CSV', type=['csv'])
    ecue_path = st.sidebar.file_uploader('ECUE CSV', type=['csv'])

    if not students_path:
        students_path = students_default
    if not campaign_path:
        campaign_path = campaign_default
    if not ecue_path:
        ecue_path = ecue_default

    def _prepare_path(p):
        # If Streamlit UploadedFile (file-like), write to a temp file and return Path
        if hasattr(p, 'read'):
            data = p.read()
            tf = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
            tf.write(data)
            tf.flush()
            tf.close()
            return Path(tf.name)
        return Path(p)

    if st.button('Charger et analyser'):
        sp = _prepare_path(students_path)
        cp = _prepare_path(campaign_path)
        ep = _prepare_path(ecue_path)
        campaign = load_campaign_paths(sp, cp, ep)
        df = unassignable_by_feasibility(campaign)
        st.subheader('Vœux sans occurrence accessible (approx.)')
        st.dataframe(df)

        st.sidebar.subheader('Par étudiant')
        student_ids = sorted(campaign.students.keys())
        sid = st.sidebar.selectbox('Choisir un id_student', [''] + student_ids)
        if sid:
            s = campaign.students[sid]
            st.write('Régime:', s.regime)
            st.write('Filières:', ','.join(s.filieres))
            st.write('Vœux de cet étudiant:')
            voeux = [v for v in campaign.voeux if v.id_student == sid]
            rows = []
            for v in voeux:
                for rank, oid in enumerate(v.ranked_occurrences, 1):
                    o = campaign.occurrences.get(oid)
                    rows.append({'id_demande': v.id_demande, 'rank': rank, 'id_occ': oid,
                                 'label': o.label if o else '', 'period': o.period if o else None,
                                 'slot': o.slot if o else ''})
            st.table(pd.DataFrame(rows))
            st.subheader('Emploi du temps reconstitué (par période)')
            for p in (1, 2, 3, 4):
                st.write(f'Période P{p}')
                occupied = reconstruct_timetable_for(s, p)
                if not occupied:
                    st.write('Aucune filière connue pour reconstitution')
                    continue
                st.table(pd.DataFrame([{'slot': k, 'status': v}
                         for k, v in occupied.items()]))


if __name__ == '__main__':
    main()
