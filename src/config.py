"""Project paths and constants."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
PREDICTIONS = ROOT / "predictions"
MODELS_DIR = ROOT / "models"
DOCS = ROOT / "docs"

MARTJ42_URLS = {
    "results": "https://raw.githubusercontent.com/martj42/international_results/master/results.csv",
    "goalscorers": "https://raw.githubusercontent.com/martj42/international_results/master/goalscorers.csv",
    "shootouts": "https://raw.githubusercontent.com/martj42/international_results/master/shootouts.csv",
    "former_names": "https://raw.githubusercontent.com/martj42/international_results/master/former_names.csv",
}

ELO_URL = "https://www.eloratings.net/World.tsv"

# WC 2026 Round of 32 pairings (post group stage, Jun 2026)
R32_FIXTURES = [
    {"id": "r32_1", "home": "Netherlands", "away": "Japan", "date": "2026-06-28"},
    {"id": "r32_2", "home": "Argentina", "away": "Senegal", "date": "2026-06-28"},
    {"id": "r32_3", "home": "France", "away": "Mexico", "date": "2026-06-29"},
    {"id": "r32_4", "home": "England", "away": "Colombia", "date": "2026-06-29"},
    {"id": "r32_5", "home": "Brazil", "away": "Ecuador", "date": "2026-06-30"},
    {"id": "r32_6", "home": "Germany", "away": "USA", "date": "2026-06-30"},
    {"id": "r32_7", "home": "Spain", "away": "Morocco", "date": "2026-07-01"},
    {"id": "r32_8", "home": "Portugal", "away": "Uruguay", "date": "2026-07-01"},
    {"id": "r32_9", "home": "Belgium", "away": "Switzerland", "date": "2026-07-02"},
    {"id": "r32_10", "home": "Croatia", "away": "Denmark", "date": "2026-07-02"},
    {"id": "r32_11", "home": "Italy", "away": "Austria", "date": "2026-07-03"},
    {"id": "r32_12", "home": "Poland", "away": "South Korea", "date": "2026-07-03"},
]

R16_BRACKET = [
    ("r16_1", "r32_1", "r32_2"),
    ("r16_2", "r32_3", "r32_4"),
    ("r16_3", "r32_5", "r32_6"),
    ("r16_4", "r32_7", "r32_8"),
    ("r16_5", "r32_9", "r32_10"),
    ("r16_6", "r32_11", "r32_12"),
]

# Team name normalization map (common variants)
TEAM_ALIASES = {
    "Korea Republic": "South Korea",
    "Korea, South": "South Korea",
    "Korea DPR": "North Korea",
    "United States": "USA",
    "Czech Republic": "Czechia",
    "Republic of Ireland": "Ireland",
    "IR Iran": "Iran",
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "DR Congo": "DR Congo",
    "Congo DR": "DR Congo",
    "Cabo Verde": "Cape Verde",
    "Bosnia and Herzegovina": "Bosnia and Herzegovina",
    "United States": "USA",
    "USMNT": "USA",
}
