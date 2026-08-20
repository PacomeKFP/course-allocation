"""Test de non-régression bout-en-bout sur les données d'exemple."""
from pathlib import Path
from tests.conftest import *  # noqa: F401,F403 — pose sys.path
from src.pipeline import run_campaign
from src.solvers import MipSolver
from src.validate import validate_assignment

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "data" / "samples"


def test_pipeline_samples_produces_valid_assignment(tmp_path):
    campaign, assignment, report = run_campaign(
        SAMPLES / "etudiants_anonymises.csv",
        SAMPLES / "campagne_synthetique.csv",
        solver=MipSolver(time_limit_s=60), out_dir=tmp_path)

    violations = validate_assignment(campaign, assignment)
    assert violations == [], f"{len(violations)} violations : {violations[:3]}"

    stats = report.stats_global()
    assert stats["n_expected"] == len(campaign.voeux) > 0
    assert stats["assignment_rate"] > 0.95

    for name in ("synapse_import.csv", "non_affectes.csv", "remplissage.csv",
                 "stats_par_demande.csv", "stats_compensation.csv"):
        assert (tmp_path / name).exists(), name

    # Le rapport des non-affectés doit expliquer chaque échec résiduel.
    na = report.not_assigned()
    assert len(na) == stats["n_expected"] - stats["n_assigned"]
    assert na["cause"].str.len().gt(0).all()
