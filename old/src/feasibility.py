"""Analyse de faisabilité — à exécuter AVANT tout algorithme.

Répond à la demande d'explicabilité : combien de paires sont
structurellement infaisables, quels cours sont tendus, où placer les
occurrences dont le créneau n'est pas encore fixé.

Toutes les fonctions renvoient des DataFrames (ou un dict, pour ``resume``).
Aucun effet de bord.
"""
from __future__ import annotations
import pandas as pd
from .model import Instance
from .constantes import CRENEAUX, JOUR_DU_CRENEAU
from .filters import occ_accessibles, accessible, creneaux_occupes, jour_bloque


def par_eleve(inst: Instance) -> pd.DataFrame:
    """Une ligne par (élève, bloc) : nb accessibles, vœux atteignables."""
    rows = []
    for s in inst.students:
        for b in inst.blocs:
            accs = occ_accessibles(inst, s, b)
            ues_acc = {o.id_ue for o in accs}
            wishes_ok = [ue for ue in s.voeux_par_bloc.get(b, []) if ue in ues_acc]
            rows.append({
                "eleve": s.id_eleve, "regime": s.regime, "langue": s.langue,
                "groupes": "+".join(s.groupes_filiere) or "-", "bloc": b,
                "nb_accessibles": len(accs),
                "nb_voeux": len(s.voeux_par_bloc.get(b, [])),
                "nb_voeux_atteignables": len(wishes_ok),
                "premier_voeu_atteignable": wishes_ok[0] if wishes_ok else "",
            })
    return pd.DataFrame(rows)


def par_occurrence(inst: Instance) -> pd.DataFrame:
    """Une ligne par occurrence : demande théorique vs capacité, taux de tension."""
    rows = []
    for o in inst.occurrences:
        interess = [s for s in inst.students if accessible(s, o)]
        rangeurs = [s for s in interess if o.id_ue in s.voeux_par_bloc.get(o.bloc, [])]
        premier = sum(1 for s in rangeurs if s.voeux_par_bloc[o.bloc][0] == o.id_ue)
        rows.append({
            "id_occ": o.id_occ, "id_display": o.id_display, "bloc": o.bloc,
            "creneau": o.creneau, "periode": o.periode, "langue": o.langue,
            "fisea": o.fisea, "cap_dispo": o.cap_dispo, "cap_min": o.cap_min,
            "n_theorique_accessible": len(interess),
            "n_ranged": len(rangeurs),
            "n_premier_choix": premier,
            "tension": len(rangeurs) / o.cap_dispo if o.cap_dispo else float("inf"),
        })
    return pd.DataFrame(rows).sort_values("tension", ascending=False)


def impossibles(inst: Instance) -> pd.DataFrame:
    """Paires (élève, bloc) sans aucune occurrence accessible — blocage structurel."""
    df = par_eleve(inst)
    return df[df["nb_accessibles"] == 0].copy()


def _n_libres(inst: Instance, periode: int, creneau: str, eleves=None) -> int:
    """Nombre d'élèves libres (parmi ``eleves`` ou tous) sur (période, créneau)."""
    pool = eleves if eleves is not None else inst.students
    return sum(1 for s in pool
               if creneau not in creneaux_occupes(s, periode)
               and JOUR_DU_CRENEAU[creneau] not in jour_bloque(s, periode))


def creneaux_disponibles_par_periode(inst: Instance) -> pd.DataFrame:
    """Pour chaque (période, créneau), combien d'élèves sont libres."""
    rows = [{"periode": p, "creneau": c,
             "n_libres": _n_libres(inst, p, c),
             "n_total": len(inst.students)}
            for p in (1, 2, 3, 4) for c in CRENEAUX]
    return pd.DataFrame(rows).sort_values(["periode", "n_libres"],
                                          ascending=[True, False])


def occurrences_sans_creneau(inst: Instance) -> pd.DataFrame:
    """Pour chaque occurrence sans créneau fixé, classement des créneaux candidats."""
    rows = []
    for o in inst.occurrences:
        if o.creneau:
            continue
        interess = [s for s in inst.students
                    if o.id_ue in s.voeux_par_bloc.get(o.bloc, [])]
        for c in CRENEAUX:
            rows.append({
                "id_occ": o.id_occ, "id_display": o.id_display,
                "bloc": o.bloc, "periode": o.periode,
                "cap": o.cap_max, "n_demandeurs": len(interess),
                "creneau_candidat": c,
                "n_demandeurs_libres": _n_libres(inst, o.periode or 3, c, interess),
            })
    return pd.DataFrame(rows).sort_values(["id_occ", "n_demandeurs_libres"],
                                          ascending=[True, False])


def resume(inst: Instance) -> dict:
    """Synthèse compacte pour affichage."""
    df = par_eleve(inst)
    occ = par_occurrence(inst)
    return {
        "n_eleves": len(inst.students),
        "n_occurrences": len(inst.occurrences),
        "n_blocs": len(inst.blocs),
        "n_paires_eleve_bloc": len(df),
        "paires_sans_occurrence_accessible": int((df["nb_accessibles"] == 0).sum()),
        "paires_sans_voeu_classe": int((df["nb_voeux"] == 0).sum()),
        "paires_voeux_hors_atteinte": int(((df["nb_voeux"] > 0) &
                                          (df["nb_voeux_atteignables"] == 0)).sum()),
        "occurrences_tendues_gt_100pct": int((occ["tension"] > 1).sum()),
        "occurrences_sous_effectif_min_potentiel": int((occ["n_ranged"] < occ["cap_min"]).sum()),
    }
