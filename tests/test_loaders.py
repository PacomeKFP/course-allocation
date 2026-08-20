"""Tests des chargeurs Synapse."""
from tests.conftest import *  # noqa: F401,F403 — pose sys.path
from src.data.loaders import load_students, load_campaign, load_ecue, build_campaign


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_load_students_regimes(tmp_path):
    p = _write(tmp_path, "etu.csv",
               "Id Personne;Régime Inscrip.;Francophone;Filieres\n"
               "1;Apprentis;OUI;CYBER\n"
               "2;Auditeur libre;NON;\n"
               "3;Etudiant;OUI;IMA$$MACS\n")
    students = load_students(p)
    assert students["1"].regime == "apprentice"
    assert students["2"].regime == "auditor"
    assert students["2"].francophone is False
    assert students["3"].filieres == ["IMA", "MACS"]


def test_load_campaign_choice_order_follows_rank_not_alphabetical(tmp_path):
    """Les colonnes 'IDOccur Choix N' doivent être lues dans l'ordre 1,2,...,10
    même si le fichier les déclare dans le désordre."""
    cols = ["PersID", "IDCampagne", "IDDemande",
            "IDOccur Choix 10", "IDOccur Choix 2", "IDOccur Choix 1"]
    p = _write(tmp_path, "camp.csv",
               ";".join(cols) + "\n" + "s1;42;d1;110;102;101\n")
    voeux, cid = load_campaign(p)
    assert cid == "42"
    assert voeux[0].ranked_occurrences == ["101", "102", "110"]


def test_load_campaign_skips_empty_rows(tmp_path):
    p = _write(tmp_path, "camp.csv",
               "PersID;IDCampagne;IDDemande;IDOccur Choix 1\n"
               "s1;42;d1;\ns2;42;d1;101\n")
    voeux, _ = load_campaign(p)
    assert len(voeux) == 1 and voeux[0].id_student == "s2"


def test_load_ecue_unknown_period_does_not_crash(tmp_path):
    p = _write(tmp_path, "ecue.csv",
               "Idoccur;Idue;Codeue;Intituleoccur;Periode;Créneau prédéfini;"
               "Nbinscrits;Effectifmin;Effectifmax;Langues;FISEA\n"
               "1;10;X;Cours X;Période inconnue;Me-am;0;5;30;Français;N\n")
    occs = load_ecue(p)
    assert occs["1"].period == 0


def test_build_campaign_filters_voeux_of_unknown_students(tmp_path):
    s = _write(tmp_path, "etu.csv",
               "Id Personne;Régime Inscrip.;Francophone;Filieres\n1;Etudiant;OUI;IMA\n")
    c = _write(tmp_path, "camp.csv",
               "PersID;IDCampagne;IDDemande;IDOccur Choix 1\n1;42;d1;101\n999;42;d1;101\n")
    campaign = build_campaign(s, c)
    assert [v.id_student for v in campaign.voeux] == ["1"]
