import pandas as pd 
from src.hoophub.crawler.fetch import fetch_response_status_code, read_html
from src.hoophub.crawler.urls import player_stats_url
from src.hoophub.parsers.player_stats import parse_player_stats
from src.hoophub.repository.save import save_to_db
from src.hoophub.repository.query import query_last_year_in_table, query_existing_years_in_table

def get_year_player_pg_stats(year: int, stat_type: str, season_type: str, page_limit: int) -> pd.DataFrame:
    url = player_stats_url(year, "per_game")
    table_id = stat_type if stat_type == "advanced" else "per_game_stats"
    table_id = table_id if season_type == "regular" else table_id + "_post"

    df = read_html(url, page_limit=page_limit, attrs={"id" : table_id})[0]
    df = parse_player_stats(df, year)
    return df

def check_for_player_pg_stats_to_scrape(stat_type: str, season_type: str, page_limit: int) -> list[int]:
    table_name = "player_pg_stats"
    if stat_type == "advanced":
        table_name = "advanced_" + table_name 
    if season_type == "playoffs":
        table_name += "_playoffs"

    last_year_in_db = query_last_year_in_table(table_name, "Year", 2026)
    start_of_new_years = next_year_to_check = int(last_year_in_db) + 1
    
    while True:
        if fetch_response_status_code(player_stats_url(next_year_to_check, stat_type), page_limit=page_limit) != 200:
            break
        next_year_to_check += 1

    return list(range(start_of_new_years, next_year_to_check))

def get_player_pg_stats_not_already_existing(stat_type: str, season_type: str, years: list[int]) -> list[int]:
    table_name = "player_pg_stats"
    if stat_type == "advanced":
        table_name = "advanced_" + table_name 
    if season_type == "playoffs":
        table_name += "_playoffs"

    years_existing = query_existing_years_in_table(table_name, "Year")
    return [year for year in years if year not in years_existing]

def get_selected_years_player_pg_stats(years: list[int], page_limit: int, stat_type: str, season_type: str) -> pd.DataFrame:
    stats = []
    for year in years:
        year_df = get_year_player_pg_stats(year, stat_type, season_type, page_limit)  
        stats.append(year_df)
        print(f"Player {stat_type} {season_type} per-game stats added for year: {year}")
    return pd.concat(stats, axis=0, ignore_index=True) if stats else pd.DataFrame()

def run(years: list[int], page_limit: int) -> None:
    requested_years = years

    for stat_type in ["per_game", "advanced"]:
        for season_type in ["regular", "playoffs"]:
            years = get_player_pg_stats_not_already_existing(stat_type, season_type, requested_years)
            new_years = check_for_player_pg_stats_to_scrape(stat_type, season_type, page_limit)
            years = list(set(new_years + years))

            if years:
                df = get_selected_years_player_pg_stats(years, page_limit, stat_type, season_type)

                table_name = "player_pg_stats"
                if stat_type == "advanced":
                    table_name = "advanced_" + table_name
                if season_type == "playoffs":
                    table_name += "_playoffs"

                save_to_db(df, table_name, if_exists="append")
