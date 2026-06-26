from sqlalchemy import text, create_engine
import pandas as pd
import numpy as np
import time 
from pathlib import Path 
from urllib.error import HTTPError
import requests 

def get_month_game_schedule(month, year):
    url = f"https://www.basketball-reference.com/leagues/{"NBA" if year >= 1950 else "BAA"}_{year}_games-{month}.html"
    
    try:
        schedule = pd.read_html(url, attrs={"id" : "schedule"})[0]

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

def get_year_game_schedule(year, page_limit, pages_visited=0, start_time=None):
    months = [
        "october", "november", "december", "january", "february", "march", 
        "april", "may", "june"
    ]

    schedule = pd.DataFrame() 

    if not start_time:
        start_time = time.time()

    for month in months: 
        if pages_visited == page_limit: 
            wait_time = max(0, 60 - (time.time() - start_time))
            print(f"Rate limited. Waiting for {wait_time:.2f} seconds")
            time.sleep(wait_time)

            pages_visited = 0
            start_time = time.time()

        df = get_month_game_schedule(month, year)
        schedule = pd.concat([schedule, df], axis=0)
        pages_visited += 1

    return schedule, pages_visited, start_time

def get_selected_years_game_schedule(years, page_limit):
    schedule = pd.DataFrame()
    pages_visited = 0
    start_time = None

    for year in years:
        df, pages_visited, start_time = get_year_game_schedule(year, page_limit, pages_visited=pages_visited, start_time=start_time)
        schedule = pd.concat([schedule, df], axis=0)

    return schedule

def move_game_schedule_to_database(schedule):
    db_path = Path("~/Personal Project/data/nba.db").expanduser()
    engine = create_engine(f"sqlite:///{db_path}")

    schedule.to_sql(
        "game_schedule_history",
        engine,
        if_exists="append",
        index=False
    )

    print("Successfully moved to database.")

def check_for_schedules_to_scrape(page_limit=15):
    db_path = Path("~/Personal Project/data/nba.db").expanduser()
    engine = create_engine(f"sqlite:///{db_path}")

    with engine.connect() as conn:
        query = text("SELECT MAX(date) FROM game_schedule_history")
        last_date_in_db = pd.to_datetime(conn.execute(query).fetchone()[0])
        next_date_to_check = last_date_in_db + pd.DateOffset(months=1)

        dates_available = [] 
        more_dates = True 

        pages_visited = 0
        start_time = time.time()

        while more_dates:
            next_month_to_check, next_year_to_check = pd.to_datetime(next_date_to_check).dt.month_name.str.lower(), int(pd.to_datetime(next_date_to_check).dt.year)
            next_season_year = next_year_to_check if next_month_to_check in ["january", "february", "march", "april", "may", "june"] else next_year_to_check + 1
            
            if pages_visited == page_limit:
                wait_time = max(0, 60 - (time.time() - start_time))
                print(f"Rate limited. Waiting for {wait_time:.2f} seconds")
                time.sleep(wait_time)
                pages_visited = 0
                start_time = time.time()
            
            next_month_status_code = requests.get(f"https://www.basketball-reference.com/leagues/NBA_{next_year_to_check}_games-{next_month_to_check}.html")
            pages_visited += 1

            if pages_visited == page_limit:
                wait_time = max(0, 60 - (time.time() - start_time))
                print(f"Rate limited. Waiting for {wait_time:.2f} seconds")
                time.sleep(wait_time)
                pages_visited = 0
                start_time = time.time()

            next_season_status_code = requests.get(f"https://www.basketball-reference.com/leagues/NBA_{next_season_year}_games-october.html")
            pages_visited += 1

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
    db_path = Path("~/Personal Project/data/nba.db").expanduser()
    engine = create_engine(f"sqlite:///{db_path}")

    years_existing = []
    with engine.connect() as conn:
        years_existing += [year[0] for year in conn.execute(text("SELECT DISTINCT strftime('%Y', Date) FROM game_schedule_history")).fetchall()]

    return [year for year in years if year not in years_existing]

def game_schedule_history_etl(years, page_limit):
    if years:
        print(f"Getting game schedule history for years: {', '.join([str(i) for i in years])}")
        df = get_selected_years_game_schedule(years, page_limit)
        move_game_schedule_to_database(df)
    else:
        print("All years are accounted for.")

if __name__ == "__main__":
    game_schedule_history_etl(list(range(1947, 2027)), 15)