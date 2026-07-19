"""Chargement d'une instance depuis un dossier de CSV.

Deux formats supportés :
  * simplifié : ``eleves.csv``, ``cours.csv``, ``filiere.csv`` (année N-1).
  * Synapse 2026 : ``etudiants_anonymises.csv``, ``Liste ECUE ...``, ``Liste des
    filières ...`` (§4 du cahier).

L'adaptateur produit toujours le même :class:`Instance`.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from .model import Instance, Occurrence, Student, CRENEAUX_GROUPES

JOUR2CODE = {"Lundi": "Lu", "Mardi": "Ma", "Mercredi": "Me", "Vendredi": "Ve"}
HEURE2CODE = {"8h30-11h45": "am", "13h30-16h45": "pm"}


def _creneau(jour: str, heure: str) -> str:
    """(``Lundi``, ``8h30-11h45``) out ``Lu-am``. Renvoie ``""`` si non résolu."""
    j, h = JOUR2CODE.get(str(jour).strip()), HEURE2CODE.get(str(heure).strip())
    return f"{j}-{h}" if j and h else ""


def _norm_langue(v: str) -> str:
    v = str(v).strip().lower()
    return "EN" if v.startswith(("en", "an")) else "FR"


def load(data_dir: str | Path) -> Instance:
    """Charge une instance. Détecte automatiquement le format."""
    d = Path(data_dir)
    if (d / "eleves.csv").exists():
        return _load_simplifie(d)
    if (d / "etudiants_anonymises.csv").exists():
        return _load_synapse(d)
    raise FileNotFoundError(f"Aucun format reconnu dans {d}")


# -- format simplifié -------------------------------------------------------

def _load_simplifie(d: Path) -> Instance:
    cours = pd.read_csv(d / "cours.csv", sep=";")
    eleves = pd.read_csv(d / "eleves.csv", sep=";")
    # Si un classement par bloc est fourni, il fait autorité.
    par_bloc = (pd.read_csv(d / "eleves_par_bloc.csv", sep=";")
                if (d / "eleves_par_bloc.csv").exists() else None)

    occurrences: list[Occurrence] = []
    for i, r in cours.iterrows():
        titre = str(r["Intitulé"]).lower()
        occurrences.append(Occurrence(
            id_occ=f"O{i:03d}",
            id_ue=str(r["Code UE"]).strip(),
            bloc=str(r["Type ens."]).strip(),
            periode=int(r["Période"]),
            creneau=_creneau(r["Jour"], r["Heure"]),
            langue=_norm_langue(r["Langue"]),
            fisea=("apprenti" in titre) or ("fisea" in titre),
            cap_max=int(r["Max."]),
            cap_min=int(r["Min."]),
        ))

    blocs = sorted({o.bloc for o in occurrences})

    students: list[Student] = []
    for _, r in eleves.iterrows():
        info = str(r.get("info", "")).strip().lower()
        regime = "apprenti" if info == "apprenti" else "etudiant"
        langue = "EN" if info == "international" else "FR"
        # filière : "A", "B", "C", ou combinaison "A+B" / "A+C" / "B+C".
        groupes = [g for g in str(r["filiere"]).strip().upper().split("+")
                   if g in CRENEAUX_GROUPES]
        voeux_par_bloc: dict[str, list[str]] = {}
        if par_bloc is not None:
            sub = par_bloc[par_bloc["eleveID"] == r["eleveID"]]
            for _, row in sub.iterrows():
                voeux_par_bloc[str(row["bloc"])] = [
                    c.strip() for c in str(row["classement"]).split("|") if c.strip()
                ]
        else:
            classement = [c.strip() for c in str(r["classement_matieres"]).split("|")]
            for bloc in blocs:
                ues_du_bloc = {o.id_ue for o in occurrences if o.bloc == bloc}
                voeux_par_bloc[bloc] = [ue for ue in classement if ue in ues_du_bloc]
        students.append(Student(
            id_eleve=str(r["eleveID"]).strip(),
            langue=langue,
            regime=regime,
            groupes_filiere=groupes,
            jours_bloques=[],  # non fourni dans ce format (cf. notes.md N7)
            voeux_par_bloc=voeux_par_bloc,
        ))

    return Instance(students=students, occurrences=occurrences, blocs=blocs)


# -- format Synapse 2026 ----------------------------------------------------

_PERIODE2INT = {"S1-P1": 1, "S1-P2": 2, "S2-P3": 3, "S2-P4": 4}


def _load_synapse(d: Path) -> Instance:
    cours = pd.read_csv(d / "Liste ECUE du tronc commun de 2A 2026-2027.csv", sep=";")
    fil = pd.read_csv(d / "Liste des filières avec créneaux 2026-2027.csv", sep=";")
    et = pd.read_csv(d / "etudiants_anonymises.csv", sep=";")

    occurrences = [Occurrence(
        id_occ=str(r["Idoccur"]),
        id_ue=str(r["Codeue"]),
        bloc=str(r["Bloc"]).strip(),
        periode=_PERIODE2INT.get(str(r["Periode"]).strip(), 0),
        creneau=str(r["Créneau prédéfini"]).strip() if pd.notna(r["Créneau prédéfini"]) else "",
        langue=_norm_langue(r["Langues"]),
        fisea=str(r["FISEA"]).strip().upper() == "O",
        cap_max=int(r["Effectifmax"]),
        cap_min=int(r["Effectifmin"]),
        nb_deja_inscrits=int(r["Nbinscrits"]),
    ) for _, r in cours.iterrows()]

    code2groupe = {str(r["Code parcours"]).strip(): str(r["Créneau"]).strip()
                   for _, r in fil.iterrows()}

    blocs = sorted({o.bloc for o in occurrences})
    students: list[Student] = []
    # Vœux non fournis dans ce format → classement vide (à compléter par un
    # extractzz de Synapse ou par tools/make_ranking_par_bloc.py sur des données
    # dérivées).
    for _, r in et.iterrows():
        regime_raw = str(r["Régime Inscrip."]).strip().lower()
        regime = ("apprenti" if regime_raw.startswith("apprenti")
                  else "auditeur" if regime_raw.startswith("auditeur")
                  else "etudiant")
        codes = [c for c in str(r["Filieres"]).split("$$") if c.strip()]
        groupes = sorted({code2groupe[c] for c in codes if c in code2groupe})
        students.append(Student(
            id_eleve=str(r["Id Personne"]),
            langue="FR" if str(r["Francophone"]).strip().upper() == "OUI" else "EN",
            regime=regime,
            groupes_filiere=groupes,
            jours_bloques=[],
            voeux_par_bloc={b: [] for b in blocs},
        ))

    return Instance(students=students, occurrences=occurrences, blocs=blocs)
