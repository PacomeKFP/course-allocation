"""Chargement des trois entrées Synapse.

  * ``load_students(path)``    → dict[id_student, Student]
  * ``load_ecue(path=None)``   → dict[id_occ, Occurrence]  (défaut embarqué si None)
  * ``load_campaign(path, campagne_id)`` → list[Voeu]  (uniquement non-vides)
  * ``build_campaign(...)`` assemble le tout en :class:`Campaign`.
"""
from __future__ import annotations
from pathlib import Path
from typing import Tuple
import pandas as pd
from .model import Student, Occurrence, Voeu, Campaign

DEFAULT_ECUE = Path(__file__).with_name("default_ecue.csv")
_PERIOD = {"S1-P1": 1, "S1-P2": 2, "S2-P3": 3, "S2-P4": 4}
_REGIME = {"etudiant": "student", "apprentis": "apprentice",
           "apprenti": "apprentice", "auditeur libre": "auditor",
           "etudiant militaire": "student"}


def load_students(path: str | Path) -> dict[str, Student]:
    df = pd.read_csv(path, sep=";")
    out: dict[str, Student] = {}
    for _, r in df.iterrows():
        raw_regime = str(r["Régime Inscrip."]).strip().lower()
        filieres = [c.strip() for c in str(r.get("Filieres", "")).split("$$") if c.strip()]
        s = Student(
            id_student=str(r["Id Personne"]),
            id_dossier=str(r.get("IDDossierEtudiant", r["Id Personne"])),
            regime=_REGIME.get(raw_regime, "student"),
            francophone=str(r["Francophone"]).strip().upper() == "OUI",
            filieres=filieres,
        )
        out[s.id_student] = s
    return out


def load_ecue(path: str | Path | None = None) -> dict[str, Occurrence]:
    df = pd.read_csv(path or DEFAULT_ECUE, sep=";")
    out: dict[str, Occurrence] = {}
    for _, r in df.iterrows():
        slot = str(r["Créneau prédéfini"]).strip().replace("_", "-") \
               if pd.notna(r["Créneau prédéfini"]) else ""
        lang = "EN" if str(r["Langues"]).strip().lower().startswith(("en", "an")) else "FR"
        o = Occurrence(
            id_occ=str(r["Idoccur"]), id_ue=str(r["Idue"]),
            code_ue=str(r["Codeue"]).strip(), label=str(r["Intituleoccur"]),
            period=_PERIOD.get(str(r["Periode"]).strip(), 0),
            slot=slot, language=lang,
            fisea=str(r["FISEA"]).strip().upper() == "O",
            cap_max=int(r["Effectifmax"]), cap_min=int(r["Effectifmin"]),
            already_enrolled=int(r["Nbinscrits"]),
            bloc=str(r["Bloc"]).strip() if pd.notna(r.get("Bloc")) else "",
        )
        out[o.id_occ] = o
    return out


def load_campaign(path: str | Path) -> Tuple[list[Voeu], str]:
    """Charge un ``structure-export`` Synapse ; ignore les lignes vides (élève
    non concerné par la demande)."""
    df = pd.read_csv(path, sep=";")
    # Tri numérique explicite : l'ordre des colonnes du fichier n'est pas garanti.
    choice_cols = sorted((c for c in df.columns if c.startswith("IDOccur Choix ")),
                         key=lambda c: int(c.rsplit(" ", 1)[1]))
    voeux: list[Voeu] = []
    campaign_id = str(df["IDCampagne"].iloc[0]) if not df.empty else ""
    for _, r in df.iterrows():
        ranked = [str(int(r[c])) for c in choice_cols if pd.notna(r[c]) and str(r[c]).strip()]
        if not ranked:
            # TODO: peut etre qu'ici on pourrait recceuillir les étudiants qui n'ont pas de voeux pour les signaler dans le rapport
            continue
        voeux.append(Voeu(
            id_student=str(r["PersID"]),
            id_demande=str(r["IDDemande"]),
            ranked_occurrences=ranked,
        ))
    return voeux, campaign_id


def build_campaign(students_path, campaign_path, ecue_path=None) -> Campaign:
    students = load_students(students_path)
    occurrences = load_ecue(ecue_path)
    voeux, campaign_id = load_campaign(campaign_path)
    voeux = [v for v in voeux if v.id_student in students]
    return Campaign(id_campagne=campaign_id, students=students,
                    occurrences=occurrences, voeux=voeux)
