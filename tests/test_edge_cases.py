"""Cas limites déterministes — données adversariales construites à la main.

Chaque test cible un comportement à risque : données manquantes, inconnues,
dégénérées ou contradictoires. L'attendu : pas de crash + résultat validé.
"""
from tests.conftest import *  # noqa: F401,F403
from src.data.model import Voeu
from src.solvers import PriorityChain, MipSolver, empty_assignment
from src.validate import validate_assignment, analyze_demande


def _solve(c):
    a = empty_assignment(c)
    return MipSolver(time_limit_s=5).solve(c, pre_assignment=PriorityChain().apply(c, a))


def test_voeu_references_unknown_occurrences():
    """Vœux pointant vers des id_occ absents du catalogue : ignorés proprement."""
    s = make_student("s1")
    o = make_occ("real")
    c = make_campaign([s], [o], [Voeu("s1", "d1", ["ghost1", "real", "ghost2"])])
    a = _solve(c)
    assert a[("s1", "d1")] == "real"
    assert validate_assignment(c, a) == []


def test_occurrence_without_slot_is_never_assigned():
    s = make_student("s1")
    o = make_occ("noslot", slot="")
    c = make_campaign([s], [o], [Voeu("s1", "d1", ["noslot"])])
    a = _solve(c)
    assert a[("s1", "d1")] is None
    assert not analyze_demande(c, "s1", "d1").satisfiable


def test_unknown_period_occurrence_rejected():
    s = make_student("s1")
    o = make_occ("p0", period=0)
    c = make_campaign([s], [o], [Voeu("s1", "d1", ["p0"])])
    a = _solve(c)
    assert a[("s1", "d1")] is None
    assert validate_assignment(c, a) == []


def test_zero_capacity_occurrence():
    s = make_student("s1")
    o = make_occ("full", cap_max=0)
    c = make_campaign([s], [o], [Voeu("s1", "d1", ["full"])])
    a = _solve(c)
    assert a[("s1", "d1")] is None


def test_student_without_filiere_gets_any_slot():
    """Filière vide (auditeur PEI) : aucune contrainte de créneau ni jour d'entreprise."""
    s = make_student("s1", regime="auditor", filieres=())
    o = make_occ("o1", slot="Lu-am")  # créneau filière A — bloqué pour les autres
    c = make_campaign([s], [o], [Voeu("s1", "d1", ["o1"])])
    a = _solve(c)
    assert a[("s1", "d1")] == "o1"


def test_student_with_unmapped_filiere():
    """Filière absente de FILIERE_TO_GROUPE (ex. TSIA) : pas de contrainte."""
    s = make_student("s1", filieres=("TSIA",))
    o = make_occ("o1", slot="Lu-am")
    c = make_campaign([s], [o], [Voeu("s1", "d1", ["o1"])])
    a = _solve(c)
    assert a[("s1", "d1")] == "o1"


def test_duplicate_ranked_occurrence_in_one_voeu():
    """Un élève classe deux fois la même occurrence : ne doit pas la recevoir 2×."""
    s = make_student("s1")
    o = make_occ("o1", cap_max=5)
    c = make_campaign([s], [o], [Voeu("s1", "d1", ["o1", "o1"]),
                                 Voeu("s1", "d2", ["o1"])])
    a = _solve(c)
    assert list(a.values()).count("o1") <= 1
    assert validate_assignment(c, a) == []


def test_anglophone_apprentice_fisea_fr_blocked():
    """Apprenti anglophone : FISEA en FR reste interdit (règle langue prioritaire)."""
    s = make_student("s1", regime="apprentice", francophone=False, filieres=("CYBER",))
    fisea_fr = make_occ("fi_fr", fisea=True, language="FR", slot="Ma-am")
    c = make_campaign([s], [fisea_fr], [Voeu("s1", "d1", ["fi_fr"])])
    a = _solve(c)
    assert a[("s1", "d1")] is None
    analysis = analyze_demande(c, "s1", "d1")
    assert not analysis.satisfiable
    assert "fi_fr" in analysis.impossibles


def test_student_in_voeux_but_not_in_students_is_flagged_by_validator():
    """Ligne de vœu orpheline (élève inconnu) : filtrée au chargement ;
    si elle arrive quand même dans une affectation, le validateur la signale."""
    s = make_student("known")
    o = make_occ("o1")
    c = make_campaign([s], [o], [Voeu("ghost", "d1", ["o1"])])
    a = {("ghost", "d1"): "o1"}
    kinds = {v.kind for v in validate_assignment(c, a)}
    assert "hors_voeux" in kinds
