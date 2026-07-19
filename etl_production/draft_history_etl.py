import pandas as pd
import time 
import sys
from sqlalchemy import text 
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path
import requests 

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from utils.rate_limit import wait_for_rate_limit
from utils.database import get_nba_db_engine

def get_year_draft_results(year):
    url = f"https://www.basketball-reference.com/draft/{"NBA" if year >= 1950 else "BAA"}_{year}.html"

    df = pd.read_html(url, attrs={"id" : "stats"})[0]
    df.columns = [i[1] for i in df.columns.to_flat_index()]

    df = df[["Rk", "Pk", "Tm", "Player", "College"]].copy()
    df["Rk"] = pd.to_numeric(df["Rk"], errors="coerce")
    df = df[df.Rk.notna() & df.Player.notna()]
    df["College"] = df["College"].fillna("None")

    return df

def check_for_drafts_to_scrape(page_limit):
    engine = get_nba_db_engine()
    
    try:
        with engine.connect() as conn:
            query = text("SELECT MAX(Year) FROM draft_history")
            last_draft_in_db = conn.execute(query).fetchone()[0]
    except SQLAlchemyError:
        last_draft_in_db = None

    if last_draft_in_db is None:
        last_draft_in_db = 1946

    start_of_new_years = next_year_to_check = int(last_draft_in_db) + 1
    pages_visited = 0
    start_time = time.time()

    while True:
        pages_visited, start_time = wait_for_rate_limit(page_limit, pages_visited, start_time)
        league = "NBA" if next_year_to_check >= 1950 else "BAA"
        response = requests.get(f"https://www.basketball-reference.com/draft/{league}_{next_year_to_check}.html")
        pages_visited += 1

        if response.status_code != 200:
            break

        next_year_to_check += 1

    return list(range(start_of_new_years, next_year_to_check)), pages_visited, start_time

def get_drafts_not_already_existing(years):
    engine = get_nba_db_engine()

    years_existing = []
    try:
        with engine.connect() as conn:
            years_existing += [year[0] for year in conn.execute(text("SELECT DISTINCT Year FROM draft_history")).fetchall()]
    except SQLAlchemyError:
        return years

    return [year for year in years if year not in years_existing]
        
def get_selected_years_draft_results(years, page_limit, pages_visited=0, start_time=None):
    if start_time is None:
        start_time = time.time()
    
    df = pd.DataFrame()
    for year in years:
        pages_visited, start_time = wait_for_rate_limit(page_limit, pages_visited, start_time)

        if year < 1947:
            print(f"Year is invalid. Skipping {year}...")
            continue 

        year_df = get_year_draft_results(year)
        pages_visited += 1

        year_df["Year"] = year
        
        df = pd.concat([df, year_df], axis=0)

        print(f"Draft history added for year: {year}")

    return df

def move_draft_history_to_database(draft_history):
    engine = get_nba_db_engine()
    
    draft_history.to_sql(
        "draft_history",
        engine,
        if_exists="append",
        index=False
    )

    print("Successfully moved to database.")

def draft_history_etl(years, page_limit):
    years = get_drafts_not_already_existing(years)
    new_years, pages_visited, start_time = check_for_drafts_to_scrape(page_limit)
    years += new_years
    years = list(set(years))

    if years:
        print(f"Getting draft history for years: {', '.join([str(i) for i in years])}")
        df = get_selected_years_draft_results(years, page_limit, pages_visited=pages_visited, start_time=start_time)
        move_draft_history_to_database(df)
    else:
        print("All years are accounted for.")

if __name__ == "__main__":
    draft_history_etl(list(range(1947, 2027)), 19)
