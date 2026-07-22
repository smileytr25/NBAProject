from hoophub.crawler.fetch import fetch_response_content
from hoophub.crawler.urls import standings_url
from hoophub.parsers.standings import (
    get_conference_rank,
    parse_BAA_standings,
    parse_NBA1950_standings,
    parse_NBA1951_1970_standings,
    parse_NBA1971_2004_standings,
    parse_NBA_after_2004_standings,
    parse_head_to_head,
)
from hoophub.repository.save import save_standings_to_db
from hoophub.repository.query import query_existing_years_in_table
import pandas as pd 

def get_BAA_year_expanded_standings(year: int, page_limit: int) -> pd.DataFrame:
    url = standings_url(year)
    content = fetch_response_content(url, page_limit=page_limit)
    standings_df = parse_BAA_standings(content, year)
    return standings_df

def get_NBA1950_year_expanded_standings(year: int, page_limit: int) -> pd.DataFrame:
    url = standings_url(year)
    content = fetch_response_content(url, page_limit=page_limit)
    standings_df  = parse_NBA1950_standings(content, year)
    return standings_df

def get_NBA1951_1970_year_expanded_standings(year: int, page_limit: int) -> pd.DataFrame:
    url = standings_url(year)
    content = fetch_response_content(url, page_limit=page_limit)
    standings_df = parse_NBA1951_1970_standings(content, year)
    return standings_df

def get_NBA1971_2004_year_expanded_standings(year: int, page_limit: int) -> pd.DataFrame:
    url = standings_url(year)
    content = fetch_response_content(url, page_limit=page_limit)
    standings_df = parse_NBA1971_2004_standings(content, year)
    return standings_df

def get_NBA_after_2004_year_expanded_standings(year: int, page_limit: int) -> pd.DataFrame:
    url = standings_url(year)
    content = fetch_response_content(url, page_limit=page_limit)
    standings_df = parse_NBA_after_2004_standings(content, year)
    return standings_df 

def get_year_team_vs_team(year: int, page_limit: int) -> pd.DataFrame:
    url = standings_url(year)
    content = fetch_response_content(url, page_limit=page_limit) 
    standings_df, pivoted = parse_head_to_head(content, year)
    return standings_df, pivoted

def get_year_standings(year: int, page_limit: int) -> tuple[pd.DataFrame]:    
    expanded_standings = None
    if year < 1950:
        expanded_standings = get_BAA_year_expanded_standings(year, page_limit)
    elif year == 1950:
        expanded_standings = get_NBA1950_year_expanded_standings(year, page_limit)
    elif year <= 1970:
        expanded_standings = get_NBA1951_1970_year_expanded_standings(year, page_limit)
    elif year <= 2004:
        expanded_standings = get_NBA1971_2004_year_expanded_standings(year, page_limit)
    else:
        expanded_standings = get_NBA_after_2004_year_expanded_standings(year, page_limit)
    team_vs_team, pivoted_team_vs_team = get_year_team_vs_team(year, page_limit)
    if year >= 1971:
        expanded_standings = get_conference_rank(expanded_standings, team_vs_team)
    print(f"Added standings history for {year}")
    return expanded_standings, pivoted_team_vs_team

def get_standings_not_already_existing(years: list[int]) -> list[int]:
    years_existing = []
    tables = [
        "standings_history_after_2004",
        "standings_history_after_1970_to_2004",
        "standings_history_after_1950_to_1970",
        "standings_history_1950",
        "standings_history_before_1950"
    ]
    for table in tables:
        years_existing += query_existing_years_in_table(table, "year")

    return [year for year in years if year not in years_existing]

def run(years: list[int], page_limit: int) -> None:
    years = get_standings_not_already_existing(years)
    if years:
        for year in years:
            expanded_standings, pivoted_team_vs_team = get_year_standings(year, page_limit)
            save_standings_to_db(expanded_standings, pivoted_team_vs_team)
