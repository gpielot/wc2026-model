"""Real FIFA World Cup 2026 fixtures and results (from martj42 + FIFA schedule)."""

from __future__ import annotations

# Completed Round of 32 through July 1, 2026 (+ shootout winners for 1-1 ties)
WC2026_R32_RESULTS = [
    {"date": "2026-06-28", "home": "South Africa", "away": "Canada", "home_goals": 0, "away_goals": 1, "winner": "Canada"},
    {"date": "2026-06-29", "home": "Brazil", "away": "Japan", "home_goals": 2, "away_goals": 1, "winner": "Brazil"},
    {"date": "2026-06-29", "home": "Germany", "away": "Paraguay", "home_goals": 1, "away_goals": 1, "winner": "Paraguay", "shootout": True},
    {"date": "2026-06-29", "home": "Netherlands", "away": "Morocco", "home_goals": 1, "away_goals": 1, "winner": "Morocco", "shootout": True},
    {"date": "2026-06-30", "home": "Ivory Coast", "away": "Norway", "home_goals": 1, "away_goals": 2, "winner": "Norway"},
    {"date": "2026-06-30", "home": "France", "away": "Sweden", "home_goals": 3, "away_goals": 0, "winner": "France"},
    {"date": "2026-06-30", "home": "Mexico", "away": "Ecuador", "home_goals": 2, "away_goals": 0, "winner": "Mexico"},
    {"date": "2026-07-01", "home": "England", "away": "DR Congo", "home_goals": 2, "away_goals": 1, "winner": "England"},
    {"date": "2026-07-01", "home": "Belgium", "away": "Senegal", "home_goals": 3, "away_goals": 2, "winner": "Belgium", "extra_time": True},
    {"date": "2026-07-01", "home": "USA", "away": "Bosnia and Herzegovina", "home_goals": 2, "away_goals": 0, "winner": "USA"},
]

# Remaining R32 (scheduled — update scores when played)
WC2026_R32_PENDING = [
    {"id": "r32_13", "date": "2026-07-02", "home": "Spain", "away": "Austria"},
    {"id": "r32_14", "date": "2026-07-02", "home": "Portugal", "away": "Croatia"},
    {"id": "r32_15", "date": "2026-07-02", "home": "Switzerland", "away": "Algeria"},
    {"id": "r32_16", "date": "2026-07-03", "home": "Australia", "away": "Egypt"},
    {"id": "r32_17", "date": "2026-07-03", "home": "Argentina", "away": "Cape Verde"},
    {"id": "r32_18", "date": "2026-07-03", "home": "Colombia", "away": "Ghana"},
]

# Confirmed Round of 16 fixtures (FIFA bracket)
WC2026_R16_FIXTURES = [
    {"id": "r16_1", "date": "2026-07-04", "home": "Canada", "away": "Morocco", "venue": "Houston"},
    {"id": "r16_2", "date": "2026-07-04", "home": "Paraguay", "away": "France", "venue": "Philadelphia"},
    {"id": "r16_3", "date": "2026-07-05", "home": "Brazil", "away": "Norway", "venue": "New York/New Jersey"},
    {"id": "r16_4", "date": "2026-07-05", "home": "Mexico", "away": "England", "venue": "Mexico City"},
    {"id": "r16_5", "date": "2026-07-06", "home": "USA", "away": "Belgium", "venue": "Seattle"},
]

# R16 slots that depend on remaining R32 winners
WC2026_R16_PENDING = [
    {
        "id": "r16_6",
        "date": "2026-07-06",
        "home_slot": "Winner: Portugal vs Croatia",
        "away_slot": "Winner: Spain vs Austria",
        "venue": "Dallas",
        "depends_on": [("r32_13", "winner"), ("r32_14", "winner")],
    },
    {
        "id": "r16_7",
        "date": "2026-07-07",
        "home_slot": "Winner: Argentina vs Cape Verde",
        "away_slot": "Winner: Australia vs Egypt",
        "venue": "Atlanta",
        "depends_on": [("r32_16", "winner"), ("r32_17", "winner")],
    },
    {
        "id": "r16_8",
        "date": "2026-07-07",
        "home_slot": "Winner: Colombia vs Ghana",
        "away_slot": "Winner: Switzerland vs Algeria",
        "venue": "Vancouver",
        "depends_on": [("r32_15", "winner"), ("r32_18", "winner")],
    },
]
