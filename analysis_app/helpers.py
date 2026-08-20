"""Analyse hors-ligne : vœux sans occurrence accessible + reconstitution EDT."""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.data.constants import SLOTS, SLOTS_BY_GROUP, DAY_OF_SLOT, FILIERE_TO_GROUPE, company_days
from src.data.loaders import build_campaign
from src.validate import analyze_demande


def load_campaign_paths(students_path, campaign_path, ecue_path=None):
    return build_campaign(students_path, campaign_path, ecue_path)


def unassignable_by_feasibility(campaign) -> pd.DataFrame:
    """Paires (élève, demande) dont AUCUN vœu n'est accessible (règles dures)."""
    rows = []
    for v in campaign.voeux:
        s = campaign.students.get(v.id_student)
        if s is None:
            rows.append({"id_student": v.id_student, "id_demande": v.id_demande,
                         "student_info": "", "n_voeux": len(v.ranked_occurrences),
                         "reason": "élève absent"})
            continue
        a = analyze_demande(campaign, v.id_student, v.id_demande)
        if a.satisfiable:
            continue
        rows.append({
            "id_student": v.id_student, "id_demande": v.id_demande,
            "student_info": s.info,
            "id_demande_label": campaign.bloc_of(v),
            "n_voeux": a.n_voeux,
            "ranked_occurrences": ";".join(v.ranked_occurrences),
            "ranked_occurrences_labels": campaign.voeux_labels(v),
            "reason": ";".join(sorted({m for ms in a.impossibles.values() for m in ms})),
        })
    return pd.DataFrame(rows)


def reconstruct_timetable_for(s, period: int) -> dict[str, str]:
    """Créneau → statut (« occupied by filiere » / « company day ») pour l'élève."""
    if not s.filieres:
        return {}
    grp = FILIERE_TO_GROUPE.get(s.filieres[0])
    if not grp:
        return {}
    occupied = {slot: "occupied by filiere" for slot in SLOTS_BY_GROUP[grp][period]}
    days = company_days(grp, period)
    for slot in SLOTS:
        if DAY_OF_SLOT.get(slot) in days:
            occupied.setdefault(slot, "company day")
    return occupied
