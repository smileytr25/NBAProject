from bs4 import BeautifulSoup, Comment
import pandas as pd 
from io import StringIO 
from src.hoophub.crawler.fetch import fetch_response_content
from src.hoophub.crawler.urls import league_page_subsection_url
from src.hoophub.utils.database import get_nba_db_engine
from src.hoophub.parsers.eos_awards import parse_eos_awards

def get_year_eos_awards(year, page_limit):
    url = league_page_subsection_url(year, "all_awards")
    content = fetch_response_content(url, page_limit=page_limit)
    return parse_eos_awards(content, year)

def get_selected_years_eos_awards(years, page_limit):
    league_awards = []
    all_nba = []
    all_defensive = [] 
    all_rookie = []
    all_tourney = []

    for year in years:
        la, an, ad, ar, at = get_year_eos_awards(year, page_limit)
        league_awards.append(la)
        all_nba.append(an)
        all_defensive.append(ad)
        all_rookie.append(ar)
        all_tourney.append(at)
        print(f"End of season awards history added for year: {year}")

    league_awards = pd.concat(league_awards, axis=0, ignore_index=True) if league_awards else pd.DataFrame()
    all_nba = pd.concat(all_nba, axis=0, ignore_index=True) if all_nba else pd.DataFrame()
    all_defensive = pd.concat(all_defensive, axis=0, ignore_index=True) if all_defensive else pd.DataFrame()
    all_rookie = pd.concat(all_rookie, axis=0, ignore_index=True) if all_rookie else pd.DataFrame()
    all_tourney = pd.concat(all_tourney, axis=0, ignore_index=True) if all_tourney else pd.DataFrame()

    return league_awards, all_nba, all_defensive, all_rookie, all_tourney

def move_eos_awards_to_database(league_awards_df, all_nba_df, all_defensive_df, all_rookie_df, all_tourney_df):
    engine = get_nba_db_engine()

    league_awards_df.to_sql(
        "league_awards_history",
        engine,
        if_exists="append",
        index=False
    )

    all_nba_df.to_sql(
        "all-nba_history",
        engine,
        if_exists="append",
        index=False
    )

    all_defensive_df.to_sql(
        "all-defensive_history",
        engine,
        if_exists="append",
        index=False
    )

    all_rookie_df.to_sql(
        "all-rookie_history",
        engine,
        if_exists="append",
        index=False
    )

    all_tourney_df.to_sql(
        "all-tournament_history",
        engine,
        if_exists="append",
        index=False
    )

    print("Successfully moved to database.")


def run(years, page_limit):
    if years:
        print(f"Getting end of season awards history for years: {', '.join([str(i) for i in years])}")
        league_awards_df, alL_nba_df, all_defensive_df, all_rookie_df, all_tourney_df = get_selected_years_eos_awards(years, page_limit)
        move_eos_awards_to_database(league_awards_df, alL_nba_df, all_defensive_df, all_rookie_df, all_tourney_df)
    else:
        print("All years are accounted for.")
