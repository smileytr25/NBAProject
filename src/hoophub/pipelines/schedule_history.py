from sqlalchemy import text
import pandas as pd
from src.hoophub.crawler.fetch import fetch_response_status_code, read_html
from src.hoophub.crawler.urls import schedule_url
from src.hoophub.parsers.schedule import parse_schedule
from src.hoophub.repository.save import save_to_db
from src.hoophub.repository.query import query_existing_years_in_table, query_last_year_in_table

def get_month_game_schedule(month: str, year: int, page_limit: int) -> pd.DataFrame: 
    url = schedule_url(year, month)
    try:
        schedule = read_html(url, page_limit=page_limit, attrs={"id" : "schedule"})[0]
        schedule = parse_schedule(schedule)
        print(f"Schedule history added for {month}, {year}")
        return schedule 
    except:
        return pd.DataFrame()

def get_year_game_schedule(year: int, page_limit: int) -> pd.DataFrame:
    months = [
        "october", "november", "december", "january", "february", "march", 
        "april", "may", "june"
    ]
    schedule = []
    for month in months: 
        df = get_month_game_schedule(month, year, page_limit)
        schedule.append(df)
    return pd.concat(schedule, axis=0, ignore_index=True) if schedule else pd.DataFrame()

def get_selected_years_game_schedule(years: list[int], page_limit: int) -> pd.DataFrame:
    schedule = []
    for year in years:
        df = get_year_game_schedule(year, page_limit)
        schedule.append(df)
    return pd.concat(schedule, axis=0, ignore_index=True) if schedule else pd.DataFrame()

def check_for_schedules_to_scrape(page_limit: int = 15) -> list[pd.Timestamp]:
    last_date_in_db = pd.to_datetime(query_last_year_in_table("game_schedule_history", "date", "2026-06-01"))
    next_date_to_check = last_date_in_db + pd.DateOffset(months=1)

    dates_available = [] 
    more_dates = True 

    while more_dates:
        next_month_to_check, next_year_to_check = pd.to_datetime(next_date_to_check).month_name().str.lower(), int(pd.to_datetime(next_date_to_check).year)
        next_season_year = next_year_to_check if next_month_to_check in ["january", "february", "march", "april", "may", "june"] else next_year_to_check + 1            
        next_month_status_code = fetch_response_status_code(schedule_url(next_year_to_check, next_month_to_check), page_limit=page_limit)
        next_season_status_code = fetch_response_status_code(schedule_url(next_season_year, "october"), page_limit=page_limit)

        if next_month_status_code != 200 and next_season_status_code != 200: 
            more_dates = False 

        elif next_month_status_code == 200:
            dates_available.append(next_date_to_check)
            next_date_to_check = next_date_to_check + pd.DateOffset(months=1)
        
        elif next_season_status_code == 200:
            next_date_to_check = pd.Timestamp(year=next_season_year, month=10, day=1)

    dates_available = list(set(dates_available))
    return dates_available

def get_schedules_not_already_existing(years: list[int]) -> list[int]:
    years_existing = query_existing_years_in_table("game_schedule_history", "strftime('%Y', Date)")
    years_existing = [int(year) for year in years_existing]
    return [year for year in years if year not in years_existing]

def run(years: list[int], page_limit: int) -> None:
    years = get_schedules_not_already_existing(years)
    years = years + check_for_schedules_to_scrape(page_limit=15)

    if years:
        print(f"Getting game schedule history for years: {', '.join([str(i) for i in years])}")
        df = get_selected_years_game_schedule(years, page_limit)
        save_to_db(df, "game_schedule_history", if_exists="append")
