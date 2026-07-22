import pandas as pd 
from hoophub.parsers.html import get_element_from_comment
from io import StringIO
from bs4 import BeautifulSoup

def parse_league_awards(soup: bytes, year: int) -> pd.DataFrame:
    if not soup.find("div", id="all_all_awards"):
        return pd.DataFrame() 
    
    data = {"player" : [], "accolade": []}

    table = get_element_from_comment(soup, "all_all_awards", "table", "all_awards")

    eos_awards_df = pd.read_html(StringIO(str(table)))[0]
    eos_awards_df["Award"] = eos_awards_df["Award"].str.split("(").str[0].str.strip()

    for _, row in eos_awards_df.iterrows():
        data["player"].append(row["Winner"])
        data["accolade"].append(row["Award"])

    df = pd.DataFrame(data)
    df["Year"] = year
    return df

def parse_all_nba(soup: bytes, year: int) -> pd.DataFrame:
    if not soup.find("div", id="all_all-nba"):
        return pd.DataFrame() 
    
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

    df = pd.DataFrame(data)
    df["Year"] = year
    return df

def parse_all_defensive(soup: bytes, year: int) -> pd.DataFrame:
    if not soup.find("div", id="all_all-defensive"):
            return pd.DataFrame()
        
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

    df = pd.DataFrame(data)
    df["Year"] = year
    return df 

def parse_all_rookie(soup: bytes, year: int) -> pd.DataFrame: 
    if not soup.find("div", id="all_all-rookie"):
        return pd.DataFrame()
    
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

    df = pd.DataFrame(data)
    df["Year"] = year
    return df 

def parse_all_tournament(soup: bytes, year: int) -> pd.DataFrame:
    if not soup.find("div", id="all_in-seasontournamentall-tournamentteam"):
            return pd.DataFrame()
        
    data = {"player" : [], "accolade": []}

    all_tourney_div = get_element_from_comment(
        soup, "all_in-seasontournamentall-tournamentteam",
        "div", "div_in-seasontournamentall-tournamentteam"
    )

    first_team = all_tourney_div.find("div", id="in-seasontournamentall-tournamentteam_1")

    for x in first_team.find_all("p"):
        data["player"].append(x.text.replace("\xa0", ""))
        data["accolade"].append("1st Team In-Season Tournament All-Tournament")

    df = pd.DataFrame(data)
    df["Year"] = year
    return df 

def parse_eos_awards(content: bytes, year: int) -> pd.DataFrame:
    soup = BeautifulSoup(content, "html.parser")
    
    league_awards = parse_league_awards(soup, year)
    all_nba = parse_all_nba(soup, year)
    all_defensive = parse_all_defensive(soup, year)
    all_rookie = parse_all_rookie(soup, year)
    all_tourney = parse_all_tournament(soup, year)

    return league_awards, all_nba, all_defensive, all_rookie, all_tourney