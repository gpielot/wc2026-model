"""Download and cache raw data sources."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import requests

from src.config import DATA_PROCESSED, DATA_RAW, ELO_URL, MARTJ42_URLS


def _download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return dest
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    return dest


def ingest_martj42() -> dict[str, pd.DataFrame]:
    """Download martj42 international results."""
    frames = {}
    for name, url in MARTJ42_URLS.items():
        path = DATA_RAW / "martj42" / f"{name}.csv"
        _download(url, path)
        frames[name] = pd.read_csv(path)
    return frames


def ingest_elo() -> pd.DataFrame:
    """Download eloratings.net world rankings snapshot."""
    path = DATA_RAW / "elo" / "World.tsv"
    _download(ELO_URL, path)
    df = pd.read_csv(path, sep="\t", header=None, usecols=[0, 2, 3], names=["rank", "code", "elo"])
    code_to_team = {
        "AR": "Argentina", "EN": "England", "ES": "Spain", "FR": "France", "BR": "Brazil",
        "DE": "Germany", "IT": "Italy", "NL": "Netherlands", "PT": "Portugal", "BE": "Belgium",
        "HR": "Croatia", "UY": "Uruguay", "CO": "Colombia", "MX": "Mexico", "US": "USA",
        "JP": "Japan", "KR": "South Korea", "SN": "Senegal", "MA": "Morocco", "EC": "Ecuador",
        "CH": "Switzerland", "DK": "Denmark", "AT": "Austria", "PL": "Poland", "CA": "Canada",
    }
    df["team"] = df["code"].map(code_to_team).fillna(df["code"])
    return df[["rank", "team", "code", "elo"]]


def ingest_statsbomb() -> Path:
    """Clone StatsBomb open-data if not present (sparse, shallow)."""
    dest = DATA_RAW / "statsbomb" / "open-data"
    if dest.exists() and (dest / "data" / "competitions.json").exists():
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [
                "git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
                "https://github.com/statsbomb/open-data.git", str(dest),
            ],
            check=True,
            timeout=120,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(dest), "sparse-checkout", "set", "data/competitions.json",
             "data/matches", "data/events", "data/lineups"],
            check=True,
            timeout=60,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"Warning: StatsBomb sparse clone failed ({e}), downloading competitions only")
        comps_dir = dest / "data"
        comps_dir.mkdir(parents=True, exist_ok=True)
        _download(
            "https://raw.githubusercontent.com/statsbomb/open-data/master/data/competitions.json",
            comps_dir / "competitions.json",
        )
    return dest


def ingest_wc2026_fixtures() -> list[dict]:
    """Store WC 2026 knockout fixtures."""
    from src.config import R32_FIXTURES

    out = DATA_RAW / "wc2026" / "r32_fixtures.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(R32_FIXTURES, indent=2))
    return R32_FIXTURES


def build_matches_table(martj42: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Normalize martj42 results into canonical matches table."""
    from src.config import TEAM_ALIASES

    df = martj42["results"].copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.rename(
        columns={
            "home_team": "home",
            "away_team": "away",
            "home_score": "home_goals",
            "away_score": "away_goals",
        }
    )

    def norm_team(name: str) -> str:
        if name in TEAM_ALIASES:
            return TEAM_ALIASES[name]
        return name

    df["home"] = df["home"].map(norm_team)
    df["away"] = df["away"].map(norm_team)
    df["neutral"] = df["neutral"].astype(bool)
    df["match_id"] = df.apply(
        lambda r: f"{r['date'].strftime('%Y%m%d')}_{r['home']}_{r['away']}", axis=1
    )
    df["total_goals"] = df["home_goals"] + df["away_goals"]
    df["goal_diff_home"] = df["home_goals"] - df["away_goals"]

    def outcome(row):
        if row["home_goals"] > row["away_goals"]:
            return "H"
        if row["home_goals"] < row["away_goals"]:
            return "A"
        return "D"

    df["result"] = df.apply(outcome, axis=1)
    return df.sort_values("date").reset_index(drop=True)


def build_elo_table(elo_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Elo snapshot."""
    return elo_df


def run_all_ingest() -> None:
    """Run full ingest pipeline and write processed parquet files."""
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    print("Ingesting martj42...")
    martj42 = ingest_martj42()
    matches = build_matches_table(martj42)
    matches.to_parquet(DATA_PROCESSED / "matches.parquet", index=False)
    martj42["former_names"].to_parquet(DATA_PROCESSED / "former_names.parquet", index=False)

    print("Ingesting Elo ratings...")
    try:
        elo = build_elo_table(ingest_elo())
        elo.to_parquet(DATA_PROCESSED / "elo_snapshot.parquet", index=False)
    except Exception as e:
        print(f"Warning: Elo ingest failed ({e}), will compute own Elo")

    print("Ingesting StatsBomb open data...")
    try:
        sb_path = ingest_statsbomb()
        comps_path = sb_path / "data" / "competitions.json"
        if comps_path.exists():
            shutil.copy(comps_path, DATA_PROCESSED / "statsbomb_competitions.json")
    except Exception as e:
        print(f"Warning: StatsBomb ingest failed ({e})")

    print("Saving WC2026 fixtures...")
    fixtures = ingest_wc2026_fixtures()
    pd.DataFrame(fixtures).to_parquet(DATA_PROCESSED / "wc2026_r32.parquet", index=False)

    print(f"Done. {len(matches)} international matches processed.")
