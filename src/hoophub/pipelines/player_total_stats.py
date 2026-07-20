import pandas as pd 
from src.hoophub.crawler.fetch import fetch_response_status_code, read_html
from src.hoophub.crawler.urls import player_stats_url
from src.hoophub.parsers.player_stats import parse_player_stats
from src.hoophub.repository.save import save_to_db
from src.hoophub.repository.query import query_existing_years_in_table, query_last_year_in_table

def get_year_player_total_stats(year, season_type, page_limit):
    url = player_stats_url(year, "totals")
    table_id = "totals_stats" + ("" if season_type == "regular" else "_post")
    df = read_html(url, page_limit=page_limit, attrs={"id" : table_id})[0]
    df = parse_player_stats(df, year)
    return df

def check_for_player_total_stats_to_scrape(season_type, page_limit):
    table_name = "player_total_stats"
    if season_type == "playoffs":
        table_name += "_playoffs"

    last_year_in_db = query_last_year_in_table(table_name, "Year", 2026)
    start_of_new_years = next_year_to_check = int(last_year_in_db) + 1

    while True:
        if fetch_response_status_code(player_stats_url(next_year_to_check, "totals"), page_limit=page_limit) != 200:
            break 
        next_year_to_check += 1
    
    return list(range(start_of_new_years, next_year_to_check))

def get_player_total_stats_not_already_existing(season_type, years):
    table_name = "player_total_stats"
    if season_type == "playoffs":
        table_name += "_playoffs"
    
    years_existing = query_existing_years_in_table(table_name, "Year")
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
