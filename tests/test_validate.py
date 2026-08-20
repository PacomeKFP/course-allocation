"""Tests du validateur d'affectation et de l'analyseur de satisfiabilité."""
from tests.conftest import *  # noqa: F401,F403
from src.data.model import Voeu
from src.solvers import PriorityChain, MipSolver, empty_assignment
from src.validate import validate_assignment, analyze_demande


def _solve(campaign):
    a = empty_assignment(campaign)
    pre = PriorityChain().apply(campaign, a)
    return MipSolver(time_limit_s=10).solve(campaign, pre_assignment=pre)


def test_clean_assignment_has_no_violation():
    s = make_student("s1")
    o = make_occ("o1")
    c = make_campaign([s], [o], [Voeu("s1", "d1", ["o1"])])
    a = _solve(c)
    assert a[("s1", "d1")] == "o1"
    assert validate_assignment(c, a) == []


def test_detects_infeasible_assignment():
    s = make_student("s1", regime="student")
    o = make_occ("o1", fisea=True)
    c = make_campaign([s], [o], [Voeu("s1", "d1", ["o1"])])
    bad = {("s1", "d1"): "o1"}  # non-apprenti sur cours FISEA
    kinds = {v.kind for v in validate_assignment(c, bad)}
    assert "infaisable" in kinds


def test_detects_overcapacity():
    studs = [make_student(f"s{i}") for i in range(3)]
    o = make_occ("o1", cap_max=2)
    c = make_campaign(studs, [o], [Voeu(s.id_student, "d1", ["o1"]) for s in studs])
    bad = {(s.id_student, "d1"): "o1" for s in studs}
    assert any(v.kind == "capacité" for v in validate_assignment(c, bad))


def test_detects_slot_conflict_and_duplicate_ue():
    s = make_student("s1")
    o1 = make_occ("o1", id_ue="uA", slot="Ma-pm")
    o2 = make_occ("o2", id_ue="uB", slot="Ma-pm")  # conflit horaire avec o1
    o3 = make_occ("o3", id_ue="uA", slot="Ma-am")  # même UE que o1
    c = make_campaign([s], [o1, o2, o3],
                      [Voeu("s1", "d1", ["o1"]), Voeu("s1", "d2", ["o2"]),
                       Voeu("s1", "d3", ["o3"])])
    bad = {("s1", "d1"): "o1", ("s1", "d2"): "o2", ("s1", "d3"): "o3"}
    kinds = {v.kind for v in validate_assignment(c, bad)}
    assert {"conflit_horaire", "ue_en_double"} <= kinds


def test_detects_unranked_occurrence():
    s = make_student("s1")
    o1, o2 = make_occ("o1"), make_occ("o2", slot="Ma-am")
    c = make_campaign([s], [o1, o2], [Voeu("s1", "d1", ["o1"])])
    bad = {("s1", "d1"): "o2"}  # jamais classé
    assert any(v.kind == "hors_voeux" for v in validate_assignment(c, bad))


def test_analyze_demande_splits_possible_impossible():
    s = make_student("s1", regime="student", francophone=False)
    ok = make_occ("ok", language="EN", slot="Ma-am")
    fr = make_occ("fr", language="FR", slot="Ma-am")
    fisea = make_occ("fi", language="EN", fisea=True, slot="Ma-pm")
    c = make_campaign([s], [ok, fr, fisea],
                      [Voeu("s1", "d1", ["fr", "fi", "ok"])])
    a = analyze_demande(c, "s1", "d1")
    assert a.possibles == ["ok"]
    assert set(a.impossibles) == {"fr", "fi"}
    assert a.satisfiable


def test_analyze_demande_unsatisfiable_when_all_blocked():
    s = make_student("s1", francophone=False)
    fr1, fr2 = make_occ("a", language="FR"), make_occ("b", language="FR", slot="Ma-am")
    c = make_campaign([s], [fr1, fr2], [Voeu("s1", "d1", ["a", "b"])])
    assert not analyze_demande(c, "s1", "d1").satisfiable


def test_full_pipeline_result_is_valid_on_varied_data():
    """Scénario riche : mix apprentis/étudiants/anglophones, capacités
    serrées, inscrits préexistants — le résultat doit passer le validateur."""
    studs = [make_student(f"e{i}") for i in range(6)]
    studs += [make_student(f"a{i}", regime="apprentice", filieres=("CYBER",))
              for i in range(3)]
    studs += [make_student(f"g{i}", francophone=False) for i in range(3)]
    occs = [
        make_occ("EN1", language="EN", cap_max=2),
        make_occ("EN2", language="EN", slot="Ma-am", cap_max=2, already_enrolled=1),
        make_occ("FR1", language="FR", cap_max=3),
        make_occ("FI1", language="EN", fisea=True, slot="Ve-pm", cap_max=2),
        make_occ("FI2", language="FR", fisea=True, slot="Lu-pm", cap_max=2),
    ]
    voeux = []
    for s in studs:
        ranked = [o.id_occ for o in occs]
        voeux.append(Voeu(s.id_student, "d1", ranked))
        voeux.append(Voeu(s.id_student, "d2", list(reversed(ranked))))
    c = make_campaign(studs, occs, voeux)
    a = _solve(c)
    assert validate_assignment(c, a) == []
    # chaque paire a une clé dans l'affectation (None admis si insatisfiable)
    assert set(a) == {(v.id_student, v.id_demande) for v in voeux}
