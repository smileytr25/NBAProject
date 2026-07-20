import pandas as pd 
from sqlalchemy import text 
from src.hoophub.crawler.fetch import fetch_response_content
from src.hoophub.crawler.urls import standings_url
from src.hoophub.utils.database import get_nba_db_engine
from src.hoophub.parsers.standings import (
    get_conference_rank,
    parse_BAA_standings,
    parse_NBA1950_standings,
    parse_NBA1951_1970_standings,
    parse_NBA1971_2004_standings,
    parse_NBA_after_2004_standings,
    parse_head_to_head,
)

def get_BAA_year_expanded_standings(year, page_limit):
    url = standings_url(year)
    content = fetch_response_content(url, page_limit=page_limit)
    standings_df = parse_BAA_standings(content, year)
    return standings_df

def get_NBA1950_year_expanded_standings(year, page_limit):
    url = standings_url(year)
    content = fetch_response_content(url, page_limit=page_limit)
    standings_df  = parse_NBA1950_standings(content, year)
    return standings_df

def get_NBA1951_1970_year_expanded_standings(year, page_limit):
    url = standings_url(year)
    content = fetch_response_content(url, page_limit=page_limit)
    standings_df = parse_NBA1951_1970_standings(content, year)
    return standings_df

def get_NBA1971_2004_year_expanded_standings(year, page_limit):
    url = standings_url(year)
    content = fetch_response_content(url, page_limit=page_limit)
    standings_df = parse_NBA1971_2004_standings(content, year)
    return standings_df

def get_NBA_after_2004_year_expanded_standings(year, page_limit):
    url = standings_url(year)
    content = fetch_response_content(url, page_limit=page_limit)
    standings_df = parse_NBA_after_2004_standings(content, year)
    return standings_df 

def get_year_team_vs_team(year, page_limit):
    url = standings_url(year)
    content = fetch_response_content(url, page_limit=page_limit) 
    standings_df, pivoted = parse_head_to_head(content, year)
    return standings_df, pivoted

def get_year_standings(year, page_limit):    
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

def get_standings_not_already_existing(years):
    engine = get_nba_db_engine()
    years_existing = []
    with engine.connect() as conn:
        tables = [
            "standings_history_after_2004",
            "standings_history_after_1970_to_2004",
            "standings_history_after_1950_to_1970",
            "standings_history_1950",
            "standings_history_before_1950"
        ]
        for table in tables:
            try:
                years_existing += [year[0] for year in conn.execute(text(f"SELECT DISTINCT year FROM {table}")).fetchall()]
            except Exception:
                pass
    return [year for year in years if year not in years_existing]

def move_standings_to_database(expanded_standings, team_vs_team, year):
    engine = get_nba_db_engine()
    after_2004_standings = expanded_standings[expanded_standings.year.ge(2005)]
    after_1970_standings = expanded_standings[expanded_standings.year.ge(1971) & expanded_standings.year.lt(2005)]
    after_1950_standings = expanded_standings[expanded_standings.year.ge(1951) & expanded_standings.year.lt(1971)]
    equal_1950_standings = expanded_standings[expanded_standings.year.eq(1950)]
    before_1950_standings = expanded_standings[expanded_standings.year.lt(1950)]
    
    if len(after_2004_standings):
        after_2004_standings.to_sql(
            "standings_history_after_2004",
            engine,
            if_exists="append",
            index=False
        )

    if len(after_1970_standings):
        after_1970_standings.to_sql(
            "standings_history_after_1970_to_2004",
            engine,
            if_exists="append",
            index=False
        )
    if len(after_1950_standings):
        after_1950_standings.to_sql(
            "standings_history_after_1950_to_1970",
            engine,
            if_exists="append",
            index=False
        )

    if len(equal_1950_standings):
        equal_1950_standings.to_sql(
            "standings_history_1950",
            engine,
            if_exists="append",
            index=False
        )

    if len(before_1950_standings):
        before_1950_standings.to_sql(
            "standings_history_before_1950",
            engine,
            if_exists="append",
            index=False
        )

    team_vs_team.to_sql(
        "head_to_head_history",
        engine,
        if_exists="append",
        index=False
    )

    print(f"Successfully moved {year} standings to database.")

def run(years, page_limit):
    years = get_standings_not_already_existing(years)

    if years:
        for year in years:
            expanded_standings, pivoted_team_vs_team = get_year_standings(year, page_limit)
            move_standings_to_database(expanded_standings, pivoted_team_vs_team, year)
    else:
        print("All years are accounted for.")
