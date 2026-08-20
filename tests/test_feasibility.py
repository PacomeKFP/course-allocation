"""Tests des règles de faisabilité (élève, occurrence)."""
from tests.conftest import *  # noqa: F401,F403
from src.rules.feasibility import Feasibility

F = Feasibility()


def test_slot_not_defined():
    s = make_student()
    o = make_occ("o1", slot="")
    assert "créneau non fixé" in F.slot_defined(s, o)


def test_fisea_reserved_to_apprentices():
    fisea = make_occ("o1", fisea=True)
    assert F.fisea_ok(make_student(regime="student"), fisea) is not None
    assert F.fisea_ok(make_student(regime="apprentice"), fisea) is None


def test_slot_free_blocks_group_slot():
    # Groupe B période 1 : créneaux occupés = Lu-pm, Ve-am
    s = make_student(filieres=("IMA",))
    assert F.slot_free(s, make_occ("o1", slot="Lu-pm")) is not None
    assert F.slot_free(s, make_occ("o2", slot="Ma-pm")) is None


def test_slot_free_unknown_period_does_not_crash():
    s = make_student(filieres=("IMA",))
    o = make_occ("o1", period=0)
    assert F.check(s, o)  # rejeté, sans lever KeyError


def test_slot_free_unknown_slot_does_not_crash():
    s = make_student(filieres=("IMA",))
    o = make_occ("o1", slot="Je-am")  # jeudi : absent de DAY_OF_SLOT
    assert isinstance(F.check(s, o), list)  # pas de KeyError


def test_company_day_apprentice():
    # CYBER = groupe A, période 1 : entreprise Jeudi+Vendredi
    s = make_student(regime="apprentice", filieres=("CYBER",))
    assert F.company_day(s, make_occ("o1", slot="Ve-am")) is not None
    assert F.company_day(s, make_occ("o2", slot="Lu-am")) is None
    # Pas apprenti -> règle inopérante
    assert F.company_day(make_student(), make_occ("o3", slot="Ve-am")) is None


def test_language_anglophone_needs_english():
    s = make_student(francophone=False)
    assert F.language(s, make_occ("o1", language="FR")) is not None
    assert F.language(s, make_occ("o2", language="EN")) is None


def test_check_accumulates_reasons():
    s = make_student(regime="student", francophone=False, filieres=("IMA",))
    o = make_occ("o1", slot="Lu-pm", language="FR", fisea=True)
    reasons = F.check(s, o)
    assert len(reasons) == 3  # FISEA + créneau filière + langue
