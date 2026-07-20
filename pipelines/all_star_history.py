import pandas as pd
import numpy as np 
from bs4 import BeautifulSoup, Comment
from pathlib import Path
import sys

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from crawler.fetch import fetch_response_content
from crawler.urls import league_page_subsection_url
from utils.database import get_nba_db_engine

def get_year_all_stars(year, page_limit):
    url = league_page_subsection_url(year, "all_star_game_rosters")
    content = fetch_response_content(url, page_limit=page_limit)

    soup = BeautifulSoup(content, "html.parser")
    wrapper = soup.find("div", id="all_all_star_game_rosters")

    if not wrapper:
        return []
    
    all_star_comment = wrapper.find(string=lambda text: isinstance(text, Comment)
                                    and 'id="div_all_star_game_rosters"' in text)
    
    all_star_soup = BeautifulSoup(all_star_comment, "html.parser")
    all_star_div = all_star_soup.find("div", id="div_all_star_game_rosters")

    all_star1 = all_star_div.find("div", id="all_star_game_rosters_1")
    all_star2 = all_star_div.find("div", id="all_star_game_rosters_2")
    all_star3 = all_star_div.find("div", id="all_star_game_rosters_3")

    all_stars = []

    if all_star1:
        for name in all_star1.find_all("p"):
            all_stars.append(name.find("a").text)

    if all_star2:
        for name in all_star2.find_all("p"):
            all_stars.append(name.find("a").text)

    if all_star3:
        for name in all_star3.find_all("p"):
            all_stars.append(name.find("a").text)
    
    return all_stars 

def get_selected_years_all_stars(years, page_limit):
    all_stars = pd.DataFrame()
    for year in years:
        year_all_stars = get_year_all_stars(year, page_limit)

        if year_all_stars:
            year_df = pd.DataFrame({"player" : year_all_stars})
            year_df["year"] = year 

            all_stars = pd.concat([all_stars, year_df], axis=0)

            print(f"All-star history added for year: {year}")

        else:
            print(f"No all-star history for year: {year}")
        
    return all_stars 

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
