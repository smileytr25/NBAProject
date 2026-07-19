import pandas as pd 
from pathlib import Path 
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import time 
import sys 
import requests 

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.rate_limit import wait_for_rate_limit
from utils.database import get_nba_db_engine
from utils.text_cleaning import remove_accents

def get_year_player_total_stats(year, season_type):
    url = f"https://www.basketball-reference.com/leagues/{"NBA" if year >= 1950 else "BAA"}_{year}_totals.html"

    df = pd.read_html(url, attrs={"id" : "totals_stats"})[0]
    df["Player"] = df["Player"].apply(remove_accents)
    df = df.drop(columns=["Rk", "Awards"])
    df = df.loc[df.Team.ne("2TM"), :]

    return df

def check_for_player_total_stats_to_scrape(season_type, page_limit, start_time = None, pages_visited = 0):
    engine = get_nba_db_engine()

    try:
        with engine.connect() as conn:
            table_name = "player_total_stats"
            if season_type == "playoffs":
                table_name += "_playoffs"

            query = text(f"SELECT MAX(Year) FROM {table_name}")
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
        response = requests.get(f"https://www.basketball-reference.com/leagues/{league}_{next_year_to_check}_totals.html")
        pages_visited += 1

        if response.status_code != 200:
            break 

        next_year_to_check += 1
    
    return list(range(start_of_new_years, next_year_to_check)), pages_visited, start_time

def get_player_total_stats_not_already_existing(season_type, years):
    engine = get_nba_db_engine()

    years_existing = []
    try:
        with engine.connect() as conn:
            table_name = "player_total_stats"
            if season_type == "playoffs":
                table_name += "_playoffs"

            years_existing = [year[0] for year in conn.execute(text(f"SELECT DISTINCT Year FROM {table_name}")).fetchall()]
    except SQLAlchemyError:
        return years
    
    return [year for year in years if year not in years_existing]

def get_selected_years_player_total_stats(years, page_limit, season_type, pages_visited=0, start_time=None):
    if start_time is None:
        start_time = time.time()

    df = pd.DataFrame()
    for year in years:
        pages_visited, start_time = wait_for_rate_limit(page_limit, pages_visited, start_time)

        if year < 1947:
            print(f"Year is invalid. Skipping {year}...")
            continue 

        year_df = get_year_player_total_stats(year, season_type)

        pages_visited += 1

        year_df["Year"] = year

        df = pd.concat([df, year_df], axis=0)

        print(f"Player {season_type} total stats added for year: {year}")

    return df, pages_visited, start_time 

def move_player_total_stats_to_database(player_total_stats, season_type):
    engine = get_nba_db_engine()

    table_name = "player_total_stats"
    if season_type == "playoffs":
        table_name += "_playoffs"

    player_total_stats.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False
    )

    print("Successfully moved to database.")

def player_total_stats_etl(years, page_limit):
    requested_years = years 
    pages_visited = 0
    start_time = None 

    for season_type in ["regular", "playoffs"]:
        years = get_player_total_stats_not_already_existing(season_type, requested_years)
        new_years, pages_visited, start_time = check_for_player_total_stats_to_scrape(
                season_type,
                page_limit,
                start_time=start_time,
                pages_visited=pages_visited
            )
        years += new_years
        years = sorted(set(years))

        if years:
            print(f"Getting player {season_type} total stats for years: {', '.join([str(i) for i in years])}")
            df, pages_visited, start_time = get_selected_years_player_total_stats(
                years,
                page_limit,
                season_type,
                pages_visited=pages_visited,
                start_time=start_time
            )
            move_player_total_stats_to_database(df, season_type)
        else:
            print("All player {season_type} total stats years are accounted for.")

if __name__ == "__main__":
    player_total_stats_etl(list(range(1947, 2027)), 15)