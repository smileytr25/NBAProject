import pandas as pd
import numpy as np 
from bs4 import BeautifulSoup, Comment
from pathlib import Path

from src.hoophub.crawler.fetch import fetch_response_content
from src.hoophub.crawler.urls import league_page_subsection_url
from src.hoophub.utils.database import get_nba_db_engine
from src.hoophub.parsers.all_star import parse_all_star_rosters

def get_year_all_stars(year, page_limit):
    url = league_page_subsection_url(year, "all_star_game_rosters")
    content = fetch_response_content(url, page_limit=page_limit)
    all_star_df = parse_all_star_rosters(content, year)
    return all_star_df

def get_selected_years_all_stars(years, page_limit):
    all_stars = []
    for year in years:
        year_all_stars = get_year_all_stars(year, page_limit)
        all_stars.append(year_all_stars)
        print(f"All-star history added for year: {year}")
    return pd.concat(all_stars, axis=0, ignore_index=True) if all_stars else pd.DataFrame()

def move_all_stars_to_database(all_stars):
    engine = get_nba_db_engine()
    all_stars.to_sql(
        "all-star_history",
        engine,
        if_exists="append",
        index=False
    )
    print("Successfully moved to database")

def run(years, page_limit):
    all_stars = get_selected_years_all_stars(years, page_limit)
    move_all_stars_to_database(all_stars)
