"""Fabriques minimales d'objets métier pour les tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.model import Student, Occurrence, Voeu, Campaign


def make_student(sid="s1", regime="student", francophone=True, filieres=("IMA",)):
    return Student(id_student=sid, id_dossier=sid, regime=regime,
                   francophone=francophone, filieres=list(filieres))


def make_occ(oid, period=1, slot="Ma-pm", language="FR", fisea=False,
             cap_max=30, id_ue=None, code_ue="UE1", already_enrolled=0):
    return Occurrence(id_occ=oid, id_ue=id_ue or f"ue_{oid}", code_ue=code_ue,
                      label=f"Cours {oid}", period=period, slot=slot,
                      language=language, fisea=fisea, cap_max=cap_max,
                      already_enrolled=already_enrolled)


def make_campaign(students, occurrences, voeux):
    return Campaign(id_campagne="test",
                    students={s.id_student: s for s in students},
                    occurrences={o.id_occ: o for o in occurrences},
                    voeux=voeux)
