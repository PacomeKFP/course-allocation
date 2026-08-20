"""Tests de propriétés sur des campagnes synthétiques variées et massives.

Pour chaque scénario généré, on vérifie les invariants métier :
  1. le résultat passe le validateur (0 violation de règle dure) ;
  2. toute paire (élève, demande) a une clé dans l'affectation ;
  3. tout rang obtenu ≤ nombre de vœux classés ;
  4. les statistiques globales sont cohérentes (comptes, taux ∈ [0,1]) ;
  5. une demande structurellement impossible (analyze_demande) n'est jamais servie.
"""
from tests.conftest import *  # noqa: F401,F403 — pose sys.path
import pytest
from synthesizer.generator import ProfileMix, CampaignMix, generate_all
from src.data.loaders import build_campaign
from src.solvers import PriorityChain, MipSolver, empty_assignment
from src.reporting import Report
from src.validate import validate_assignment, analyze_demande

TIME_LIMIT = 20  # secondes max par scénario — reste rapide en CI

SCENARIOS = {
    # petite promotion équilibrée
    "tiny_20":       dict(n_total=20,  pct_apprentis=0.10, pct_anglophones=0.10),
    # promotion moyenne, beaucoup d'anglophones
    "anglo_120":     dict(n_total=120, pct_apprentis=0.05, pct_anglophones=0.40),
    # beaucoup d'apprentis (pression sur les FISEA)
    "apprenti_150":  dict(n_total=150, pct_apprentis=0.35, pct_anglophones=0.10),
    # promotion très déséquilibrée vers le groupe C
    "groupC_200":    dict(n_total=200, pct_apprentis=0.10, pct_anglophones=0.10,
                          weights_group={"A": 1, "B": 1, "C": 5}),
    # gros volume
    "big_400":       dict(n_total=400, pct_apprentis=0.12, pct_anglophones=0.15),
}


def _run(students_df, campaign_df, tmp_path, seed):
    sp, cp = tmp_path / f"stu_{seed}.csv", tmp_path / f"camp_{seed}.csv"
    students_df.to_csv(sp, sep=";", index=False)
    campaign_df.to_csv(cp, sep=";", index=False)
    campaign = build_campaign(sp, cp)
    a = empty_assignment(campaign)
    pre = PriorityChain().apply(campaign, a)
    assignment = MipSolver(time_limit_s=TIME_LIMIT).solve(campaign, pre_assignment=pre)
    return campaign, assignment


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_generated_campaign_invariants(name, tmp_path):
    kw = SCENARIOS[name]
    profile = ProfileMix(seed=hash(name) % 1000, **kw)
    students_df, campaign_df = generate_all(profile, CampaignMix(seed=profile.seed))
    campaign, assignment = _run(students_df, campaign_df, tmp_path, profile.seed)

    # 1. Zéro violation de règle dure — l'invariant le plus important.
    violations = validate_assignment(campaign, assignment)
    assert violations == [], f"[{name}] {len(violations)} violations : {violations[:3]}"

    # 2. Toutes les paires attendues ont une clé.
    expected = {(v.id_student, v.id_demande) for v in campaign.voeux}
    assert set(assignment) == expected

    # 3. Rang obtenu toujours dans la liste classée.
    from src.solvers.base import rank
    for v in campaign.voeux:
        oid = assignment.get((v.id_student, v.id_demande))
        if oid:
            assert rank(v, oid) <= len(v.ranked_occurrences)

    # 4. Cohérence des statistiques.
    stats = Report(campaign, assignment).stats_global()
    assert stats["n_expected"] == len(campaign.voeux)
    assert stats["n_assigned"] <= stats["n_expected"]
    assert 0.0 <= stats["assignment_rate"] <= 1.0
    assert 0.0 <= stats["first_choice_share"] <= stats["top3_share"] <= 1.0

    # 5. Jamais d'affectation sur une demande structurellement impossible.
    for v in campaign.voeux:
        if assignment.get((v.id_student, v.id_demande)):
            assert analyze_demande(campaign, v.id_student, v.id_demande).satisfiable


def test_completely_saturated_demande_is_left_unassigned(tmp_path):
    """Capacité totale < nombre de demandeurs : les perdants doivent être None
    (pas de dépassement, pas de crash)."""
    studs = [make_student(f"s{i}") for i in range(5)]
    o = make_occ("only", cap_max=2)
    c = make_campaign(studs, [o], [Voeu(s.id_student, "d1", ["only"]) for s in studs])
    a = empty_assignment(c)
    a = MipSolver(time_limit_s=5).solve(c, pre_assignment=a)
    assert validate_assignment(c, a) == []
    assert sum(1 for v in a.values() if v) == 2  # exactement la capacité


def test_all_wishes_impossible_everyone_unassigned():
    """Anglophones sur campagne 100 % FR : rien d'assignable, pas de crash."""
    studs = [make_student(f"g{i}", francophone=False) for i in range(4)]
    occs = [make_occ("fr1"), make_occ("fr2", slot="Ma-am")]
    c = make_campaign(studs, occs, [Voeu(s.id_student, "d1", ["fr1", "fr2"]) for s in studs])
    a = empty_assignment(c)
    a = MipSolver(time_limit_s=5).solve(c, pre_assignment=a)
    assert all(v is None for v in a.values())
    assert validate_assignment(c, a) == []
