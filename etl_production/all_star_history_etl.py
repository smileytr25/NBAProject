import pandas as pd
import requests
import numpy as np 
from bs4 import BeautifulSoup, Comment
from pathlib import Path
from sqlalchemy import create_engine
import time 
import sys

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from utils.rate_limit import wait_for_rate_limit

def get_year_all_stars(year):
    url = f"https://www.basketball-reference.com/leagues/{"NBA" if year >= 1950 else "BAA"}_{year}.html#all_all_star_game_rosters"
    r = requests.get(url)

    soup = BeautifulSoup(r.content, "html.parser")
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
    start_time = time.time()
    pages_visited = 0

    all_stars = pd.DataFrame()
    for year in years:
        pages_visited, start_time = wait_for_rate_limit(page_limit, pages_visited, start_time)

        year_all_stars = get_year_all_stars(year)

        if year_all_stars:
            year_df = pd.DataFrame({"player" : year_all_stars})
            year_df["year"] = year 

            all_stars = pd.concat([all_stars, year_df], axis=0)

            print(f"All-star history added for year: {year}")

        else:
            print(f"No all-star history for year: {year}")

        pages_visited += 1
        
    return all_stars 

def move_all_stars_to_database(all_stars):
    db_path = Path("~/Personal Project/data/nba.db").expanduser()
    engine = create_engine(f"sqlite:///{db_path}")

    all_stars.to_sql(
        "all-star_history",
        engine,
        if_exists="append",
        index=False
    )

    print("Successfully moved to database")

def all_star_etl(years, page_limit):
    all_stars = get_selected_years_all_stars(years, page_limit)
    move_all_stars_to_database(all_stars)

if __name__ == "__main__":
    all_star_etl(list(range(1947, 2027)), 15)
