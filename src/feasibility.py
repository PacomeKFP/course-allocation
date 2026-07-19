"""Analyse de faisabilité — à exécuter AVANT tout algorithme.

Objectifs (cf. demande utilisateur : explicabilité) :
  * savoir, pour chaque (élève, bloc), combien d'occurrences lui sont
    théoriquement accessibles et combien de ses vœux sont réalisables ;
  * savoir, pour chaque occurrence, la demande théorique (élèves qui
    l'ont classée ET peuvent la suivre) vs la capacité — repérer les
    cours tendus ;
  * repérer les cas structurellement impossibles avant l'algo.

Les fonctions renvoient des DataFrames. Aucun côté effet.
"""
from __future__ import annotations
import pandas as pd
from .model import Instance
from .filters import occ_accessibles, accessible


def par_eleve(inst: Instance) -> pd.DataFrame:
    """Une ligne par (élève, bloc) : nb accessibles, vœux classés, vœux atteignables."""
    rows = []
    for s in inst.students:
        for b in inst.blocs:
            accs = occ_accessibles(inst, s, b)
            wishes = s.voeux_par_bloc.get(b, [])
            wishes_ok = [ue for ue in wishes
                         if any(o.id_ue == ue for o in accs)]
            rows.append({
                "eleve": s.id_eleve, "regime": s.regime, "langue": s.langue,
                "groupes": "+".join(s.groupes_filiere) or "-",
                "bloc": b,
                "nb_accessibles": len(accs),
                "nb_voeux": len(wishes),
                "nb_voeux_atteignables": len(wishes_ok),
                "premier_voeu_atteignable": wishes_ok[0] if wishes_ok else "",
            })
    return pd.DataFrame(rows)


def par_occurrence(inst: Instance) -> pd.DataFrame:
    """Une ligne par occurrence : demande théorique vs capacité, taux de tension."""
    rows = []
    for o in inst.occurrences:
        interess = [s for s in inst.students if accessible(s, o)]
        rangeurs = [s for s in interess
                    if o.id_ue in s.voeux_par_bloc.get(o.bloc, [])]
        premier = [s for s in rangeurs
                   if s.voeux_par_bloc[o.bloc][0] == o.id_ue]
        cap = o.cap_dispo
        rows.append({
            "id_occ": o.id_occ,
            "id_display": o.id_display,
            "bloc": o.bloc, "creneau": o.creneau, "periode": o.periode,
            "langue": o.langue, "fisea": o.fisea,
            "cap_dispo": cap,
            "n_theorique_accessible": len(interess),
            "n_ranged": len(rangeurs),
            "n_premier_choix": len(premier),
            "tension": (len(rangeurs) / cap) if cap else float("inf"),
        })
    return pd.DataFrame(rows).sort_values("tension", ascending=False)


def impossibles(inst: Instance) -> pd.DataFrame:
    """Paires (élève, bloc) où aucune occurrence n'est accessible.

    Ces cas ne peuvent PAS être résolus par un algorithme : le blocage est
    structurel (créneau/langue/FISEA). Il faut soit ouvrir une nouvelle
    occurrence, soit rediscuter la contrainte.
    """
    df = par_eleve(inst)
    return df[df["nb_accessibles"] == 0].copy()


def creneaux_disponibles_par_periode(inst: Instance) -> pd.DataFrame:
    """Pour chaque (période, créneau), nombre d'élèves libres théoriquement.

    Utile pour décider où placer les occurrences dont le ``Créneau prédéfini``
    est vide (cas des Humanités « S2P3 ou S2P4 »). Plus le nombre d'élèves
    libres est grand, plus le créneau est attractif pour y placer un cours.
    """
    from .constantes import CRENEAUX
    from .filters import creneaux_occupes, jour_bloque, JOUR_DU_CRENEAU
    rows = []
    for periode in (1, 2, 3, 4):
        for c in CRENEAUX:
            libres = 0
            for s in inst.students:
                if c in creneaux_occupes(s, periode):
                    continue
                if JOUR_DU_CRENEAU[c] in jour_bloque(s, periode):
                    continue
                libres += 1
            rows.append({"periode": periode, "creneau": c,
                         "n_libres": libres, "n_total": len(inst.students)})
    return pd.DataFrame(rows).sort_values(["periode", "n_libres"], ascending=[True, False])


def occurrences_sans_creneau(inst: Instance) -> pd.DataFrame:
    """Occurrences dont le créneau n'est pas fixé, avec suggestion de placement.

    Pour chaque occurrence sans créneau, on liste les créneaux triés par nombre
    d'élèves libres à sa période (ceux qui l'ont ranked). Le premier est le
    meilleur candidat.
    """
    from .constantes import CRENEAUX
    from .filters import creneaux_occupes, jour_bloque, JOUR_DU_CRENEAU
    dispo = creneaux_disponibles_par_periode(inst)
    rows = []
    for o in inst.occurrences:
        if o.creneau:
            continue
        interess = [s for s in inst.students
                    if o.id_ue in s.voeux_par_bloc.get(o.bloc, [])]
        for c in CRENEAUX:
            libres = 0
            for s in interess:
                if c in creneaux_occupes(s, o.periode or 3):
                    continue
                if JOUR_DU_CRENEAU[c] in jour_bloque(s, o.periode or 3):
                    continue
                libres += 1
            rows.append({"id_occ": o.id_occ, "id_display": o.id_display,
                         "bloc": o.bloc, "periode": o.periode,
                         "cap": o.cap_max, "n_demandeurs": len(interess),
                         "creneau_candidat": c, "n_demandeurs_libres": libres})
    return pd.DataFrame(rows).sort_values(["id_occ", "n_demandeurs_libres"],
                                          ascending=[True, False])


def resume(inst: Instance) -> dict:
    """Synthèse en un dict pour affichage."""
    df = par_eleve(inst)
    occ = par_occurrence(inst)
    n_paires = len(df)
    n_impos = int((df["nb_accessibles"] == 0).sum())
    n_sans_voeu = int((df["nb_voeux"] == 0).sum())
    n_voeu_hors_atteinte = int(((df["nb_voeux"] > 0) &
                                (df["nb_voeux_atteignables"] == 0)).sum())
    return {
        "n_eleves": len(inst.students),
        "n_occurrences": len(inst.occurrences),
        "n_blocs": len(inst.blocs),
        "n_paires_eleve_bloc": n_paires,
        "paires_sans_occurrence_accessible": n_impos,
        "paires_sans_voeu_classe": n_sans_voeu,
        "paires_voeux_hors_atteinte": n_voeu_hors_atteinte,
        "occurrences_tendues_gt_100pct": int((occ["tension"] > 1).sum()),
        "occurrences_sous_effectif_min_possible": int((occ["n_ranged"]
                                                      < [inst.occ_by_id(oid).cap_min
                                                         for oid in occ["id_occ"]]).sum()),
    }
