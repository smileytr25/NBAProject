import pandas as pd 
from pathlib import Path 
    
from src.hoophub.crawler.fetch import read_html
from src.hoophub.crawler.urls import coaches_url
from src.hoophub.utils.database import get_nba_db_engine
from src.hoophub.parsers.coach import parse_coaches

def get_year_coaches(year, page_limit):
    url = coaches_url(year)
    raw_df = read_html(url, page_limit=page_limit, attrs={"id" : f"{"NBA" if year >= 1950 else "BAA"}_coaches"})[0]
    year_coaches = parse_coaches(raw_df, year)
    return year_coaches

def get_selected_years_coaches(years, page_limit):
    coaches = []
    for year in years:
        year_coaches = get_year_coaches(year, page_limit)
        coaches.append(year_coaches)
        print(f"Coaches history added for year: {year}")
    return pd.concat(coaches, axis=0, ignore_index=True) if coaches else pd.DataFrame()

def move_coaches_history_to_database(coaches):
    engine = get_nba_db_engine()
    coaches.to_sql(
        "coaches_history",
        engine,
        if_exists="append",
        index=False
    ) 
    print("Successfully moved to database")

def run(years, page_limit):
    coaches = get_selected_years_coaches(years, page_limit)
    move_coaches_history_to_database(coaches)
