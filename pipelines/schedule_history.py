from sqlalchemy import text
import pandas as pd
import numpy as np
import sys
from pathlib import Path 
from urllib.error import HTTPError
project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from crawler.fetch import fetch_response_status_code, read_html
from crawler.urls import schedule_url
from utils.database import get_nba_db_engine

def get_month_game_schedule(month, year, page_limit):
    url = schedule_url(year, month)
    
    try:
        schedule = read_html(url, page_limit=page_limit, attrs={"id" : "schedule"})[0]

        schedule = schedule[schedule.Date.ne("Playoffs")]

        if "Start (ET)" not in schedule.columns.tolist():
            unnamed_drop = "Unnamed: 5"
            overtime_col = "Unnamed: 6"
        else:
            unnamed_drop = "Unnamed: 6"
            overtime_col = "Unnamed: 7"

        schedule = schedule.rename(columns = {
            "Start (ET)" : "Start_Time",
            "Visitor/Neutral" : "Visitor",
            "PTS" : "Visitor_PTS",
            "Home/Neutral" : "Home",
            "PTS.1" : "Home_PTS",
            overtime_col : "Overtime",
            "Attend." : "Attendance",
            "Notes" : "Game_Notes"
        }).drop(columns=["LOG", unnamed_drop], errors="ignore")

        schedule["Game_Notes"] = schedule["Game_Notes"].fillna("None")
        schedule["Overtime"] = schedule["Overtime"].fillna("None")
        schedule["Attendance"] = schedule["Attendance"].fillna(0)
        
        schedule["Date"] = pd.to_datetime(schedule["Date"])

        if "Start_Time" in schedule.columns.tolist() and schedule["Start_Time"].isna().sum():
            schedule = schedule.drop(columns=["Start_Time"])

        if "Start_Time" in schedule.columns.tolist():
            s = schedule["Start_Time"].str.strip().str.lower()
            s = s.str.replace(r"(\d)(a)$", r"\1AM", regex=True)
            s = s.str.replace(r"(\d)(p)$", r"\1PM", regex=True)

            schedule["Start_Time"] = pd.to_datetime(s, format="%I:%M%p", errors="coerce")
        
        print(f"Schedule history added for {month}, {year}")
        return schedule 
    except HTTPError as e:
        print(f"Schedule history finished with error for url: {url}, {month}, {year}")
        print(e)
        return pd.DataFrame()

def get_year_game_schedule(year, page_limit):
    months = [
        "october", "november", "december", "january", "february", "march", 
        "april", "may", "june"
    ]

    schedule = pd.DataFrame() 

    for month in months: 
        df = get_month_game_schedule(month, year, page_limit)
        schedule = pd.concat([schedule, df], axis=0)

    return schedule

def get_selected_years_game_schedule(years, page_limit):
    schedule = pd.DataFrame()

    for year in years:
        df = get_year_game_schedule(year, page_limit)
        schedule = pd.concat([schedule, df], axis=0)

    return schedule

def move_game_schedule_to_database(schedule):
    engine = get_nba_db_engine()

    schedule.to_sql(
        "game_schedule_history",
        engine,
        if_exists="append",
        index=False
    )

    print("Successfully moved to database.")

def check_for_schedules_to_scrape(page_limit=15):
    engine = get_nba_db_engine()

    with engine.connect() as conn:
        query = text("SELECT MAX(date) FROM game_schedule_history")
        last_date_in_db = pd.to_datetime(conn.execute(query).fetchone()[0])
        next_date_to_check = last_date_in_db + pd.DateOffset(months=1)

        dates_available = [] 
        more_dates = True 

        while more_dates:
            next_month_to_check, next_year_to_check = pd.to_datetime(next_date_to_check).dt.month_name.str.lower(), int(pd.to_datetime(next_date_to_check).dt.year)
            next_season_year = next_year_to_check if next_month_to_check in ["january", "february", "march", "april", "may", "june"] else next_year_to_check + 1            
            next_month_status_code = fetch_response_status_code(schedule_url(next_year_to_check, next_month_to_check), page_limit=page_limit)
            next_season_status_code = fetch_response_status_code(schedule_url(next_season_year, "october"), page_limit=page_limit)

            if next_month_status_code != 200 and next_season_status_code != 200: 
                more_dates = False 

            elif next_month_status_code == 200:
                dates_available.append(next_year_to_check)
                next_date_to_check = next_date_to_check + pd.DateOffset(months=1)
            
            elif next_season_status_code == 200:
                next_date_to_check = pd.Timestamp(year=next_season_year, month=10, day=1)

        dates_available = list(set(dates_available))
        return dates_available

def get_schedules_not_already_existing(years):
    engine = get_nba_db_engine()

    years_existing = []
    with engine.connect() as conn:
        years_existing += [year[0] for year in conn.execute(text("SELECT DISTINCT strftime('%Y', Date) FROM game_schedule_history")).fetchall()]

    return [year for year in years if year not in years_existing]

def run(years, page_limit):
    years = get_schedules_not_already_existing(years)
    years = years + check_for_schedules_to_scrape(page_limit=15)

    if years:
        print(f"Getting game schedule history for years: {', '.join([str(i) for i in years])}")
        df = get_selected_years_game_schedule(years, page_limit)
        move_game_schedule_to_database(df)
    else:
        print("All years are accounted for.")
