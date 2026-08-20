from pathlib import Path
import sys
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from analysis_app.helpers import load_campaign_paths, unassignable_by_feasibility

students_path = REPO / 'data' / 'samples' / 'etudiants_anonymises.csv'
campaign_path = REPO / 'data' / 'samples' / 'campagne_synthetique.csv'
ecue_path = REPO / 'src' / 'data' / 'default_ecue.csv'

campaign = load_campaign_paths(students_path, campaign_path, ecue_path)
df = unassignable_by_feasibility(campaign)

out_path = REPO / 'out' / 'unassigned_reasons.csv'
out_path.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(out_path, index=False, sep=';')
print(f'Wrote {len(df)} rows to {out_path}')
print('\nFirst 10 rows:')
print(df.head(10).to_string(index=False))
