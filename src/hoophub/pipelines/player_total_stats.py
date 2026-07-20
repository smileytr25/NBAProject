import pandas as pd 
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from src.hoophub.crawler.fetch import fetch_response_status_code, read_html
from src.hoophub.crawler.urls import player_stats_url
from src.hoophub.repository.engine import get_nba_db_engine
from src.hoophub.parsers.player_stats import parse_player_stats
from src.hoophub.repository.save import save_to_db

def get_year_player_total_stats(year, season_type, page_limit):
    url = player_stats_url(year, "totals")
    table_id = "totals_stats" + ("" if season_type == "regular" else "_post")
    df = read_html(url, page_limit=page_limit, attrs={"id" : table_id})[0]
    df = parse_player_stats(df)
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
    stats = []
    for year in years: 
        year_df = get_year_player_total_stats(year, season_type, page_limit)
        stats.append(year_df)
        print(f"Player {season_type} total stats added for year: {year}")
    return pd.concat(stats, axis=0, ignore_index=True) if stats else pd.DataFrame()

def run(years, page_limit):
    requested_years = years 

    for season_type in ["regular", "playoffs"]:
        years = get_player_total_stats_not_already_existing(season_type, requested_years)
        new_years = check_for_player_total_stats_to_scrape(season_type, page_limit)
        years = list(set(years + new_years))

        if years:
            df = get_selected_years_player_total_stats(years, page_limit, season_type)
            
            table_name = "player_total_stats"
            if season_type == "playoffs":
                table_name += "_playoffs"
                
            save_to_db(df, table_name, if_exists="append")
