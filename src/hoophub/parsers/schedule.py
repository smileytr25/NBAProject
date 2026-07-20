import pandas as pd 

def parse_schedule():
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

    return schedule 