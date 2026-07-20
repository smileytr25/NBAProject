import pandas as pd 
import sys
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path 

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from crawler.fetch import fetch_response_status_code, read_html
from crawler.urls import player_stats_url
from utils.database import get_nba_db_engine
from utils.text_cleaning import remove_accents

def get_year_regular_player_pg_stats(year, season_type, page_limit):
    url = player_stats_url(year, "per_game")

    df = read_html(url, page_limit=page_limit, attrs={"id" : "per_game_stats" + ("" if season_type == "regular" else "_post")})[0]
    df["Player"] = df["Player"].apply(remove_accents)
    df = df.drop(columns=["Rk", "Awards"])
    df = df.loc[df.Team.ne("2TM"), :]

    return df

def get_year_advanced_player_pg_stats(year, season_type, page_limit):
    url = player_stats_url(year, "advanced")

    df = read_html(url, page_limit=page_limit, attrs={"id" : "advanced" + ("" if season_type == "regular" else "_post")})[0]
    df["Player"] = df["Player"].apply(remove_accents)
    df = df.drop(columns=["Rk", "Awards"])
    df = df.loc[df.Team.ne("2TM"), :]

    return df 

def check_for_player_pg_stats_to_scrape(stat_type, season_type, page_limit):
    engine = get_nba_db_engine()

    try:
        with engine.connect() as conn:
            table_name = "player_pg_stats"
            if stat_type == "advanced":
                table_name = "advanced_" + table_name 
            if season_type == "playoffs":
                table_name += "_playoffs"

            query = text(f"SELECT MAX(Year) FROM {table_name}")
            last_year_in_db = conn.execute(query).fetchone()[0]
    except SQLAlchemyError:
        last_year_in_db = None

    if last_year_in_db is None:
        last_year_in_db = 2026

    start_of_new_years = next_year_to_check = int(last_year_in_db) + 1
    
    while True:
        status_code = fetch_response_status_code(
            player_stats_url(next_year_to_check, stat_type),
            raise_for_status=False,
            page_limit=page_limit
        )

        if status_code != 200:
            break

        next_year_to_check += 1

    return list(range(start_of_new_years, next_year_to_check))

def get_player_pg_stats_not_already_existing(stat_type, season_type, years):
    engine = get_nba_db_engine()

    years_existing = []
    try:
        with engine.connect() as conn:
            table_name = "player_pg_stats"
            if stat_type == "advanced":
                table_name = "advanced_" + table_name 
            if season_type == "playoffs":
                table_name += "_playoffs"

            years_existing += [year[0] for year in conn.execute(text(f"SELECT DISTINCT Year FROM {table_name}")).fetchall()]
    except SQLAlchemyError:
        return years

    return [year for year in years if year not in years_existing]

def get_selected_years_player_pg_stats(years, page_limit, stat_type, season_type):
    df = pd.DataFrame()
    for year in years:
        if year < 1947:
            print(f"Year is invalid. Skipping {year}...")
            continue 

        if stat_type == "per_game":
            year_df = get_year_regular_player_pg_stats(year, season_type, page_limit)
        else:
            year_df = get_year_advanced_player_pg_stats(year, season_type, page_limit)

        year_df["Year"] = year 

        df = pd.concat([df, year_df], axis=0)

        print(f"Player {stat_type} {season_type} per-game stats added for year: {year}")

    return df

def move_player_pg_stats_to_database(player_pg_stats, stat_type, season_type):
    engine = get_nba_db_engine()

    table_name = "player_pg_stats"
    if stat_type == "advanced":
        table_name = "advanced_" + table_name
    if season_type == "playoffs":
        table_name += "_playoffs"

    player_pg_stats.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False
    )

    print("Successfully moved to database.")

def run(years, page_limit):
    requested_years = years

    for stat_type in ["per_game", "advanced"]:
        for season_type in ["regular", "playoffs"]:
            years = get_player_pg_stats_not_already_existing(stat_type, season_type, requested_years)
            new_years = check_for_player_pg_stats_to_scrape(
                stat_type,
                season_type,
                page_limit
            )
            years += new_years
            years = sorted(set(years))

            if years:
                print(f"Getting {stat_type} player {season_type} per-game stats for years: {', '.join([str(i) for i in years])}")
                df = get_selected_years_player_pg_stats(
                    years,
                    page_limit,
                    stat_type,
                    season_type
                )
                move_player_pg_stats_to_database(df, stat_type, season_type)
            else:
                print(f"All {stat_type} player {season_type} per-game stats years are accounted for.")
