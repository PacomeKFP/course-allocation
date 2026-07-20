"""Charte visuelle Télécom Paris — CSS + composants d'en-tête.

Couleurs primaires : bleu institutionnel #003a6b, accent carmin #ce0e2d,
neutres gris/blanc. Sans émojis, sans effets décoratifs.
"""
from __future__ import annotations
import streamlit as st

BLEU = "#003a6b"
CARMIN = "#ce0e2d"
GRIS = "#f4f6fa"

_CSS = f"""
<style>
  /* Bloc principal : espacement plus généreux */
  .block-container {{ padding-top: 2.5rem; padding-bottom: 3rem; }}
  /* En-tête personnalisé */
  .app-header {{
      border-left: 4px solid {CARMIN};
      padding: 0.5rem 0 0.5rem 1rem;
      margin-bottom: 1.5rem;
  }}
  .app-header h1 {{
      color: {BLEU}; font-weight: 600; margin: 0;
      font-size: 1.65rem; letter-spacing: -0.01em;
  }}
  .app-header .subtitle {{
      color: #4a5568; font-size: 0.95rem; margin-top: 0.15rem;
  }}
  /* KPI cards */
  [data-testid="stMetric"] {{
      background: {GRIS};
      border-radius: 6px;
      padding: 0.8rem 1rem;
      border-left: 3px solid {BLEU};
  }}
  [data-testid="stMetricLabel"] {{
      color: {BLEU}; font-weight: 600; font-size: 0.85rem;
      text-transform: uppercase; letter-spacing: 0.03em;
  }}
  [data-testid="stMetricValue"] {{ color: #1a1a1a; }}
  /* Onglets plus lisibles */
  .stTabs [data-baseweb="tab-list"] button {{
      font-weight: 500; padding-top: 0.6rem; padding-bottom: 0.6rem;
  }}
  .stTabs [aria-selected="true"] {{
      color: {BLEU} !important; border-bottom-color: {CARMIN} !important;
  }}
  /* Sidebar : titres section */
  section[data-testid="stSidebar"] h3 {{
      color: {BLEU}; font-size: 0.9rem;
      text-transform: uppercase; letter-spacing: 0.04em;
      margin-top: 1.2rem; margin-bottom: 0.4rem;
  }}
</style>
"""


def apply_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def header(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="app-header"><h1>{title}</h1>'
        f'<div class="subtitle">{subtitle}</div></div>',
        unsafe_allow_html=True)


def metric_row(items: list[tuple[str, object, str | None]]) -> None:
    """Rangée de KPI, appel unique : ``metric_row([(label, val, help), …])``."""
    cols = st.columns(len(items))
    for col, (label, val, help_) in zip(cols, items):
        col.metric(label, val, help=help_)
