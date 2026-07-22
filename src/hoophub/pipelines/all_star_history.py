import pandas as pd
from src.hoophub.crawler.fetch import fetch_response_content
from src.hoophub.crawler.urls import league_page_subsection_url
from src.hoophub.parsers.all_star import parse_all_star_rosters
from src.hoophub.repository.save import save_to_db

def get_year_all_stars(year: int, page_limit: int) -> pd.DataFrame:
    url = league_page_subsection_url(year, "all_star_game_rosters")
    content = fetch_response_content(url, page_limit=page_limit)
    all_star_df = parse_all_star_rosters(content, year)
    return all_star_df

def get_selected_years_all_stars(years: list[int], page_limit: int) -> pd.DataFrame:
    all_stars = []
    for year in years:
        year_all_stars = get_year_all_stars(year, page_limit)
        all_stars.append(year_all_stars)
    return pd.concat(all_stars, axis=0, ignore_index=True) if all_stars else pd.DataFrame()

def run(years: list[int], page_limit: int) -> None:
    all_stars = get_selected_years_all_stars(years, page_limit)
    save_to_db(all_stars, "all-stars_history", if_exists="append")
    
