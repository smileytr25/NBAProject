import pandas as pd 
from src.hoophub.crawler.fetch import read_html
from src.hoophub.crawler.urls import all_teams_url
from src.hoophub.utils.database import get_nba_db_engine
from src.hoophub.parsers.franchises import parse_franchises

def run():
    url = all_teams_url()

    active_franchises = read_html(url, attrs={"id" : "teams_active"})[0]
    defunct_franchises = read_html(url, attrs={"id" : "teams_defunct"})[0]
    team_histories, season_members = parse_franchises(active_franchises, defunct_franchises)

    engine = get_nba_db_engine()

    team_histories.to_sql(
        "franchies_histories",
        engine,
        if_exists="replace",
        index=False
    )

    season_members.to_sql(
        "season_teams",
        engine,
        if_exists="replace",
        index=False
    )

    print("Successfully moved to database.")
