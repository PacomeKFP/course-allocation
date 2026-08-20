"""Tests de la chaîne de priorités et du solveur MIP."""
from tests.conftest import *  # noqa: F401,F403
from src.data.model import Voeu
from src.solvers import PriorityChain, MipSolver, empty_assignment
from src.solvers.base import rank


def _solve(campaign):
    a = empty_assignment(campaign)
    pre = PriorityChain().apply(campaign, a)
    return MipSolver(time_limit_s=10).solve(campaign, pre_assignment=pre)


def test_rank():
    v = Voeu("s", "d", ["a", "b", "c"])
    assert rank(v, "a") == 1 and rank(v, "c") == 3 and rank(v, "zzz") == 4


def test_priority_no_slot_conflict_between_demandes():
    """Un élève prioritaire ne doit pas recevoir deux cours au même créneau
    via deux demandes différentes (bug : la chaîne ignore les conflits)."""
    s = make_student("s1", francophone=False)  # prioritaire anglophone
    o1 = make_occ("o1", slot="Ma-pm", language="EN")
    o2 = make_occ("o2", slot="Ma-pm", language="EN")  # même instant
    c = make_campaign([s], [o1, o2],
                      [Voeu("s1", "d1", ["o1"]), Voeu("s1", "d2", ["o2"])])
    a = _solve(c)
    slots = [c.occurrences[o].slot for o in a.values() if o]
    assert len(slots) == len(set(slots))


def test_priority_respects_capacity():
    s1 = make_student("s1", francophone=False)
    s2 = make_student("s2", francophone=False)
    o = make_occ("o1", language="EN", cap_max=1)
    c = make_campaign([s1, s2], [o],
                      [Voeu("s1", "d1", ["o1"]), Voeu("s2", "d1", ["o1"])])
    a = _solve(c)
    assert sum(1 for v in a.values() if v == "o1") <= 1


def test_mip_unique_ue_per_student():
    s = make_student("s1")
    o1 = make_occ("o1", id_ue="ueX", slot="Ma-pm")
    o2 = make_occ("o2", id_ue="ueX", slot="Ma-am")  # même UE, autre créneau
    c = make_campaign([s], [o1, o2],
                      [Voeu("s1", "d1", ["o1", "o2"]), Voeu("s1", "d2", ["o1", "o2"])])
    a = _solve(c)
    ues = [c.occurrences[o].id_ue for o in a.values() if o]
    assert len(ues) == len(set(ues))


def test_mip_prefers_better_rank():
    s1, s2 = make_student("s1"), make_student("s2")
    o = make_occ("o1", cap_max=1)
    # s1 classe o1 en 1er, s2 en 2e -> s1 doit l'obtenir
    o_other = make_occ("o2", slot="Ma-am", cap_max=1)
    c = make_campaign([s1, s2], [o, o_other],
                      [Voeu("s1", "d1", ["o1", "o2"]),
                       Voeu("s2", "d1", ["o2", "o1"])])
    a = _solve(c)
    assert a[("s1", "d1")] == "o1"
    assert a[("s2", "d1")] == "o2"


def test_mip_already_enrolled_reduces_capacity():
    s = make_student("s1")
    o = make_occ("o1", cap_max=2, already_enrolled=2)  # complet
    c = make_campaign([s], [o], [Voeu("s1", "d1", ["o1"])])
    a = _solve(c)
    assert a[("s1", "d1")] is None
