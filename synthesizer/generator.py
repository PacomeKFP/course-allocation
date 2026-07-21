"""Génération Synapse fictive. Ne force PAS la faisabilité pour éprouver le solveur."""
from __future__ import annotations
import random, string, sys
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.data import load_ecue
from src.data.constants import FILIERE_TO_GROUPE

APPR_FILIERES = ["CYBER", "DSAI", "RIO", "SE"]
ALL_FILIERES = list(FILIERE_TO_GROUPE)


@dataclass
class ProfileMix:
    n_total: int = 200
    pct_apprentis: float = 0.10
    pct_anglophones: float = 0.15
    pct_auditeurs_pei: float = 0.0
    weights_group: dict = field(default_factory=lambda: {"A": 1, "B": 1, "C": 1})
    seed: int = 42


@dataclass
class CampaignMix:
    n_voeux_min: int = 2
    n_voeux_max: int = 8
    pct_demandes_vides: float = 0.02
    seed: int = 42


def _hex(rng, n=16):
    return "".join(rng.choice(string.hexdigits[:16].lower()) for _ in range(n))


def _pick_two_filieres(rng, weights):
    w = [weights[FILIERE_TO_GROUPE[f]] for f in ALL_FILIERES]
    a, b = rng.choices(ALL_FILIERES, weights=w, k=2)
    while a == b: a, b = rng.choices(ALL_FILIERES, weights=w, k=2)
    return [a, b]


def generate_students(mix: ProfileMix) -> pd.DataFrame:
    rng = random.Random(mix.seed)
    n_appr = int(mix.n_total * mix.pct_apprentis)
    n_pei = int(mix.n_total * mix.pct_auditeurs_pei)
    n_eng = int(mix.n_total * mix.pct_anglophones)
    rows = []
    for i in range(mix.n_total):
        if i < n_appr:
            reg, fil, cur = "Apprentis", rng.choice(APPR_FILIERES), "24 mois"
        elif i < n_appr + n_pei:
            reg, fil, cur = "Auditeur libre", "", "1 semestre"
        else:
            reg, fil, cur = "Etudiant", "$$".join(_pick_two_filieres(rng, mix.weights_group)), "36 mois"
        is_eng = i >= mix.n_total - n_eng
        rows.append({"Id Personne": 300000 + i, "Nom": _hex(rng), "Prenom": _hex(rng),
                     "N° INE": _hex(rng), "Diplôme": "PEI" if reg == "Auditeur libre" else "ING",
                     "Cursus": cur, "Régime Inscrip.": reg,
                     "Francophone": "NON" if is_eng else "OUI", "Filieres": fil})
    return pd.DataFrame(rows)


def _load_bloc_map():
    df = pd.read_csv(Path(__file__).resolve().parent.parent
                     / "src" / "data" / "default_ecue.csv", sep=";")[["Idoccur", "Bloc"]]
    return df.assign(Idoccur=df["Idoccur"].astype(str), Bloc=df["Bloc"].str.strip())


def generate_campaign(students, ecue, mix: CampaignMix,
                       demandes: list[str] | None = None) -> pd.DataFrame:
    rng = random.Random(mix.seed)
    ecue_df = _load_bloc_map()
    blocs = sorted(ecue_df["Bloc"].dropna().unique())
    demandes = demandes or [f"5440{i+1}" for i in range(len(blocs))]
    bloc_to_demande = dict(zip(blocs, demandes))
    rows = []
    for _, s in students.iterrows():
        for bloc, id_demande in bloc_to_demande.items():
            cands = ecue_df[ecue_df["Bloc"] == bloc]["Idoccur"].tolist()
            if rng.random() < mix.pct_demandes_vides or not cands:
                ranked = []
            else:
                n = rng.randint(mix.n_voeux_min, min(mix.n_voeux_max, len(cands)))
                ranked = rng.sample(cands, n)
            row = {"PersID": s["Id Personne"], "IDDossierEtudiant": s["Id Personne"],
                   "Nom": s["Nom"], "Prénom": s["Prenom"],
                   "CampagneIntitulé": "Campagne synthétique", "IDCampagne": "544",
                   "IDDemande": id_demande}
            row.update({f"IDOccur Choix {i+1}": (ranked[i] if i < len(ranked) else "")
                        for i in range(14)})
            rows.append(row)
    return pd.DataFrame(rows)


def generate_all(profile: ProfileMix, campaign: CampaignMix):
    students = generate_students(profile)
    return students, generate_campaign(students, load_ecue(), campaign)
