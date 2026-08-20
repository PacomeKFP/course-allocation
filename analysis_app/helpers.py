from __future__ import annotations
from pathlib import Path
import sys
from typing import Dict, List
import pandas as pd

# Ensure repository root is on sys.path so `src` package is importable
REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.data.constants import SLOTS_BY_GROUP, DAY_OF_SLOT, company_days
from src.rules.feasibility import Feasibility
from src.data.loaders import build_campaign


def load_campaign_paths(students_path: Path, campaign_path: Path, ecue_path: Path | None):
    return build_campaign(students_path, campaign_path, ecue_path)


def unassignable_by_feasibility(campaign) -> pd.DataFrame:
    f = Feasibility()
    rows = []
    # Build occurrence label map and UE->Bloc map (using default_ecue as authoritative)
    occ_label = {
        o.id_occ: f"{o.id_occ} | {o.label}" for o in campaign.occurrences.values()}
    # try to read default_ecue for Bloc per Idue
    ue_block: dict[str, str] = {}
    try:
        import pandas as _pd
        repo = Path(__file__).resolve().parents[1]
        df_ecue = _pd.read_csv(repo / 'src' / 'data' /
                               'default_ecue.csv', sep=';')
        for _, r in df_ecue.iterrows():
            idue = str(r.get('Idue')).strip()
            bloc = str(r.get('Bloc', '')).strip()
            if idue:
                ue_block[idue] = bloc
    except Exception:
        ue_block = {}
    for v in campaign.voeux:
        s = campaign.students.get(v.id_student)
        if s is None:
            rows.append({"id_student": v.id_student, "id_demande": v.id_demande,
                         "student_info": "", "n_voeux": len(v.ranked_occurrences),
                         "reason": "élève absent"})
            continue
        accessible = False
        per = {}
        # collect the UEs present in this voeu (for a human-friendly demande label)
        ues_for_voeu = set()
        for oid in v.ranked_occurrences:
            o = campaign.occurrences.get(oid)
            if o is None:
                per[oid] = ["occurrence inconnue"]
                continue
            # collect UE info
            if getattr(o, 'id_ue', None):
                ues_for_voeu.add(o.id_ue)
            msgs = f.check(s, o)
            if not msgs:
                accessible = True
                break
            per[oid] = msgs
        # prepare student_info: regime|langue|filieres
        lang = 'EN' if not s.francophone else 'FR'
        filieres_str = "+".join(s.filieres) if s.filieres else ""
        student_info = f"{s.regime}|{lang}|{filieres_str}"

        if not accessible:
            # build human-friendly labels
            ranked_labels = ";".join(occ_label.get(x, x)
                                     for x in v.ranked_occurrences)
            ue_labels = []
            for idue in sorted(ues_for_voeu):
                blk = ue_block.get(idue) or ''
                ue_labels.append(f"{blk}/{idue}" if blk else f"{idue}")
            demande_label = ";".join(ue_labels) if ue_labels else ''
            rows.append({"id_student": v.id_student, "id_demande": v.id_demande,
                             "student_info": student_info,
                             "id_demande_label": demande_label,
                             "n_voeux": len(v.ranked_occurrences),
                             "ranked_occurrences": ";".join(v.ranked_occurrences),
                             "ranked_occurrences_labels": ranked_labels,
                             "reason": ";".join(sorted({m for ms in per.values() for m in ms})),
                             "per_occurrence": str(per)})
    return pd.DataFrame(rows)


def reconstruct_timetable_for(s, period: int) -> Dict[str, str]:
    """Return mapping slot->status for the student's group and period."""
    if not s.filieres:
        return {}
    g = None
    # first filiere drives schedule
    try:
        g = s.filieres[0]
    except Exception:
        return {}
    # SLOTS_BY_GROUP keys are groups like 'A','B','C' so map filiere->group
    # We need to import mapping lazily to avoid import cycles
    from src.data.constants import FILIERE_TO_GROUPE
    grp = FILIERE_TO_GROUPE.get(g)
    if not grp:
        return {}
    occupied = {
        slot: 'occupied by filiere' for slot in SLOTS_BY_GROUP[grp][period]}
    # company days -> mark all slots on that day as 'company'
    days = company_days(grp, period)
    for slot, day in DAY_OF_SLOT.items():
        if day in days:
            occupied.setdefault(slot, 'company day')
    return occupied
