import pandas as pd 
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from src.hoophub.crawler.fetch import fetch_response_status_code, read_html
from src.hoophub.crawler.urls import player_stats_url
from src.hoophub.utils.database import get_nba_db_engine
from src.hoophub.utils.text_cleaning import remove_accents

def get_year_player_total_stats(year, season_type, page_limit):
    url = player_stats_url(year, "totals")

    df = read_html(url, page_limit=page_limit, attrs={"id" : "totals_stats"})[0]
    df["Player"] = df["Player"].apply(remove_accents)
    df = df.drop(columns=["Rk", "Awards"])
    df = df.loc[df.Team.ne("2TM"), :]

    return df

def check_for_player_total_stats_to_scrape(season_type, page_limit):
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

    while True:
        status_code = fetch_response_status_code(
            player_stats_url(next_year_to_check, "totals"),
            page_limit=page_limit
        )

        if status_code != 200:
            break 

        next_year_to_check += 1
    
    return list(range(start_of_new_years, next_year_to_check))

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

def get_selected_years_player_total_stats(years, page_limit, season_type):
    df = pd.DataFrame()
    for year in years:
        if year < 1947:
            print(f"Year is invalid. Skipping {year}...")
            continue 

        year_df = get_year_player_total_stats(year, season_type, page_limit)

        year_df["Year"] = year

        df = pd.concat([df, year_df], axis=0)

        print(f"Player {season_type} total stats added for year: {year}")

    return df

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

def run(years, page_limit):
    requested_years = years 

    for season_type in ["regular", "playoffs"]:
        years = get_player_total_stats_not_already_existing(season_type, requested_years)
        new_years = check_for_player_total_stats_to_scrape(season_type, page_limit)
        years += new_years
        years = sorted(set(years))

        if years:
            print(f"Getting player {season_type} total stats for years: {', '.join([str(i) for i in years])}")
            df = get_selected_years_player_total_stats(
                years,
                page_limit,
                season_type
            )
            move_player_total_stats_to_database(df, season_type)
        else:
            print("All player {season_type} total stats years are accounted for.")
