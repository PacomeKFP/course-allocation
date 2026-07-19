"""Chargement d'une instance depuis un dossier de CSV.

Deux formats supportés :
  * simplifié : ``eleves.csv``, ``cours.csv``, ``filiere.csv`` (jeu de test).
  * Synapse 2026 : ``etudiants_anonymises.csv``, ``Liste ECUE ...``, ``Liste
    des filières ...`` (§4 du cahier ; **format canonique**).

L'adaptateur produit toujours le même :class:`Instance`.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from .model import Instance, Occurrence, Student
from .constantes import FILIERE_TO_GROUPE, FILIERES_SANS_CRENEAU

JOUR2CODE = {"Lundi": "Lu", "Mardi": "Ma", "Mercredi": "Me", "Vendredi": "Ve"}
HEURE2CODE = {"8h30-11h45": "am", "13h30-16h45": "pm"}
_PERIODE2INT = {"S1-P1": 1, "S1-P2": 2, "S2-P3": 3, "S2-P4": 4}


def _creneau_from_jh(jour: str, heure: str) -> str:
    j, h = JOUR2CODE.get(str(jour).strip()), HEURE2CODE.get(str(heure).strip())
    return f"{j}-{h}" if j and h else ""


def _norm_langue(v: str) -> str:
    v = str(v).strip().lower()
    return "EN" if v.startswith(("en", "an")) else "FR"


def _norm_creneau(v) -> str:
    """Nettoie un créneau du CSV Synapse (parfois ``Ma_pm`` au lieu de ``Ma-pm``)."""
    if pd.isna(v):
        return ""
    return str(v).strip().replace("_", "-")


def load(data_dir: str | Path) -> Instance:
    d = Path(data_dir)
    if (d / "eleves.csv").exists():
        return _load_simplifie(d)
    if (d / "etudiants_anonymises.csv").exists():
        return _load_synapse(d)
    raise FileNotFoundError(f"Aucun format reconnu dans {d}")


# ---- format simplifié -----------------------------------------------------

def _load_simplifie(d: Path) -> Instance:
    cours = pd.read_csv(d / "cours.csv", sep=";")
    eleves = pd.read_csv(d / "eleves.csv", sep=";")
    par_bloc = (pd.read_csv(d / "eleves_par_bloc.csv", sep=";")
                if (d / "eleves_par_bloc.csv").exists() else None)

    occurrences: list[Occurrence] = []
    for i, r in cours.iterrows():
        titre = str(r["Intitulé"])
        occurrences.append(Occurrence(
            id_occ=f"O{i:03d}",
            id_ue=str(r["Code UE"]).strip(),
            bloc=str(r["Type ens."]).strip(),
            periode=int(r["Période"]),
            creneau=_creneau_from_jh(r["Jour"], r["Heure"]),
            langue=_norm_langue(r["Langue"]),
            fisea=("apprenti" in titre.lower()) or ("fisea" in titre.lower()),
            cap_max=int(r["Max."]),
            cap_min=int(r["Min."]),
            intitule=titre,
        ))

    blocs = sorted({o.bloc for o in occurrences})
    students: list[Student] = []
    for _, r in eleves.iterrows():
        info = str(r.get("info", "")).strip().lower()
        regime = "apprenti" if info == "apprenti" else "etudiant"
        langue = "EN" if info == "international" else "FR"
        groupes = [g for g in str(r["filiere"]).strip().upper().split("+")
                   if g in {"A", "B", "C"}]
        vpb = _voeux_par_bloc(r, blocs, occurrences, par_bloc)
        students.append(Student(
            id_eleve=str(r["eleveID"]).strip(),
            langue=langue, regime=regime,
            groupes_filiere=groupes, filieres_brutes=groupes,
            voeux_par_bloc=vpb,
        ))

    return Instance(students=students, occurrences=occurrences, blocs=blocs)


def _voeux_par_bloc(row, blocs, occurrences, par_bloc):
    if par_bloc is not None:
        sub = par_bloc[par_bloc["eleveID"] == row["eleveID"]]
        return {str(r["bloc"]): [c.strip() for c in str(r["classement"]).split("|") if c.strip()]
                for _, r in sub.iterrows()}
    classement = [c.strip() for c in str(row["classement_matieres"]).split("|")]
    out = {}
    for bloc in blocs:
        ues = {o.id_ue for o in occurrences if o.bloc == bloc}
        out[bloc] = [ue for ue in classement if ue in ues]
    return out


# ---- format Synapse 2026 --------------------------------------------------

def _load_synapse(d: Path) -> Instance:
    cours = pd.read_csv(d / "Liste ECUE du tronc commun de 2A 2026-2027.csv", sep=";")
    et = pd.read_csv(d / "etudiants_anonymises.csv", sep=";")
    voeux = (pd.read_csv(d / "voeux_par_bloc.csv", sep=";")
             if (d / "voeux_par_bloc.csv").exists() else None)

    occurrences = [Occurrence(
        id_occ=str(r["Idoccur"]),
        id_ue=str(r["Codeue"]),
        bloc=str(r["Bloc"]).strip(),
        periode=_PERIODE2INT.get(str(r["Periode"]).strip(), 0),
        creneau=_norm_creneau(r["Créneau prédéfini"]),
        langue=_norm_langue(r["Langues"]),
        fisea=str(r["FISEA"]).strip().upper() == "O",
        cap_max=int(r["Effectifmax"]),
        cap_min=int(r["Effectifmin"]),
        nb_deja_inscrits=int(r["Nbinscrits"]),
        intitule=str(r["Intituleoccur"]),
    ) for _, r in cours.iterrows()]

    blocs = sorted({o.bloc for o in occurrences})
    students: list[Student] = []
    for _, r in et.iterrows():
        regime_raw = str(r["Régime Inscrip."]).strip().lower()
        regime = ("apprenti" if regime_raw.startswith("apprenti")
                  else "auditeur" if regime_raw.startswith("auditeur")
                  else "etudiant")
        codes_bruts = [c.strip() for c in str(r["Filieres"]).split("$$") if c.strip()]
        groupes = sorted({FILIERE_TO_GROUPE[c] for c in codes_bruts
                          if c in FILIERE_TO_GROUPE})
        vpb: dict[str, list[str]] = {b: [] for b in blocs}
        if voeux is not None:
            sub = voeux[voeux["eleveID"].astype(str) == str(r["Id Personne"])]
            for _, row in sub.iterrows():
                vpb[str(row["bloc"])] = [c.strip() for c in
                                          str(row["classement"]).split("|") if c.strip()]
        students.append(Student(
            id_eleve=str(r["Id Personne"]),
            langue="FR" if str(r["Francophone"]).strip().upper() == "OUI" else "EN",
            regime=regime, groupes_filiere=groupes,
            filieres_brutes=codes_bruts, voeux_par_bloc=vpb,
        ))

    return Instance(students=students, occurrences=occurrences, blocs=blocs)
