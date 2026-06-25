import pandas as pd
import time 
from sqlalchemy import create_engine, text 
from pathlib import Path
import requests 

def get_year_draft_results(year):
    url = f"https://www.basketball-reference.com/draft/{"NBA" if year >= 1950 else "BAA"}_{year}.html"

    df = pd.read_html(url, attrs={"id" : "stats"})[0]
    df.columns = [i[1] for i in df.columns.to_flat_index()]

    df = df[["Rk", "Pk", "Tm", "Player", "College"]].copy()
    df["Rk"] = pd.to_numeric(df["Rk"], errors="coerce")
    df = df[df.Rk.notna() & df.Player.notna()]
    df["College"] = df["College"].fillna("None")

    return df

def check_for_drafts_to_scrape():
    db_path = Path("~/Personal Project/data/nba.db").expanduser()
    engine = create_engine(f"sqlite:///{db_path}")
    
    with engine.connect() as conn:
        query = text("SELECT MAX(Year) FROM draft_history")
        last_draft_in_db = int(conn.execute(query).fetchone()[0])

        start_of_new_years = next_year_to_check = last_draft_in_db + 1
        
        while requests.get(f"https://www.basketball-reference.com/draft/NBA_{next_year_to_check}").status_code == 200:
            next_year_to_check += 1

        return list(range(start_of_new_years, next_year_to_check))

def get_drafts_not_already_existing(years):
    db_path = Path("~/Personal Project/data/nba.db").expanduser()
    engine = create_engine(f"sqlite:///{db_path}")

    years_existing = []
    with engine.connect() as conn:
        years_existing += [year[0] for year in conn.execute(text("SELECT DISTINCT Year FROM draft_history")).fetchall()]

    return [year for year in years if year not in years_existing]
        
def get_selected_years_draft_results(years, page_limit):
    rate_limiting = len(years) >= page_limit
    
    if rate_limiting: 
        pages_visited = 0
        start_time = time.time()
    
    df = pd.DataFrame()
    for year in years:
        if rate_limiting and pages_visited == page_limit:
            current_time = time.time()
            wait_time = max(0, 60 - (current_time - start_time))
            print(f"Rate limited. Waiting {wait_time:.2f} seconds")

            time.sleep(max(0, 60 - (current_time - start_time)))
            start_time = time.time()
            pages_visited = 0

        if year < 1947 or year > 2026:
            print(f"Year is invalid. Skipping {year}...")
            continue 

        year_df = get_year_draft_results(year)
        
        if rate_limiting:
            pages_visited += 1

        year_df["Year"] = year
        
        df = pd.concat([df, year_df], axis=0)

        print(f"Draft history added for year: {year}")

    return df

def move_draft_history_to_database(draft_history):
    db_path = Path("~/Personal Project/data/nba.db").expanduser()
    engine = create_engine(f"sqlite:///{db_path}")
    
    draft_history.to_sql(
        "draft_history",
        engine,
        if_exists="append",
        index=False
    )

    print("Successfully moved to database.")

def draft_history_etl(years, page_limit):
    years = get_drafts_not_already_existing(years)
    years += check_for_drafts_to_scrape()
    years = list(set(years))

    if years:
        print(f"Getting draft history for years: {', '.join([str(i) for i in years])}")
        df = get_selected_years_draft_results(years, page_limit)
        move_draft_history_to_database(df)
    else:
        print("All years are accounted for.")

if __name__ == "__main__":
    draft_history_etl(list(range(1947, 2027)), 19)