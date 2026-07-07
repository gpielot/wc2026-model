"""Real FIFA World Cup 2026 fixtures and results (from martj42 + FIFA schedule)."""

from __future__ import annotations

# Completed Round of 32 (all 16 ties)
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
    {"date": "2026-07-02", "home": "Spain", "away": "Austria", "home_goals": 3, "away_goals": 0, "winner": "Spain"},
    {"date": "2026-07-02", "home": "Portugal", "away": "Croatia", "home_goals": 2, "away_goals": 1, "winner": "Portugal"},
    {"date": "2026-07-02", "home": "Switzerland", "away": "Algeria", "home_goals": 2, "away_goals": 0, "winner": "Switzerland"},
    {"date": "2026-07-03", "home": "Australia", "away": "Egypt", "home_goals": 1, "away_goals": 1, "winner": "Egypt", "shootout": True},
    {"date": "2026-07-03", "home": "Argentina", "away": "Cape Verde", "home_goals": 3, "away_goals": 2, "winner": "Argentina", "extra_time": True},
    {"date": "2026-07-03", "home": "Colombia", "away": "Ghana", "home_goals": 1, "away_goals": 0, "winner": "Colombia"},
]

# Completed Round of 16 through July 6
WC2026_R16_RESULTS = [
    {"date": "2026-07-04", "home": "Canada", "away": "Morocco", "home_goals": 0, "away_goals": 3, "winner": "Morocco"},
    {"date": "2026-07-04", "home": "Paraguay", "away": "France", "home_goals": 0, "away_goals": 1, "winner": "France"},
    {"date": "2026-07-05", "home": "Brazil", "away": "Norway", "home_goals": 1, "away_goals": 2, "winner": "Norway"},
    {"date": "2026-07-05", "home": "Mexico", "away": "England", "home_goals": 2, "away_goals": 3, "winner": "England"},
    {"date": "2026-07-06", "home": "USA", "away": "Belgium", "home_goals": 1, "away_goals": 4, "winner": "Belgium"},
    {"date": "2026-07-06", "home": "Portugal", "away": "Spain", "home_goals": 0, "away_goals": 1, "winner": "Spain"},
]

# Remaining Round of 16 (scheduled — update scores when played)
WC2026_R16_PENDING = [
    {"id": "r16_7", "date": "2026-07-07", "home": "Argentina", "away": "Egypt", "venue": "Atlanta"},
    {"id": "r16_8", "date": "2026-07-07", "home": "Colombia", "away": "Switzerland", "venue": "Vancouver"},
]

# Confirmed quarter-final fixtures (FIFA bracket)
WC2026_QF_FIXTURES = [
    {"id": "qf_1", "date": "2026-07-09", "home": "France", "away": "Morocco", "venue": "Foxborough"},
    {"id": "qf_2", "date": "2026-07-10", "home": "Spain", "away": "Belgium", "venue": "Inglewood"},
    {"id": "qf_3", "date": "2026-07-11", "home": "Norway", "away": "England", "venue": "Miami"},
]

# QF slot that depends on remaining R16 winners
WC2026_QF_PENDING = [
    {
        "id": "qf_4",
        "date": "2026-07-11",
        "home_slot": "Winner: Argentina vs Egypt",
        "away_slot": "Winner: Colombia vs Switzerland",
        "venue": "Kansas City",
        "depends_on": [("r16_7", "winner"), ("r16_8", "winner")],
    },
]

# Legacy aliases used by older publish script
WC2026_R32_PENDING: list[dict] = []
WC2026_R16_FIXTURES = WC2026_R16_RESULTS  # historical; use R16_RESULTS + PENDING
