import pandas as pd 
import numpy as np 
import requests
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path 
import unicodedata
import time 

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.rate_limit import wait_for_rate_limit

def remove_accents(name):
    if name is None:
        return None

    normalized = unicodedata.normalize("NFKD", name)
    return "".join(
        char for char in normalized
        if not unicodedata.combining(char)
    )

def get_year_regular_player_pg_stats(year):
    url = f"https://www.basketball-reference.com/leagues/{"NBA" if year >= 1950 else "BAA"}_{year}_per_game.html"

    df = pd.read_html(url, attrs={"id" : "per_game_stats"})[0]
    df["Player"] = df["Player"].apply(remove_accents)
    df = df.drop(columns=["Rk", "Awards"])
    df = df.loc[df.Team.ne("2TM"), :]

    return df

def get_year_advanced_player_pg_stats(year):
    url = f"https://www.basketball-reference.com/leagues/{"NBA" if year >= 1950 else "BAA"}_{year}_advanced.html"

    df = pd.read_html(url, attrs={"id" : "advanced"})[0]
    df["Player"] = df["Player"].apply(remove_accents)
    df = df.drop(columns=["Rk", "Awards"])
    df = df.loc[df.Team.ne("2TM"), :]

    return df 

def check_for_player_pg_stats_to_scrape(stat_type, page_limit, start_time = None, pages_visited = 0):
    db_path = Path("~/Personal Project/data/nba.db").expanduser()
    engine = create_engine(f"sqlite:///{db_path}")

    try:
        with engine.connect() as conn:
            query = text(f"SELECT MAX(Year) FROM {"player_pg_stats" if stat_type == "regular" else "advanced_player_pg_stats"}")
            last_year_in_db = conn.execute(query).fetchone()[0]
    except SQLAlchemyError:
        last_year_in_db = None

    if last_year_in_db is None:
        last_year_in_db = 2026

    start_of_new_years = next_year_to_check = int(last_year_in_db) + 1
    
    if start_time is None: 
        start_time = time.time()

    while True:
        pages_visited, start_time = wait_for_rate_limit(page_limit, pages_visited, start_time)
        league = "NBA" if next_year_to_check >= 1950 else "BAA"
        response = requests.get(f"https://www.basketball-reference.com/leagues/{league}_{next_year_to_check}_{"per_game" if stat_type == "regular" else "advanced"}.html")
        pages_visited += 1

        if response.status_code != 200:
            break

        next_year_to_check += 1

    return list(range(start_of_new_years, next_year_to_check)), pages_visited, start_time

def get_player_pg_stats_not_already_existing(stat_type, years):
    db_path = Path("~/Personal Project/data/nba.db").expanduser()
    engine = create_engine(f"sqlite:///{db_path}")

    years_existing = []
    try:
        with engine.connect() as conn:
            years_existing += [year[0] for year in conn.execute(text(f"SELECT DISTINCT Year FROM {"player_pg_stats" if stat_type == "regular" else "advanced_player_pg_stats"}")).fetchall()]
    except SQLAlchemyError:
        return years

    return [year for year in years if year not in years_existing]

def get_selected_years_player_pg_stats(years, page_limit, stat_type, pages_visited=0, start_time=None):
    if start_time is None:
        start_time = time.time() 

    df = pd.DataFrame()
    for year in years:
        pages_visited, start_time = wait_for_rate_limit(page_limit, pages_visited, start_time)

        if year < 1947:
            print(f"Year is invalid. Skipping {year}...")
            continue 

        if stat_type == "regular":
            year_df = get_year_regular_player_pg_stats(year)
        else:
            year_df = get_year_advanced_player_pg_stats(year)

        pages_visited += 1

        year_df["Year"] = year 

        df = pd.concat([df, year_df], axis=0)

        print(f"Player {"regular" if stat_type == "regular" else "advanced"} per-game stats added for year: {year}")

    return df, pages_visited, start_time

def move_player_pg_stats_to_database(player_pg_stats, stat_type):
    db_path = Path("~/Personal Project/data/nba.db").expanduser()
    engine = create_engine(f"sqlite:///{db_path}")

    player_pg_stats.to_sql(
        "player_pg_stats" if stat_type == "regular" else 'advanced_player_pg_stats',
        engine,
        if_exists="append",
        index=False
    )

    print("Successfully moved to database.")

def player_pg_stats_etl(years, page_limit):
    requested_years = years

    years = get_player_pg_stats_not_already_existing('regular', requested_years)
    new_years, pages_visited, start_time = check_for_player_pg_stats_to_scrape('regular', page_limit)
    years += new_years
    years = list(set(years))

    if years:
        print(f"Getting regular player per-game stats for years: {', '.join([str(i) for i in years])}")
        df, pages_visited, start_time = get_selected_years_player_pg_stats(years, page_limit, 'regular', pages_visited=pages_visited, start_time=start_time)
        move_player_pg_stats_to_database(df, 'regular')
    else:
        print("All years are accounted for.")

    years = get_player_pg_stats_not_already_existing('advanced', requested_years)
    new_years, pages_visited, start_time = check_for_player_pg_stats_to_scrape('advanced', page_limit, start_time=start_time, pages_visited=pages_visited)
    years += new_years 
    years = list(set(years))

    if years:
        print(f"Getting advanced player per-game stats for yeas: {', '.join([str(i) for i in years])}")
        df, _, _ = get_selected_years_player_pg_stats(years, page_limit, "advanced", pages_visited=pages_visited, start_time=start_time)
        move_player_pg_stats_to_database(df, 'advanced')
    else:
        print("All years accounted for.")

if __name__ == "__main__":
    player_pg_stats_etl(list(range(1947, 2027)), 15)
