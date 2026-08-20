"""Génération Synapse fictive. Ne force PAS la faisabilité pour éprouver le solveur."""
from __future__ import annotations
import random
import string
import sys
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.data.model import Student as StudentModel
from src.data import load_ecue
from src.data.constants import FILIERE_TO_GROUPE

APPR_FILIERES = ["CYBER", "DSAI", "RIO", "SE"]
ALL_FILIERES = list(FILIERE_TO_GROUPE)


@dataclass
class ProfileMix:
    n_total: int = 320
    pct_apprentis: float = 0.10
    pct_anglophones: float = 0.10
    pct_auditeurs_pei: float = 0.02
    weights_group: dict = field(default_factory=lambda: {
                                "A": 1, "B": 2, "C": 3})
    seed: int = 42


@dataclass
class CampaignMix:
    # students will rank all available occurrences for each demande
    # seed controls randomness of ordering
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


def generate_campaign(students, ecue: dict, mix: CampaignMix,
                      demandes: list[str] | None = None,
                      enforce_feasibility: bool = False,
                      split_apprentis: bool = False,
                      max_choices: int | None = None):
    """Generate campaign: each student ranks all occurrences per demande.

    - ecue: dict[id_occ(str) -> Occurrence]
    - For each demande (bloc), split occurrences into public and apprentis_only.
    - For each student+demande, deterministic shuffle (seed derived from mix.seed, student id, demande id).
    - Apprentis include apprentis_only; final order is shuffled to avoid append bias.
    - If enforce_feasibility=True, filter final list by Feasibility.check (kept optional).
    - Padding to equal width is applied at the end.
    """
    ecue_df = _load_bloc_map()
    blocs = sorted(ecue_df["Bloc"].dropna().unique())
    demandes = demandes or [f"5440{i+1}" for i in range(len(blocs))]
    bloc_to_demande = dict(zip(blocs, demandes))

    # candidates per bloc (Idoccur as str)
    bloc_candidates: dict[str, list[str]] = {
        bloc: ecue_df[ecue_df["Bloc"] == bloc]["Idoccur"].tolist()
        for bloc in blocs
    }

    # split into public vs apprentis_only using ecue dict
    per_demande_public: dict[str, list[str]] = {}
    per_demande_appr: dict[str, list[str]] = {}
    for bloc, cands in bloc_candidates.items():
        pub, appr = [], []
        for cid in cands:
            occ = None
            if ecue:
                occ = ecue.get(str(cid)) or ecue.get(int(cid))
            if occ is None:
                pub.append(str(cid))
            else:
                if occ.fisea:
                    appr.append(str(cid))
                else:
                    pub.append(str(cid))
        per_demande_public[bloc] = pub
        per_demande_appr[bloc] = appr

    rows_data = []
    from src.rules.feasibility import Feasibility
    feas = Feasibility()
    for _, s in students.iterrows():
        sid = str(s["Id Personne"]) if "Id Personne" in s else str(
            s.get("PersID", ""))
        regime = str(s.get("Régime Inscrip.", "")).strip().lower()
        is_apprenti = regime.startswith("appr")
        for bloc, id_demande in bloc_to_demande.items():
            pub = list(per_demande_public.get(bloc, []))
            appr_list = list(per_demande_appr.get(bloc, []))

            # deterministic seed per student+demande
            key = f"{mix.seed}:{sid}:{id_demande}"
            seed = int(hashlib.sha256(
                key.encode()).hexdigest(), 16) & 0xFFFFFFFF
            rng = random.Random(seed)

            rng.shuffle(pub)
            final = list(pub)
            if is_apprenti and appr_list:
                rng.shuffle(appr_list)
                final.extend(appr_list)
                rng.shuffle(final)

            # optional feasibility filter
            if enforce_feasibility:
                # build a Student dataclass expected by Feasibility
                franc = s.get("Francophone", "OUI")
                franc_bool = True if str(franc).strip().lower() in (
                    "oui", "o", "true", "1") else False
                raw_fil = s.get("Filieres", "") or ""
                filieres = [f for f in str(raw_fil).split("$$") if f]
                reg = str(s.get("Régime Inscrip.", "")).strip().lower()
                if reg.startswith("appr"):
                    reg_norm = "apprentice"
                elif "auditeur" in reg or "auditor" in reg:
                    reg_norm = "auditor"
                else:
                    reg_norm = "student"
                student_obj = StudentModel(id_student=sid, id_dossier=sid,
                                           regime=reg_norm, francophone=franc_bool,
                                           filieres=filieres)

                kept = []
                for cid in final:
                    occ = ecue.get(str(cid)) or ecue.get(int(cid))
                    if occ is None:
                        continue
                    if feas.is_accessible(student_obj, occ):
                        kept.append(cid)
                final = kept

            # Students rank all occurrences offered to them (no truncation,
            # no simulated 'demandes vides'). FISEA occurrences are only
            # present in `final` for apprentices (handled above).

            rows_data.append({
                "PersID": s["Id Personne"],
                "IDDossierEtudiant": s["Id Personne"],
                "Nom": s["Nom"],
                "Prénom": s["Prenom"],
                "CampagneIntitulé": "Campagne synthétique",
                "IDCampagne": "544",
                "IDDemande": id_demande,
                "ranked": final,
                "is_apprenti": is_apprenti,
            })

    # If split_apprentis, determine demandes that are apprentis-only
    apprentis_only_demandes = set()
    if split_apprentis:
        for bloc in blocs:
            pub = per_demande_public.get(bloc, [])
            appr_list = per_demande_appr.get(bloc, [])
            if (not pub) and appr_list:
                apprentis_only_demandes.add(bloc_to_demande[bloc])

    def _build_df_from_rows(sub_rows, cap: int | None = None) -> pd.DataFrame:
        cap_choices = cap if cap is not None else max(
            (len(r["ranked"]) for r in sub_rows), default=0)
        rows_out = []
        for r in sub_rows:
            row = {k: r[k] for k in ("PersID", "IDDossierEtudiant", "Nom",
                                     "Prénom", "CampagneIntitulé", "IDCampagne", "IDDemande")}
            ranked = r["ranked"]
            for i in range(cap_choices):
                row[f"IDOccur Choix {i+1}"] = ranked[i] if i < len(
                    ranked) else ""
            rows_out.append(row)
        return pd.DataFrame(rows_out)

    if not split_apprentis:
        cap = max_choices if max_choices is not None else max(
            (len(r["ranked"]) for r in rows_data), default=0)
        return _build_df_from_rows(rows_data, cap)

    # split into two datasets: apprentices only (students who are apprentis)
    # and non-apprentis (students who are not apprentis) with apprentis-only demandes removed
    rows_appr = [r for r in rows_data if r.get("is_apprenti")]
    rows_non_appr = [r for r in rows_data if not r.get(
        "is_apprenti") and r.get("IDDemande") not in apprentis_only_demandes]

    cap_appr = max_choices if max_choices is not None else max(
        (len(r["ranked"]) for r in rows_appr), default=0)
    cap_non = max_choices if max_choices is not None else max(
        (len(r["ranked"]) for r in rows_non_appr), default=0)
    df_non = _build_df_from_rows(rows_non_appr, cap_non)
    df_appr = _build_df_from_rows(rows_appr, cap_appr)

    # return tuple (non_apprentis_df, apprentis_df)
    return df_non, df_appr


def generate_all(profile: ProfileMix, campaign: CampaignMix, *, enforce_feasibility: bool = False, split_apprentis: bool = False, max_choices: int | None = None, **kwargs):
    """Wrapper helper: generate students and campaign DataFrame.

    Accepts extra kwargs for backward compatibility (ignored).
    """
    students = generate_students(profile)
    camp = generate_campaign(
        students,
        load_ecue(),
        campaign,
        enforce_feasibility=enforce_feasibility,
        split_apprentis=split_apprentis,
        max_choices=max_choices,
    )
    return students, camp
