import pandas as pd 
import sys
from pathlib import Path 

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from crawler.fetch import read_html
from crawler.urls import coaches_url
from utils.database import get_nba_db_engine

def get_year_coaches(year, page_limit):
    url = coaches_url(year)

    raw_df = read_html(url, page_limit=page_limit, attrs={"id" : f"{"NBA" if year >= 1950 else "BAA"}_coaches"})[0]
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
    engine = get_nba_db_engine()

    abbrev_mapping = pd.read_sql("SELECT * FROM team_abbreviation_to_teamname", engine)
    abbrev_mapping = {i : j for (_, i, j) in abbrev_mapping.itertuples()}

    raw_df["team"] = raw_df["team"].map(abbrev_mapping)
    raw_df["year"] = year 

    return raw_df 

def get_selected_years_coaches(years, page_limit):
    coaches = pd.DataFrame() 

    for year in years:
        year_coaches = get_year_coaches(year, page_limit)
        coaches = pd.concat([coaches, year_coaches], axis=0)
        print(f"Coaches history added for year: {year}")

    return coaches

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
