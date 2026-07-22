import pandas as pd 
from src.hoophub.crawler.fetch import read_html
from src.hoophub.crawler.urls import coaches_url
from src.hoophub.parsers.coach import parse_coaches
from src.hoophub.repository.save import save_to_db

def get_year_coaches(year: int, page_limit: int) -> pd.DataFrame:
    url = coaches_url(year)
    raw_df = read_html(url, page_limit=page_limit, attrs={"id" : f"{"NBA" if year >= 1950 else "BAA"}_coaches"})[0]
    return parse_coaches(raw_df, year)

def get_selected_years_coaches(years: list[int], page_limit: int) -> pd.DataFrame:
    coaches = []
    for year in years:
        coaches.append(get_year_coaches(year, page_limit))
    return pd.concat(coaches, axis=0, ignore_index=True) if coaches else pd.DataFrame()

def run(years: list[int], page_limit: int) -> None:
    coaches = get_selected_years_coaches(years, page_limit)
    save_to_db(coaches, "coaches_history", if_exists="append")


