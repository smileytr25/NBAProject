import pandas as pd 
from hoophub.crawler.fetch import read_html
from hoophub.crawler.urls import all_teams_url
from hoophub.parsers.franchises import parse_franchises
from hoophub.repository.save import save_franchises_to_db

def run() -> None:
    url = all_teams_url()
    active_franchises = read_html(url, attrs={"id" : "teams_active"})[0]
    defunct_franchises = read_html(url, attrs={"id" : "teams_defunct"})[0]
    team_histories, season_members = parse_franchises(active_franchises, defunct_franchises)
    save_franchises_to_db(team_histories, season_members)

