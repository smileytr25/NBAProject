from bs4 import BeautifulSoup, Comment
import pandas as pd 
from io import StringIO 
from src.hoophub.crawler.fetch import fetch_response_content
from src.hoophub.crawler.urls import league_page_subsection_url
from src.hoophub.utils.database import get_nba_db_engine

def get_element_from_comment(soup, wrapper_id, element_type, element_id):
    wrapper = soup.find("div", id=wrapper_id)
    
    element_comment = wrapper.find(
        string=lambda text: isinstance(text, Comment)
        and f'id="{element_id}"' in text
    )

    element_soup = BeautifulSoup(element_comment, "html.parser")
    element = element_soup.find(element_type, id=element_id)

    return element 

def get_year_league_awards(soup):
    if not soup.find("div", id="all_all_awards"):
        return None 
    
    data = {"player" : [], "accolade": []}

    table = get_element_from_comment(soup, "all_all_awards", "table", "all_awards")

    eos_awards_df = pd.read_html(StringIO(str(table)))[0]
    eos_awards_df["Award"] = eos_awards_df["Award"].str.split("(").str[0].str.strip()

    for idx, row in eos_awards_df.iterrows():
        data["player"].append(row["Winner"])
        data["accolade"].append(row["Award"])

    return pd.DataFrame(data)

def get_year_all_nba(soup):
    if not soup.find("div", id="all_all-nba"):
        return None 
    
    data = {"player" : [], "accolade": []}

    all_nba_div = get_element_from_comment(soup, "all_all-nba", "div", 'div_all-nba')

    first_team = all_nba_div.find("div", id="all-nba_1")
    second_team = all_nba_div.find("div", id="all-nba_2")
    third_team = all_nba_div.find("div", id="all-nba_3") 

    if first_team:
        for x in first_team.find_all("p"):
            data["player"].append(x.text.replace("\xa0", ""))
            data["accolade"].append("1st Team All-NBA")

    if second_team:
        for x in second_team.find_all("p"):
            data["player"].append(x.text.replace("\xa0", ""))
            data["accolade"].append("2nd Team All-NBA")

    if third_team:
        for x in third_team.find_all("p"):
            data["player"].append(x.text.replace("\xa0", ""))
            data["accolade"].append("3rd Team All-NBA")

    return pd.DataFrame(data)

def get_year_all_defensive(soup):
    if not soup.find("div", id="all_all-defensive"):
        return None 
    
    data = {"player" : [], "accolade": []}

    all_defensive_div = get_element_from_comment(soup, "all_all-defensive", "div", "div_all-defensive")

    first_team = all_defensive_div.find("div", id="all-defensive_1")
    second_team = all_defensive_div.find("div", id="all-defensive_2")

    if first_team:
        for x in first_team.find_all("p"):
            data["player"].append(x.text.replace("\xa0", ""))
            data["accolade"].append("1st Team All-Defensive")

    if second_team:
        for x in second_team.find_all("p"):
            data["player"].append(x.text.replace("\xa0", ""))
            data["accolade"].append("2nd Team All-Defensive")

    return pd.DataFrame(data)

def get_year_all_rookie(soup):
    if not soup.find("div", id="all_all-rookie"):
        return 
    data = {"player" : [], "accolade": []}

    all_rookie_div = get_element_from_comment(soup, "all_all-rookie", "div", "div_all-rookie")

    first_team = all_rookie_div.find("div", id="all-rookie_1")
    second_team = all_rookie_div.find("div", id="all-rookie_2")

    if first_team:
        for x in first_team.find_all("p"):
            data["player"].append(x.text.replace("\xa0", ""))
            data["accolade"].append("1st Team All-Rookie")

    if second_team:
        for x in second_team.find_all("p"):
            data["player"].append(x.text.replace("\xa0", ""))
            data["accolade"].append("2nd Team All-Rookie")

    return pd.DataFrame(data)

def get_year_in_season_tournament_all_tournament_team(soup): 
    if not soup.find("div", id="all_in-seasontournamentall-tournamentteam"):
        return None 
    
    data = {"player" : [], "accolade": []}

    all_tourney_div = get_element_from_comment(
        soup, "all_in-seasontournamentall-tournamentteam",
        "div", "div_in-seasontournamentall-tournamentteam"
    )

    first_team = all_tourney_div.find("div", id="in-seasontournamentall-tournamentteam_1")

    for x in first_team.find_all("p"):
        data["player"].append(x.text.replace("\xa0", ""))
        data["accolade"].append("1st Team In-Season Tournament All-Tournament")

    return pd.DataFrame(data)

def get_year_eos_awards(year, page_limit):
    data = {"player" : [], "accolade" : []}

    url = league_page_subsection_url(year, "all_awards")
    content = fetch_response_content(url, page_limit=page_limit)

    soup = BeautifulSoup(content, "html.parser")
    
    league_awards = get_year_league_awards(soup)
    all_nba = get_year_all_nba(soup)
    all_defensive = get_year_all_defensive(soup)
    all_rookie = get_year_all_rookie(soup)
    all_tourney = get_year_in_season_tournament_all_tournament_team(soup)
    
    return league_awards, all_nba, all_defensive, all_rookie, all_tourney

def get_selected_years_eos_awards(years, page_limit):
    all_year_dfs = {
        "league_awards" : pd.DataFrame(),
        "all_nba" : pd.DataFrame(),
        "all_defensive" : pd.DataFrame(),
        "all_rookie" : pd.DataFrame(),
        "all_tourney" : pd.DataFrame()
    }

    for year in years:
        if year < 1947:
            print(f"Year is invalid. Skipping {year}...")
            continue 

        results = get_year_eos_awards(year, page_limit)

        for name, result_set in zip(all_year_dfs, results):
            
            if not isinstance(result_set, pd.DataFrame):
                continue 

            result_set = result_set.copy()
            result_set["year"] = year 

            all_year_dfs[name] = pd.concat([all_year_dfs[name], result_set], ignore_index=True, axis=0)

        print(f"End of season awards history added for year: {year}")

    league_awards_df = all_year_dfs["league_awards"]
    all_nba_df = all_year_dfs["all_nba"]
    all_defensive_df = all_year_dfs["all_defensive"]
    all_rookie_df = all_year_dfs["all_rookie"]
    all_tourney_df = all_year_dfs["all_tourney"]

    return league_awards_df, all_nba_df, all_defensive_df, all_rookie_df, all_tourney_df

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
