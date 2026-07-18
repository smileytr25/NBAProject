import pandas as pd 
import time 
from pathlib import Path 
from sqlalchemy import create_engine

def get_year_coaches(year):
    url = f"https://www.basketball-reference.com/leagues/{"NBA" if year >= 1950 else "BAA"}_{year}_coaches.html"

    raw_df = pd.read_html(url, attrs={"id" : f"{"NBA" if year >= 1950 else "BAA"}_coaches"})[0]
    raw_df.columns = raw_df.columns.to_flat_index().map('_'.join)

    col_names = [
        "coach", "team", 'ut0', 'with_franchise_seasons', 'overall_seasons', 'ut1', 'current_regular_season_games', 
        'current_regular_season_wins', 'current_regular_season_losses', 'with_franchise_regular_season_games',
        'with_franchise_regular_season_wins', 'with_franchise_regular_season_losses', 'career_regular_season_games',
        'career_regular_season_wins', 'career_regular_season_losses', 'career_win_percentage', 'ut2', 'current_playoff_games', 'current_playoff_wins',
        'current_playoff_losses', 'with_franchise_playoff_games', 'with_franchise_playoff_wins', 'with_franchise_playoff_losses',
        'career_playoff_games', 'career_playoff_wins', 'career_playoff_losses' 
    ]

    raw_df.columns = col_names
    raw_df = raw_df.drop(columns=["ut0", "ut1", "ut2"])
    raw_df = raw_df.fillna(0)

    db_path = Path("~/Personal Project/data/nba.db").expanduser()
    engine = create_engine(f"sqlite:///{db_path}")

    abbrev_mapping = pd.read_sql("SELECT * FROM team_abbreviation_to_teamname", engine)
    abbrev_mapping = {i : j for (_, i, j) in abbrev_mapping.itertuples()}

    raw_df["team"] = raw_df["team"].map(abbrev_mapping)
    raw_df["year"] = year 

    return raw_df 

def get_selected_years_coaches(years, page_limit):
    rate_limiting = len(years) > page_limit

    if rate_limiting:
        start_time = time.time() 
        pages_visited = 0 

    coaches = pd.DataFrame() 

    for year in years:
        if rate_limiting and pages_visited == page_limit:
            wait_time = max(0, 60 - (time.time() - start_time))
            print(f"Rate limited. Waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)

            start_time = time.time()
            pages_visited = 0

        year_coaches = get_year_coaches(year)
        coaches = pd.concat([coaches, year_coaches], axis=0)

        pages_visited += 1
        print(f"Coaches history added for year: {year}")

    return coaches

def move_coaches_history_to_database(coaches):
    db_path = Path("~/Personal Project/data/nba.db").expanduser()
    engine = create_engine(f"sqlite:///{db_path}")

    coaches.to_sql(
        "coaches_history",
        engine,
        if_exists="append",
        index=False
    ) 

    print("Successfully moved to database")

def coaches_history_etl(years, page_limit):
    coaches = get_selected_years_coaches(years, page_limit)
    move_coaches_history_to_database(coaches)

if __name__ == "__main__":
    coaches_history_etl(list(range(1947, 2027)), 15)