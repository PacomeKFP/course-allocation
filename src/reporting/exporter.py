"""Export au format ``structure-import des IPE des étudiants.csv``.

Une ligne par étudiant, colonnes :
    PersID ; IDDossierEtudiant ; IDCampagne ;
    IDDemande 1 ; IDOccur 1 ; ... ; IDDemande N ; IDOccur N

Les paires ``(IDDemande, IDOccur)`` sans affectation sont émises avec
``IDOccur`` vide (l'élève reste inscrit à sa demande, mais sans occurrence).
"""
from __future__ import annotations
import csv
from pathlib import Path
from ..data.model import Campaign, Assignment


def export_synapse_import(campaign: Campaign, assignment: Assignment,
                          path: str | Path) -> None:
    demandes = campaign.demandes()
    by_student: dict[str, dict[str, str]] = {}
    for (id_student, id_demande), id_occ in assignment.items():
        by_student.setdefault(id_student, {})[id_demande] = id_occ or ""

    header = ["PersID", "IDDossierEtudiant", "IDCampagne"]
    for i, _ in enumerate(demandes, 1):
        header += [f"IDDemande {i}", f"IDOccur {i}"]

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp, delimiter=";")
        writer.writerow(header)
        for id_student, choices in sorted(by_student.items()):
            s = campaign.students.get(id_student)
            row = [id_student, s.id_dossier if s else id_student, campaign.id_campagne]
            for id_demande in demandes:
                row += [id_demande, choices.get(id_demande, "")]
            writer.writerow(row)
