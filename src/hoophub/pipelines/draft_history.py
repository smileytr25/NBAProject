import pandas as pd
from sqlalchemy import text 
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path
    
from src.hoophub.crawler.fetch import fetch_response_status_code, read_html
from src.hoophub.crawler.urls import draft_url
from src.hoophub.utils.database import get_nba_db_engine

def get_year_draft_results(year, page_limit):
    url = draft_url(year)

    df = read_html(url, page_limit=page_limit, attrs={"id" : "stats"})[0]
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
    while True:
        status_code = fetch_response_status_code(
            draft_url(next_year_to_check),
            page_limit=page_limit
        )

        if status_code != 200:
            break

        next_year_to_check += 1

    return list(range(start_of_new_years, next_year_to_check))

def get_drafts_not_already_existing(years):
    engine = get_nba_db_engine()

    years_existing = []
    try:
        with engine.connect() as conn:
            years_existing += [year[0] for year in conn.execute(text("SELECT DISTINCT Year FROM draft_history")).fetchall()]
    except SQLAlchemyError:
        return years

    return [year for year in years if year not in years_existing]
        
def get_selected_years_draft_results(years, page_limit):
    df = pd.DataFrame()
    for year in years:
        if year < 1947:
            print(f"Year is invalid. Skipping {year}...")
            continue 

        year_df = get_year_draft_results(year, page_limit)

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

def run(years, page_limit):
    years = get_drafts_not_already_existing(years)
    new_years = check_for_drafts_to_scrape(page_limit)
    years += new_years
    years = list(set(years))

    if years:
        print(f"Getting draft history for years: {', '.join([str(i) for i in years])}")
        df = get_selected_years_draft_results(years, page_limit)
        move_draft_history_to_database(df)
    else:
        print("All years are accounted for.")
