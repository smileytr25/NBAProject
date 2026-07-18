import pandas as pd 
import requests 
import numpy as np
from pathlib import Path 
from bs4 import BeautifulSoup, Comment
from io import StringIO 
from sqlalchemy import create_engine, text 
from urllib.error import HTTPError
import time 
import numpy as np 

def get_BAA_year_expanded_standings(year):
    url = f"https://www.basketball-reference.com/leagues/BAA_{year}_standings.html"
    r = requests.get(url)

    soup = BeautifulSoup(r.content, "html.parser")
    wrapper = soup.find("div", id="all_expanded_standings")

    table_comment = wrapper.find(
        string=lambda text: isinstance(text, Comment)
        and 'id="expanded_standings"' in text
    )

    table_soup = BeautifulSoup(table_comment, "html.parser")
    table = table_soup.find("table", id="expanded_standings")

    standings_df = pd.read_html(StringIO(str(table)))[0]
    standings_df.columns = [col[1] for col in standings_df.columns.to_flat_index()]

    for col in standings_df.columns:
        if col in ["Rk", "Team"]:
            continue 
        
        standings_df[f"{col}_wins"] = standings_df[col].fillna("0-0").str.split("-").str[0].astype("int")
        standings_df[f"{col}_losses"] = standings_df[col].fillna("0-0").str.split("-").str[1].astype("int")
        standings_df = standings_df.drop(columns=[col])

    standings_df = standings_df.rename(columns = {
        "Rk" : "rank", "Team" : "team", "Overall_wins" : "wins", "Overall_losses" : "losses",
        "Home_wins" : "home_wins", "Home_losses" : "home_losses", "Road_wins" : "away_wins",
        "Road_losses" : "away_losses", "Neutral_wins" : "neutral_wins", "Neutral_losses" : "neutral_losses",
        "E_wins" : "eastern_wins", "E_losses" : "eastern_losses", "W_wins" : "western_wins",
        "W_losses" : "western_losses", "≤3_wins" : "within_3pt_wins", "≤3_losses" : "within_3pt_losses",
        "≥10_wins" : "outside_10pt_wins", "≥10_losses" : "outside_10pt_losses", "Nov_wins" : "november_wins",
        "Nov_losses" : "november_losses", "Dec_wins" : "december_wins", "Dec_losses" : "december_losses",
        "Jan_wins" : "january_wins", "Jan_losses" : "january_losses", "Feb_wins" : "february_wins",
        "Feb_losses" : "february_losses", "Mar_wins" : "march_wins", "Mar_losses" : "march_losses"
    })

    division_mapping = {
        1947 : {
            "eastern" : [
                "Washington Capitols", "Philadelphia Warriors", "New York Knicks", "Providence Steamrollers",
                "Boston Celtics", "Toronto Huskies"
            ],
            "western" : [
                "Chicago Stags", "St. Louis Bombers", "Cleveland Rebels", "Detroit Falcons", "Pittsburgh Ironmen" 
            ]
        },

        1948 : {
            "eastern" : [
                "Philadelphia Warriors", "New York Knicks", "Boston Celtics", "Providence Steamrollers"
            ],
            "western" : [
                "St. Louis Bombers", "Baltimore Bullets", "Chicago Stags", "Washington Capitols"
            ]
        },

        1949 : {
            "eastern" : [
                "Washington Capitols", "New York Knicks", "Baltimore Bullets", "Philadelphia Warriors",
                "Boston Celtics", "Providence Steamrollers"
            ],
            "western" : {
                "Rochester Royals", "Minneapolis Lakers", "Chicago Stags", "St. Louis Bombers",
                "Fort Wayne Pistons", "Indianapolis Jets"
            }
        }
    }

    standings_df.loc[standings_df.team.isin(division_mapping[year]["eastern"]), "division"] = "eastern"
    standings_df.loc[~standings_df.team.isin(division_mapping[year]["western"]), "division"] = "western"

    standings_df["win_percentage"] = standings_df["wins"] / (standings_df["wins"] + standings_df["losses"])
    standings_df["home_win_percentage"] = standings_df["home_wins"] / (standings_df["home_wins"] + standings_df["home_losses"])
    standings_df["away_win_percentage"] = standings_df["away_wins"] / (standings_df["away_wins"] + standings_df["away_losses"])

    standings_df["year"] = year 

    if "neutral_wins" not in standings_df.columns:
        standings_df["neutral_wins"] = 0
        standings_df["neutral_losses"] = 0 

    return standings_df

def get_NBA1950_year_expanded_standings(year):
    url = f"https://www.basketball-reference.com/leagues/NBA_{year}_standings.html"
    r = requests.get(url)

    soup = BeautifulSoup(r.content, "html.parser")
    wrapper = soup.find("div", id="all_expanded_standings")

    table_comment = wrapper.find(
        string=lambda text: isinstance(text, Comment)
        and 'id="expanded_standings"' in text 
    )

    table_soup = BeautifulSoup(table_comment, "html.parser")
    table = table_soup.find("table", id="expanded_standings")

    standings_df = pd.read_html(StringIO(str(table)))[0]
    standings_df.columns = [col[1] for col in standings_df.columns.to_flat_index()]

    for col in standings_df.columns:
        if col in ["Rk", "Team"]:
            continue 
            
        standings_df[f"{col}_wins"] = standings_df[col].fillna("0-0").str.split("-").str[0].astype("int")
        standings_df[f"{col}_losses"] = standings_df[col].fillna("0-0").str.split("-").str[1].astype("int")
        standings_df = standings_df.drop(columns=[col])

    standings_df = standings_df.rename(columns = {
        "Rk" : "rank", "Team" : "team", "Overall_wins" : "wins", "Overall_losses" : "losses",
        "Home_wins" : "home_wins", "Home_losses" : "home_losses", "Road_wins" : "away_wins",
        "Road_losses" : "away_losses", "Neutral_wins" : "neutral_wins", "Neutral_losses" : "neutral_losses",
        "C_wins" : "central_wins", "C_losses" : "central_losses", "E_wins" : "eastern_wins",
        "E_losses" : "eastern_losses", "W_wins" : "western_wins", "W_losses" : "western_losses",
        "≤3_wins" : "within_3pt_wins", "≤3_losses" : "within_3pt_losses", '≥10_wins' : "outside_10pt_wins",
        '≥10_losses' : "outside_10pt_losses", "Oct_wins" : "october_wins", "Oct_losses" : "october_losses",
        "Nov_wins" : "november_wins", "Nov_losses" : "november_losses", "Dec_wins" : "december_wins",
        "Dec_losses" : "december_losses", "Jan_wins" : "january_wins", "Jan_losses" : "january_losses",
        "Feb_wins" : "february_wins", "Feb_losses" : "february_losses", "Mar_wins" : "march_wins",
        "Mar_losses" : "march_losses"
    })

    central_teams = [
        "Minneapolis Lakers", "Rochester Royals", "Fort Wayne Pistons", "Chicago Stags", "St. Louis Bombers"
    ]

    eastern_teams = [
        "Syracuse Nationals", "New York Knicks", "Washington Capitols", "Philadelphia Warriors",
        "Baltimore Bullets", "Boston Celtics"
    ]

    western_teams = [
        "Indianapolis Olympians", "Anderson Packers", "Tri-Cities Blackhawks", "Sheboygan Red Skins",
        "Waterloo Hawks", "Denver Nuggets"
    ]

    standings_df.loc[standings_df.team.isin(central_teams), "division"] = "central"
    standings_df.loc[standings_df.team.isin(eastern_teams), "division"] = "eastern"
    standings_df.loc[standings_df.team.isin(western_teams), "division"] = "western"

    standings_df["win_percentage"] = standings_df["wins"] / (standings_df["wins"] + standings_df["losses"])
    standings_df["home_win_percentage"] = standings_df["home_wins"] / (standings_df["home_wins"] + standings_df["home_losses"])
    standings_df["away_win_percentage"] = standings_df["away_wins"] / (standings_df["away_wins"] + standings_df["away_losses"])

    standings_df["year"] = year 

    return standings_df

def get_NBA1951_1970_year_expanded_standings(year):
    url = f"https://www.basketball-reference.com/leagues/NBA_{year}_standings.html"
    r = requests.get(url)

    if r.status_code != 200:
        raise ValueError("Got rate limited.")
    
    soup = BeautifulSoup(r.content, "html.parser")
    wrapper = soup.find("div", id="all_expanded_standings")

    table_comment = wrapper.find(
        string=lambda text: isinstance(text, Comment)
        and 'id="expanded_standings"' in text 
    )

    table_soup = BeautifulSoup(table_comment, "html.parser")
    table = table_soup.find("table", id="expanded_standings")

    standings_df = pd.read_html(StringIO(str(table)))[0]
    standings_df.columns = [col[1] for col in standings_df.columns.to_flat_index()]

    for col in standings_df.columns:
        if col in ["Rk", "Team"]:
            continue 
            
        standings_df[f"{col}_wins"] = standings_df[col].fillna("0-0").str.split("-").str[0].astype("int")
        standings_df[f"{col}_losses"] = standings_df[col].fillna("0-0").str.split("-").str[1].astype("int")
        standings_df = standings_df.drop(columns=[col])

    standings_df = standings_df.rename(columns = {
        "Rk" : "rank", "Team" : "team", "Overall_wins" : "wins", "Overall_losses" : "losses",
        "Home_wins" : "home_wins", "Home_losses" : "home_losses", "Road_wins" : "away_wins",
        "Road_losses" : "away_losses", "Neutral_wins" : "neutral_wins", "Neutral_losses" : "neutral_losses",
        "Pre_wins" : "pre_allstar_wins", "Pre_losses" : "pre_allstar_losses", "Post_wins" : "post_allstar_wins",
        "Post_losses" : "post_allstar_losses", "E_wins" : "eastern_wins", "E_losses" : "eastern_losses", 
        "W_wins" : "western_wins", "W_losses" : "western_losses", "≤3_wins" : "within_3pt_wins", 
        "≤3_losses" : "within_3pt_losses", '≥10_wins' : "outside_10pt_wins", '≥10_losses' : "outside_10pt_losses", 
        "Oct_wins" : "october_wins", "Oct_losses" : "october_losses", "Nov_wins" : "november_wins", "Nov_losses" : "november_losses", 
        "Dec_wins" : "december_wins", "Dec_losses" : "december_losses", "Jan_wins" : "january_wins", "Jan_losses" : "january_losses",
        "Feb_wins" : "february_wins", "Feb_losses" : "february_losses", "Mar_wins" : "march_wins", "Mar_losses" : "march_losses"
    })

    division_mapping = {
        "Philadelphia Warriors" : {
            "eastern" : [
                1951, 1952, 1953, 1954, 1955, 1956, 1957, 1958, 1959, 1960, 1961,
                1962
            ],
        },
        "Boston Celtics" : {
            "eastern" : [
                1951, 1952, 1953, 1954, 1955, 1956, 1957, 1958, 1959, 1960, 1961,
                1962, 1963, 1964, 1965, 1966, 1967, 1968, 1969, 1970
            ],
        },
        "New York Knicks" : {
            "eastern" : [
                1951, 1952, 1953, 1954, 1955, 1956, 1957, 1958, 1959, 1960, 1961,
                1962, 1963, 1964, 1965, 1966, 1967, 1968, 1969, 1970
            ],
        },
        "Syracuse Nationals" : {
            "eastern" : [
                1951, 1952, 1953, 1954, 1955, 1956, 1957, 1958, 1959, 1960, 1961,
                1962, 1963
            ],
        },
        "Baltimore Bullets" : {
            "eastern" : [1951, 1952, 1953, 1954, 1955, 1967, 1968, 1969, 1970],
            "western" : [1964, 1965, 1966],
        },
        "Washington Capitols" : {
            "eastern" : [1951],
        },
        "Minneapolis Lakers" : {
            "western" : [1951, 1952, 1953, 1954, 1955, 1956, 1957, 1958, 1959, 1960],
        },
        "Rochester Royals" : {
            "western" : [1951, 1952, 1953, 1954, 1955, 1956, 1957],
        },
        "Fort Wayne Pistons" : {
            "western" : [1951, 1952, 1953, 1954,  1955, 1956, 1957],
        },
        "Indianapolis Olympians" : {
            "western" : [1951, 1952, 1953],
        },
        "Tri-Cities Blackhawks" : {
            "western" : [1951],
        },
        "Milwaukee Hawks" : {
            "western" : [1952, 1953, 1954, 1955],
        },
        "St. Louis Hawks" : {
            "western" : [
                1956, 1957, 1958, 1959, 1960, 1961, 1962, 1963, 1964, 1965, 1966,
                1967, 1968
            ],
        },
        "Detroit Pistons" : {
            "western" : [
                1958, 1959, 1960, 1961, 1962, 1963, 1964, 1965, 1966, 1967
            ],
            "eastern" : [1968, 1969, 1970],
        },
        "Cincinnati Royals" : {
            "western" : [1958, 1959, 1960, 1961, 1962, 1965, 1966, 1967],
            "eastern" : [1963, 1964, 1968, 1969, 1970],
        },
        "Los Angeles Lakers" : {
            "western" : [
                1961, 1962, 1963, 1964, 1965, 1966, 1967, 1968, 1969,
                1970
            ],
        },
        "Chicago Packers" : {
            "western" : [1962],
        },
        "San Francisco Warriors" : {
            "western" : [1963, 1964, 1965, 1966, 1967, 1968, 1969, 1970],
        },
        "Chicago Zephyrs" : {
            "western" : [1963],
        },
        "Philadelphia 76ers" : {
            "eastern" : [1964, 1965, 1966, 1967, 1968, 1969, 1970],
        },
        "Chicago Bulls" : {
            "western" : [1967, 1968, 1969, 1970],
        },
        "Seattle SuperSonics" : {
            "western" : [1968, 1969, 1970],
        },
        "San Diego Rockets" : {
            "western" : [1968, 1969, 1970],
        },
        "Milwaukee Bucks" : {
            "eastern" : [1969, 1970],
        },
        "Atlanta Hawks" : {
            "western" : [1969, 1970],
        },
        "Phoenix Suns" : {
            "western" : [1969, 1970]
        }
    }

    for team in standings_df.team.unique():
        division_hist = division_mapping[team]

        for division, years in division_hist.items():
            if year in years:
                standings_df.loc[standings_df.team.eq(team), "division"] = division

    standings_df["win_percentage"] = standings_df["wins"] / (standings_df["wins"] + standings_df["losses"])
    standings_df["home_win_percentage"] = standings_df["home_wins"] / (standings_df["home_wins"] + standings_df["home_losses"])
    standings_df["away_win_percentage"] = standings_df["away_wins"] / (standings_df["away_wins"] + standings_df["away_losses"])

    standings_df["year"] = year 

    return standings_df

def get_NBA1971_2004_year_expanded_standings(year):
    url = f"https://www.basketball-reference.com/leagues/NBA_{year}_standings.html"
    r = requests.get(url)

    soup = BeautifulSoup(r.content, "html.parser")
    wrapper = soup.find("div", id="all_expanded_standings")

    table_comment = wrapper.find(
        string=lambda text: isinstance(text, Comment)
        and 'id="expanded_standings"' in text 
    )

    table_soup = BeautifulSoup(table_comment, "html.parser")
    table = table_soup.find("table", id="expanded_standings")

    standings_df = pd.read_html(StringIO(str(table)))[0]
    standings_df.columns = [col[1] for col in standings_df.columns.to_flat_index()]

    for col in standings_df.columns:
        if col in ["Rk", "Team"]:
            continue 
            
        standings_df[f"{col}_wins"] = standings_df[col].fillna("0-0").str.split("-").str[0].astype("int")
        standings_df[f"{col}_losses"] = standings_df[col].fillna("0-0").str.split("-").str[1].astype("int")
        standings_df = standings_df.drop(columns=[col])

    standings_df = standings_df.rename(columns = {
        "Rk" : "rank", "Team" : "team", "Overall_wins" : "wins", "Overall_losses" : "losses",
        "Home_wins" : "home_wins", "Home_losses" : "home_losses", "Road_wins" : "away_wins",
        "Road_losses" : "away_losses", "Neutral_wins" : "neutral_wins", "Neutral_losses" : "neutral_losses",
        "Pre_wins" : "pre_allstar_wins", "Pre_losses" : "pre_allstar_losses", "Post_wins" : "post_allstar_wins",
        "Post_losses" : "post_allstar_losses", "E_wins" : "eastern_wins", "E_losses" : "eastern_losses", 
        "W_wins" : "western_wins", "W_losses" : "western_losses", "A_wins" : "atlantic_wins", "A_losses" : "atlantic_losses",
        "C_wins" : "central_wins", "C_losses" : "central_losses", "M_wins" : "midwest_wins", "M_losses" : "midwest_losses",
        "P_wins" : "pacific_wins", "P_losses" : "pacific_losses", "≤3_wins" : "within_3pt_wins", "≤3_losses" : "within_3pt_losses", 
        '≥10_wins' : "outside_10pt_wins", '≥10_losses' : "outside_10pt_losses", "Oct_wins" : "october_wins", "Oct_losses" : "october_losses", 
        "Nov_wins" : "november_wins", "Nov_losses" : "november_losses", "Dec_wins" : "december_wins", "Dec_losses" : "december_losses", 
        "Jan_wins" : "january_wins", "Jan_losses" : "january_losses", "Feb_wins" : "february_wins", "Feb_losses" : "february_losses", "Mar_wins" : "march_wins", 
        "Mar_losses" : "march_losses", "Apr_wins" : "april_wins", "Apr_losses" : "april_losses", "May_wins" : "may_wins", "May_losses" : "may_losses"
    })

    conf_div_mapping = {
        "New York Knicks" : {
            "eastern" : {
                "atlantic" : [
                    1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982,
                    1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994,
                    1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004
                ],
            },
        },
        "Philadelphia 76ers" : {
            "eastern" : {
                "atlantic" : [
                    1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982,
                    1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994,
                    1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004
                ],
            },
        },
        "Boston Celtics" : {
            "eastern" : {
                "atlantic" : [
                    1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982,
                    1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994,
                    1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004
                ],
            },
        },
        "New York Nets" : {
            "eastern" : {
                "atlantic" : [1977],
            },
        },
        "New Jersey Nets" : {
            "eastern" : {
                "atlantic" : [
                    1978, 1979, 1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 
                    1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 
                    2002, 2003, 2004
                ],
            },
        },
        "Miami Heat" : {
            "western" : {
                "midwest" : [1989],
            },
            "eastern" : {
                "atlantic" : [
                    1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001,
                    2002, 2003, 2004
                ],
            },
        },
        "Orlando Magic" : {
            "eastern" : {
                "central" : [1990],
                "atlantic" : [
                    1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003,
                    2004
                ],
            },
            "western" : {
                "midwest" : [1991],
            },
        },
        "Washington Wizards" : {
            "eastern" : {
                "atlantic" : [1998, 1999, 2000, 2001, 2002, 2003, 2004],
            },
        },
        "Atlanta Hawks" : {
            "eastern" : {
                "central" : [
                    1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982,
                    1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994,
                    1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004
                ],
            },
        },
        "Cleveland Cavaliers" : {
            "eastern" : {
                "central" : [
                    1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982,
                    1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994,
                    1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004
                ],
            },
        },
        "Detroit Pistons" : {
            "western" : {
                "midwest" : [1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978],
            },
            "eastern" : {
                "central" : [
                    1979, 1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990,
                    1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002,
                    2003, 2004
                ],
            },
        },
        "Indiana Pacers" : {
            "western" : {
                "midwest" : [1977, 1978, 1979],
            },
            "eastern" : {
                "central" : [
                    1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991,
                    1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003,
                    2004
                ],
            },
        },
        "Milwaukee Bucks" : {
            "western" : {
                "midwest" : [1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980],
            },
            "eastern" : {
                "central" : [
                    1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992,
                    1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004
                ],
            },
        },
        "Chicago Bulls" : {
            "western" : {
                "midwest" : [1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980],
            },
            "eastern" : {
                "central" : [
                    1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992,
                    1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004
                ],
            },
        },
        "New Orleans Hornets" : {
            "eastern" : {
                "central" : [2003, 2004],
            },
        },
        "Toronto Raptors" : {
            "eastern" : {
                "central" : [1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004],
            },
        },
        "San Antonio Spurs" : {
            "eastern" : {
                "central" : [1977, 1978, 1979, 1980],
            },
            "western" : {
                "midwest" : [
                    1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992,
                    1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004
                ],
            },
        },
        "Houston Rockets" : {
            "western" : {
                "pacific" : [1972],
                "midwest" : [
                    1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992,
                    1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004
                ],
            },
            "eastern" : {
                "central" : [1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980],
            },
        },
        "Denver Nuggets" : {
            "western" : {
                "midwest" : [
                    1977, 1978, 1979, 1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988,
                    1989, 1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000,
                    2001, 2002, 2003, 2004
                ],
            },
        },
        "Utah Jazz" : {
            "western" : {
                "midwest" : [
                    1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991,
                    1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003,
                    2004
                ],
            },
        },
        "Dallas Mavericks" : {
            "western" : {
                "midwest" : [
                    1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992,
                    1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004
                ],
            },
        },
        "Minnesota Timberwolves" : {
            "western" : {
                "midwest" : [
                    1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001,
                    2002, 2003, 2004
                ],
            },
        },
        "Memphis Grizzlies" : {
            "western" : {
                "midwest" : [2002, 2003, 2004],
            },
        },
        "Sacramento Kings" : {
            "western" : {
                "midwest" : [1986, 1987, 1988],
                "pacific" : [
                    1989, 1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000,
                    2001, 2002, 2003, 2004
                ],
            },
        },
        "Los Angeles Lakers" : {
            "western" : {
                "pacific" : [
                    1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982,
                    1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994,
                    1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004
                ],
            },
        },
        "Golden State Warriors" : {
            "western" : {
                "pacific" : [
                    1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982, 1983,
                    1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994, 1995,
                    1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004
                ],
            },
        },
        "Seattle SuperSonics" : {
            "western" : {
                "pacific" : [
                    1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982,
                    1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994,
                    1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004
                ],
            },
        },
        "Portland Trail Blazers" : {
            "western" : {
                "pacific" : [
                    1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982,
                    1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994,
                    1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004
                ],
            },
        },
        "Phoenix Suns" : {
            "western" : {
                "midwest" : [1971, 1972],
                "pacific" : [
                    1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982, 1983, 1984,
                    1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994, 1995, 1996,
                    1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004
                ],
            },
        },
        "Los Angeles Clippers" : {
            "western" : {
                "pacific" : [
                    1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994, 1995, 1996,
                    1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004
                ],
            },
        },
        "San Francisco Warriors" : {
            "western" : {
                "pacific" : [1971],
            },
        },
        "San Diego Rockets" : {
            "western" : {
                "pacific" : [1971],
            },
        },
        "Kansas City-Omaha Kings" : {
            "western" : {
                "midwest" : [1973, 1974, 1975],
            },
        },
        "Capital Bullets" : {
            "eastern" : {
                "central" : [1974],
            },
        },
        "Cincinnati Royals" : {
            "eastern" : {
                "central" : [1971, 1972],
            },
        },
        "Baltimore Bullets" : {
            "eastern" : {
                "central" : [1971, 1972, 1973],
            },
        },
        "Buffalo Braves" : {
            "eastern" : {
                "atlantic" : [1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978],
            },
        },
        "New Orleans Jazz" : {
            "eastern" : {
                "central" : [1975, 1976, 1977, 1978, 1979],
            },
        },
        "San Diego Clippers" : {
            "western" : {
                "pacific" : [1979, 1980, 1981, 1982, 1983, 1984],
            },
        },
        "Kansas City Kings" : {
            "western" : {
                "midwest" : [1976, 1977, 1978, 1979, 1980, 1981, 1982, 1983, 1984, 1985],
            },
        },
        "Washington Bullets" : {
            "eastern" : {
                "central" : [1975, 1976, 1977, 1978],
                "atlantic" : [
                    1979, 1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990,
                    1991, 1992, 1993, 1994, 1995, 1996, 1997
                ]
            },
        },
        "Vancouver Grizzlies" : {
            "western" : {
                "midwest" : [1996, 1997, 1998, 1999, 2000, 2001],
            },
        },
        "Charlotte Hornets" : {
            "eastern" : {
                "atlantic" : [1989],
                "central" : [
                    1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002
                ],
            },
            "western" : {
                "midwest" : [1990],
            },
        }
    }

    for team in standings_df.team.unique():
        division_hist = conf_div_mapping[team]

        for conference, divisions in division_hist.items():
            for division, years in divisions.items():
                if year in years:
                    standings_df.loc[standings_df.team.eq(team), "conference"] = conference
                    standings_df.loc[standings_df.team.eq(team), "division"] = division

    standings_df["win_percentage"] = standings_df["wins"] / (standings_df["wins"] + standings_df["losses"])
    standings_df["home_win_percentage"] = standings_df["home_wins"] / (standings_df["home_wins"] + standings_df["home_losses"])
    standings_df["away_win_percentage"] = standings_df["away_wins"] / (standings_df["away_wins"] + standings_df["away_losses"])

    standings_df["year"] = year 

    for month in ["october", "november", "december", "january", "february", "march", "april", "may"]:
        if f"{month}_wins" not in standings_df.columns:
            standings_df[f"{month}_wins"] = 0
            standings_df[f"{month}_losses"] = 0

    if "neutral_wins" not in standings_df.columns:
        standings_df["neutral_wins"] = 0
        standings_df["neutral_losses"] = 0

    return standings_df

def get_NBA_after_2004_year_expanded_standings(year):
    url = f"https://www.basketball-reference.com/leagues/NBA_{year}_standings.html"
    r = requests.get(url)

    soup = BeautifulSoup(r.content, "html.parser")
    wrapper = soup.find("div", id="all_expanded_standings")

    table_comment = wrapper.find(
        string=lambda text: isinstance(text, Comment)
        and 'id="expanded_standings"' in text 
    )

    table_soup = BeautifulSoup(table_comment, "html.parser")
    table = table_soup.find("table", id="expanded_standings")

    standings_df = pd.read_html(StringIO(str(table)))[0]
    standings_df.columns = [col[1] for col in standings_df.columns.to_flat_index()]

    for col in standings_df.columns:
        if col in ["Rk", "Team"]:
            continue 

        standings_df[f"{col}_wins"] = standings_df[col].fillna("0-0").str.split("-").str[0].astype("int")
        standings_df[f"{col}_losses"] = standings_df[col].fillna("0-0").str.split("-").str[1].astype("int")
        standings_df = standings_df.drop(columns=[col])

    standings_df = standings_df.rename(columns = {
        "Rk" : "rank", "Team" : "team", "Overall_wins" : "wins", "Overall_losses" : "losses",
        "Home_wins" : "home_wins", "Home_losses" : "home_losses", "Road_wins" : "away_wins",
        "Road_losses" : "away_losses", "E_wins" : "eastern_wins", "E_losses" : "eastern_losses",
        "W_wins" : "western_wins", "W_losses" : "western_losses", "A_wins" : "atlantic_wins",
        "A_losses" : "atlantic_losses", "C_wins" : "central_wins", "C_losses" : "central_losses",
        "SE_wins" : "southeast_wins", "SE_losses" : "southeast_losses", "NW_wins" : "northwest_wins",
        "NW_losses" : "northwest_losses", "P_wins" : "pacific_wins", "P_losses" : "pacific_losses",
        "SW_wins" : "southwest_wins", "SW_losses" : "southwest_losses", "Pre_wins" : "pre_allstar_wins",
        "Pre_losses" : "pre_allstar_losses", "Post_wins" : "post_allstar_wins", "Post_losses" : "post_allstar_losses",
        "≤3_wins" : "within_3pt_wins", "≤3_losses" : "within_3pt_losses", '≥10_wins' : "outside_10pt_wins",
        '≥10_losses' : "outside_10pt_losses", "Oct_wins" : "october_wins", "Oct_losses" : "october_losses",
        "Nov_wins" : "november_wins", "Nov_losses" : "november_losses", "Dec_wins" : "december_wins",
        "Dec_losses" : "december_losses", "Jan_wins" : "january_wins", "Jan_losses" : "january_losses",
        "Feb_wins" : "february_wins", "Feb_losses" : "february_losses", "Mar_wins" : "march_wins",
        "Mar_losses" : "march_losses", "Apr_wins" : "april_wins", "Apr_losses" : "april_losses",
        "May_wins" : "may_wins", "May_losses" : "may_losses", "Jun_wins" : "june_wins", "Jun_losses" : "june_losses",
        "Jul_wins" : "july_wins", "Jul_losses" : "july_losses", "Aug_wins" : "august_wins", "Aug_losses" : "august_losses"
    })

    conf_div_mapping = {
        "eastern" : {
            "atlantic" : ["Boston Celtics", "Philadelphia 76ers", "New Jersey Nets", "Toronto Raptors", "New York Knicks", "Brooklyn Nets"],
            "central" : ["Detroit Pistons", "Chicago Bulls", "Indiana Pacers", "Cleveland Cavaliers", "Milwaukee Bucks"],
            "southeast" : [
                "Miami Heat", "Washington Wizards", "Orlando Magic", "Charlotte Bobcats", "Atlanta Hawks", "Charlotte Hornets"
            ],
        },
        "western" : {
            "northwest" : [
                "Seattle SuperSonics", "Denver Nuggets", "Minnesota Timberwolves", "Portland Trail Blazers", "Utah Jazz",
                "Oklahoma City Thunder"
            ],
            "pacific" : ["Phoenix Suns", "Sacramento Kings", "Los Angeles Clippers", "Los Angeles Lakers", "Golden State Warriors"],
            "southwest" : [
                "San Antonio Spurs", "Dallas Mavericks", "Houston Rockets", "Memphis Grizzlies", "New Orleans Hornets", 
                "New Orleans/Oklahoma City Hornets", "New Orleans Pelicans"
            ],
        }
    }

    for team in standings_df.team.unique():
        for conference, divisions in conf_div_mapping.items():
            for division, teams in divisions.items():
                if team in teams:
                    standings_df.loc[standings_df.team.eq(team), "conference"] = conference
                    standings_df.loc[standings_df.team.eq(team), "division"] = division

    standings_df["win_percentage"] = standings_df["wins"] / (standings_df["wins"] + standings_df["losses"])
    standings_df["home_win_percentage"] = standings_df["home_wins"] / (standings_df["home_wins"] + standings_df["home_losses"])
    standings_df["away_win_percentage"] = standings_df["away_wins"] / (standings_df["away_wins"] + standings_df["away_losses"])

    standings_df["year"] = year 

    for month in ["october", "november", "december", "january", "february", "march", "april", "may", "june", "july", "august"]:
        if f"{month}_wins" not in standings_df.columns:
            standings_df[f"{month}_wins"] = 0
            standings_df[f"{month}_losses"] = 0

    if "neutral_wins" not in standings_df.columns:
        standings_df["neutral_wins"] = 0
        standings_df["neutral_losses"] = 0

    return standings_df 

def get_year_team_vs_team(year):
    url = f"https://www.basketball-reference.com/leagues/{"BAA" if year < 1950 else "NBA"}_{year}_standings.html"
    r = requests.get(url)

    soup = BeautifulSoup(r.content, "html.parser")

    wrapper = soup.find("div", id="all_team_vs_team")

    table_comment = wrapper.find(
        string=lambda text: isinstance(text, Comment)
        and 'id="team_vs_team"' in text
    )

    table_soup = BeautifulSoup(table_comment, "html.parser")
    table = table_soup.find("table", id="team_vs_team")

    standings_df = pd.read_html(StringIO(str(table)))[0]    
    standings_df = standings_df.drop(columns=["Rk"]).fillna("0-0")
    standings_df.columns = ["Team"] + standings_df.Team.tolist()

    pivoted = pd.DataFrame(columns=["year", "team", "against", "wins", "losses"])

    for rn, row in standings_df.iterrows():
        for col_name, col_val in row.items():
            if col_name == "Team":
                continue 

            pivoted_row = {}
            pivoted_row["year"] = year
            pivoted_row["team"] = row["Team"]
            pivoted_row["against"] = col_name
            pivoted_row["wins"] = int(col_val.split("-")[0])
            pivoted_row["losses"] = int(col_val.split("-")[1])

            pivoted.loc[len(pivoted)] = pivoted_row 
    
    return standings_df, pivoted

def get_division_winners(conference_df):
    df = conference_df.copy()

    df["division_wp"] = df.apply(
        lambda row: row[f"{row['division']}_wins"]
        / (
            row[f"{row['division']}_wins"]
            + row[f"{row['division']}_losses"]
        ),
        axis=1
    )

    df = df.sort_values(["win_percentage", "division_wp"], ascending=False)
    
    df["division_rank"] = df.groupby("division").cumcount() + 1

    return df[df.division_rank.eq(1)].team.unique().tolist()

def break_ties(n_ties, conference_df, tvt, ties_history, wp, conference_rank, conference, conference_rk, tie_teams=None):
    tie_rows = conference_df[conference_df.win_percentage.eq(wp)]
    
    if not tie_teams: 
        tie_teams = tie_rows.team.unique().tolist()
    else:
        tie_rows = tie_rows[tie_rows.team.isin(tie_teams)]

    if tie_teams in ties_history:
        return "resolved"
    elif n_ties == 1:
        ties_history.append(tie_teams)

        team0_h2h_wins = int(tvt.loc[tvt.Team.eq(tie_teams[0]), tie_teams[1]].iloc[0].split("-")[0])
        team1_h2h_wins = int(tvt.loc[tvt.Team.eq(tie_teams[1]), tie_teams[0]].iloc[0].split("-")[0])

        if team0_h2h_wins > team1_h2h_wins:
            conference_rank[conference][tie_teams[0]] = conference_rk 
            conference_rank[conference][tie_teams[1]] = conference_rk + 1
            conference_rk += 2

        elif team1_h2h_wins > team0_h2h_wins:
            conference_rank[conference][tie_teams[1]] = conference_rk 
            conference_rank[conference][tie_teams[0]] = conference_rk + 1
            conference_rk += 2

        else:
            division_winners = get_division_winners(conference_df)

            if tie_teams[0] in division_winners and tie_teams[1] not in division_winners:
                conference_rank[conference][tie_teams[0]] = conference_rk 
                conference_rank[conference][tie_teams[1]] = conference_rk + 1
                conference_rk += 2
            
            elif tie_teams[1] in division_winners and tie_teams[0] not in division_winners:
                conference_rank[conference][tie_teams[1]] = conference_rk 
                conference_rank[conference][tie_teams[0]] = conference_rk + 1
                conference_rk += 2
            
            else:
                team0_division = tie_rows[tie_rows.team.eq(tie_teams[0])].division.iloc[0]
                team1_division = tie_rows[tie_rows.team.eq(tie_teams[1])].division.iloc[0]

                team0_div_wp = int(tie_rows.loc[tie_rows.team.eq(tie_teams[0]), f"{team0_division}_wins"].iloc[0]) / \
                    (
                        int(tie_rows.loc[tie_rows.team.eq(tie_teams[0]), f"{team0_division}_wins"].iloc[0]) + 
                        int(tie_rows.loc[tie_rows.team.eq(tie_teams[0]), f"{team0_division}_losses"].iloc[0])
                    )

                team1_div_wp = int(tie_rows.loc[tie_rows.team.eq(tie_teams[1]), f"{team1_division}_wins"].iloc[0]) / \
                    (
                        int(tie_rows.loc[tie_rows.team.eq(tie_teams[1]), f"{team1_division}_wins"].iloc[0]) + 
                        int(tie_rows.loc[tie_rows.team.eq(tie_teams[1]), f"{team1_division}_losses"].iloc[0])
                    )
                
                if team0_div_wp > team1_div_wp:
                    conference_rank[conference][tie_teams[0]] = conference_rk 
                    conference_rank[conference][tie_teams[1]] = conference_rk + 1
                    conference_rk += 2

                elif team1_div_wp > team0_div_wp:
                    conference_rank[conference][tie_teams[1]] = conference_rk 
                    conference_rank[conference][tie_teams[0]] = conference_rk + 1
                    conference_rk += 2

                else:
                    team0_conference = tie_rows[tie_rows.team.eq(tie_teams[0])].conference.iloc[0]
                    team1_conference = tie_rows[tie_rows.team.eq(tie_teams[1])].conference.iloc[0]

                    team0_conf_wp = int(tie_rows.loc[tie_rows.team.eq(tie_teams[0]), f"{team0_conference}_wins"].iloc[0]) / \
                        (
                            int(tie_rows.loc[tie_rows.team.eq(tie_teams[0]), f"{team0_conference}_wins"].iloc[0]) + 
                            int(tie_rows.loc[tie_rows.team.eq(tie_teams[0]), f"{team0_conference}_losses"].iloc[0])
                        )

                    team1_conf_wp = int(tie_rows.loc[tie_rows.team.eq(tie_teams[1]), f"{team1_conference}_wins"].iloc[0]) / \
                        (
                            int(tie_rows.loc[tie_rows.team.eq(tie_teams[1]), f"{team1_conference}_wins"].iloc[0]) + 
                            int(tie_rows.loc[tie_rows.team.eq(tie_teams[1]), f"{team1_conference}_losses"].iloc[0])
                        )
                    
                    if team0_conf_wp > team1_conf_wp:
                        conference_rank[conference][tie_teams[0]] = conference_rk 
                        conference_rank[conference][tie_teams[1]] = conference_rk + 1
                        conference_rk += 2

                    elif team1_conf_wp > team0_conf_wp:
                        conference_rank[conference][tie_teams[1]] = conference_rk 
                        conference_rank[conference][tie_teams[0]] = conference_rk + 1
                        conference_rk += 2

        return ties_history, conference_rank, conference_rk
    else: 
        division_winners = get_division_winners(conference_df)
        
        if tie_teams[0] in division_winners and tie_teams[1] not in division_winners and tie_teams[2] not in division_winners:
            conference_rank[conference][tie_teams[0]] = conference_rk 
            conference_rk += 1
            
            ties_history.append(tie_teams.copy()) 
            team_to_remove = tie_teams[0]
            tie_teams.remove(team_to_remove)

            ties_history, conference_rank, conference_rk = break_ties(n_ties - 1, conference_df, tvt, ties_history, wp, conference_rank, conference, conference_rk, tie_teams=tie_teams)

            return ties_history, conference_rank, conference_rk
        
        elif tie_teams[1] in division_winners and tie_teams[0] not in division_winners and tie_teams[2] not in division_winners:
            conference_rank[conference][tie_teams[1]] = conference_rk 
            conference_rk += 1
            
            ties_history.append(tie_teams.copy())
            team_to_remove = tie_teams[1]
            tie_teams.remove(team_to_remove)

            ties_history, conference_rank, conference_rk = break_ties(n_ties - 1, conference_df, tvt, ties_history, wp, conference_rank, conference, conference_rk, tie_teams=tie_teams)

            return ties_history, conference_rank, conference_rk

        elif tie_teams[2] in division_winners and tie_teams[0] not in division_winners and tie_teams[1] not in division_winners:
            conference_rank[conference][tie_teams[2]] = conference_rk 
            conference_rk += 1
            
            ties_history.append(tie_teams.copy())
            team_to_remove = tie_teams[2]
            tie_teams.remove(team_to_remove)

            ties_history, conference_rank, conference_rk = break_ties(n_ties - 1, conference_df, tvt, ties_history, wp, conference_rank, conference, conference_rk, tie_teams=tie_teams)

            return ties_history, conference_rank, conference_rk
        
        elif len([tm for tm in tie_teams if tm in division_winners]) == 2:
            non_division_winner = next(
                tm for tm in tie_teams
                if tm not in division_winners
            )

            conference_rank[conference][non_division_winner] = conference_rk + 2

            ties_history.append(tie_teams.copy())

            tie_teams.remove(non_division_winner)

            ties_history, conference_rank, conference_rk = break_ties(1, conference_df, tvt, ties_history, wp, conference_rank, conference, conference_rk, tie_teams)

            conference_rk += 1

            return ties_history, conference_rank, conference_rk
        
        else:
            h2h_wins_dict = {"team" : [], "h2h_wins" : []}
            for tm in tie_teams:
                h2h_wins = 0
                for other_team in [team for team in tie_teams if team != tm]:
                    h2h_wins += int(tvt.loc[tvt.Team.eq(tm), other_team].iloc[0].split("-")[0])
                h2h_wins_dict["team"].append(tm)
                h2h_wins_dict["h2h_wins"].append(h2h_wins)
            
            h2h = pd.DataFrame(data=h2h_wins_dict)
            max_wins = h2h.h2h_wins.max()
            n_teams = len(h2h[h2h.h2h_wins.eq(max_wins)])

            winning_team = h2h[h2h.h2h_wins.eq(max_wins)]["team"].iloc[0]

            if n_teams == 1:
                conference_rank[conference][winning_team] = conference_rk
                conference_rk += 1

                ties_history.append(tie_teams.copy())
                tie_teams.remove(winning_team)

                ties_history, conference_rank, conference_rk = break_ties(n_ties - 1, conference_df, tvt, ties_history, wp, conference_rank, conference, conference_rk, tie_teams=tie_teams)

                return ties_history, conference_rank, conference_rk 
            else:
                if tie_rows.division.nunique() == 1:
                    div_wp_dict = {"team" : [], "div_wp" : []}
                    for tm in tie_teams:
                        div_wins = int(tie_rows[tie_rows.team.eq(tm)][f"{tie_rows[tie_rows.team.eq(tm)].division.iloc[0]}_wins"].iloc[0])
                        div_total = div_wins + int(tie_rows[tie_rows.team.eq(tm)][f"{tie_rows[tie_rows.team.eq(tm)].division.iloc[0]}_losses"].iloc[0])
                        div_wp_dict["team"].append(tm)
                        div_wp_dict["div_wp"].append(div_wins / div_total)

                    div_wp = pd.DataFrame(data=div_wp_dict)
                    max_wp = div_wp.div_wp.max()
                    n_teams = len(div_wp[div_wp.div_wp.eq(max_wp)])

                    winning_team = div_wp[div_wp.div_wp.eq(max_wp)]["team"].iloc[0]

                    if n_teams == 1:
                        conference_rank[conference][winning_team] = conference_rk
                        conference_rk += 1

                        ties_history.append(tie_teams.copy())
                        tie_teams.remove(winning_team)

                        ties_history, conference_rank, conference_rk = break_ties(n_ties - 1, conference_df, tvt, ties_history, wp, conference_rank, conference, conference_rk, tie_teams=tie_teams)

                        return ties_history, conference_rank, conference_rk
                    
                    else:
                        conf_wp_dict = {"team" : [], "conf_wp" : []}
                        for tm in tie_teams:
                            conf_wins = int(tie_rows[tie_rows.team.eq(tm)][f"{tie_rows[tie_rows.team.eq(tm)].conference.iloc[0]}_wins"].iloc[0])
                            conf_total = conf_wins + int(tie_rows[tie_rows.team.eq(tm)][f"{tie_rows[tie_rows.team.eq(tm)].conference.iloc[0]}_losses"].iloc[0])
                            conf_wp_dict["team"].append(tm)
                            conf_wp_dict["conf_wp"].append(conf_wins / conf_total)

                        conf_wp = pd.DataFrame(data=conf_wp_dict)
                        max_wp = conf_wp.conf_wp.max()
                        n_teams = len(conf_wp[conf_wp.conf_wp.eq(max_wp)])

                        winning_team = conf_wp[conf_wp.conf_wp.eq(max_wp)]["team"].iloc[0]

                        if n_teams == 1:
                            conference_rank[conference][winning_team] = conference_rk
                            conference_rk += 1

                            ties_history.append(tie_teams.copy())
                            tie_teams.remove(winning_team)

                            ties_history, conference_rank, conference_rk = break_ties(n_ties - 1, conference_df, tvt, ties_history, wp, conference_rank, conference, conference_rk, tie_teams=tie_teams)

                            return ties_history, conference_rank, conference_rk
                        
                        else:
                            raise ValueError("MAYDAY MAYDAY!!!")
                        
                else:
                    conf_wp_dict = {"team" : [], "conf_wp" : []}
                    for tm in tie_teams:
                        conf_wins = int(tie_rows[tie_rows.team.eq(tm)][f"{tie_rows[tie_rows.team.eq(tm)].conference.iloc[0]}_wins"].iloc[0])
                        conf_total = conf_wins + int(tie_rows[tie_rows.team.eq(tm)][f"{tie_rows[tie_rows.team.eq(tm)].conference.iloc[0]}_losses"].iloc[0])
                        conf_wp_dict["team"].append(tm)
                        conf_wp_dict["conf_wp"].append(conf_wins / conf_total)

                    conf_wp = pd.DataFrame(data=conf_wp_dict)
                    max_wp = conf_wp.conf_wp.max()
                    n_teams = len(conf_wp[conf_wp.conf_wp.eq(max_wp)])

                    winning_team = conf_wp[conf_wp.conf_wp.eq(max_wp)]["team"].iloc[0]

                    if n_teams == 1:
                        conference_rank[conference][winning_team] = conference_rk
                        conference_rk += 1

                        ties_history.append(tie_teams.copy())
                        tie_teams.remove(winning_team)

                        ties_history, conference_rank, conference_rk = break_ties(n_ties - 1, conference_df, tvt, ties_history, wp, conference_rank, conference, conference_rk, tie_teams=tie_teams)

                        return ties_history, conference_rank, conference_rk
                        
                    else:
                        raise ValueError("MAYDAY MAYDAY!!!")
                        
def get_conference_rank(expanded_standings, team_vs_team):
    df = expanded_standings.copy() 
    tvt = team_vs_team.copy() 

    conference_rk = 1

    ties_history = []
    conference_rank = {conf : {} for conf in df.conference.unique()}

    for conference in df.conference.unique():
        conference_df = df[df.conference.eq(conference)].sort_values("win_percentage", ascending=False)

        for rn, row in conference_df.iterrows():
            if row["team"] in conference_rank[conference]:
                continue 

            wp = row["win_percentage"]
            n_ties = len(conference_df[conference_df.win_percentage.eq(wp)]) - 1

            if not n_ties: 
                conference_rank[conference][row["team"]] = conference_rk
                conference_rk += 1
            
            else:
                result = break_ties(n_ties, conference_df, tvt, ties_history, wp, conference_rank, conference, conference_rk)
                if result == "resolved":
                    continue 
                else:
                    ties_history, conference_rank, conference_rk = result 
        if len(conference_rank[conference]) < len(conference_df):
            raise ValueError("Need to revisit the function code to add more tiebreakers")
        for tm, rank in conference_rank[conference].items():
            df.loc[df.team.eq(tm), "conference_rank"] = rank

        conference_rk = 1      
                    
    return df

def get_year_standings(year, page_limit, pages_visited=0, start_time=None):
    if not start_time: 
        start_time = time.time() 

    if pages_visited == page_limit:
        wait_time = max(0, 60 - (time.time() - start_time))
        print(f"Rate limited. Waiting for {wait_time:.2f} seconds")
        time.sleep(wait_time)

        pages_visited = 0
        start_time = time.time()
    
    expanded_standings = None
    if year < 1950:
        expanded_standings = get_BAA_year_expanded_standings(year)
    elif year == 1950:
        expanded_standings = get_NBA1950_year_expanded_standings(year)
    elif year <= 1970:
        expanded_standings = get_NBA1951_1970_year_expanded_standings(year)
    elif year <= 2004:
        expanded_standings = get_NBA1971_2004_year_expanded_standings(year)
    else:
        expanded_standings = get_NBA_after_2004_year_expanded_standings(year)

    pages_visited += 1

    if pages_visited == page_limit:
        wait_time = max(0, 60 - (time.time() - start_time))
        print(f"Rate limited. Waiting for {wait_time:.2f} seconds")
        time.sleep(wait_time)

        pages_visited = 0
        start_time = time.time()

    team_vs_team, pivoted_team_vs_team = get_year_team_vs_team(year)

    pages_visited += 1

    if year >= 1971:
        expanded_standings = get_conference_rank(expanded_standings, team_vs_team)

    print(f"Added standings history for {year}")

    return expanded_standings, pivoted_team_vs_team, pages_visited, start_time 

def get_standings_not_already_existing(years):
    db_path = Path("~/Personal Project/data/nba.db").expanduser()
    engine = create_engine(f"sqlite:///{db_path}")

    years_existing = []
    with engine.connect() as conn:
        tables = [
            "standings_history_after_2004",
            "standings_history_after_1970_to_2004",
            "standings_history_after_1950_to_1970",
            "standings_history_1950",
            "standings_history_before_1950"
        ]
        
        for table in tables:
            try:
                years_existing += [year[0] for year in conn.execute(text(f"SELECT DISTINCT year FROM {table}")).fetchall()]
            except Exception:
                pass
        
    return [year for year in years if year not in years_existing]

def move_standings_to_database(expanded_standings, team_vs_team, year):
    db_path = Path("~/Personal Project/data/nba.db").expanduser()
    engine = create_engine(f"sqlite:///{db_path}")

    after_2004_standings = expanded_standings[expanded_standings.year.ge(2005)]
    after_1970_standings = expanded_standings[expanded_standings.year.ge(1971) & expanded_standings.year.lt(2005)]
    after_1950_standings = expanded_standings[expanded_standings.year.ge(1951) & expanded_standings.year.lt(1971)]
    equal_1950_standings = expanded_standings[expanded_standings.year.eq(1950)]
    before_1950_standings = expanded_standings[expanded_standings.year.lt(1950)]

    if len(after_2004_standings):
        after_2004_standings.to_sql(
            "standings_history_after_2004",
            engine,
            if_exists="append",
            index=False
        )

    if len(after_1970_standings):
        after_1970_standings.to_sql(
            "standings_history_after_1970_to_2004",
            engine,
            if_exists="append",
            index=False
        )

    if len(after_1950_standings):
        after_1950_standings.to_sql(
            "standings_history_after_1950_to_1970",
            engine,
            if_exists="append",
            index=False
        )

    if len(equal_1950_standings):
        equal_1950_standings.to_sql(
            "standings_history_1950",
            engine,
            if_exists="append",
            index=False
        )

    if len(before_1950_standings):
        before_1950_standings.to_sql(
            "standings_history_before_1950",
            engine,
            if_exists="append",
            index=False
        )

    team_vs_team.to_sql(
        "head_to_head_history",
        engine,
        if_exists="append",
        index=False
    )

    print(f"Successfully moved {year} standings to database.")

def standings_history_etl(years, page_limit):
    pages_visited = 0
    start_time = time.time()

    years = get_standings_not_already_existing(years)

    if years:
        for year in years:
            expanded_standings, pivoted_team_vs_team, pages_visited, start_time = get_year_standings(year, 15, pages_visited, start_time)
            move_standings_to_database(expanded_standings, pivoted_team_vs_team, year)
    else:
        print("All years are accounted for.")

if __name__ == "__main__": 
    standings_history_etl(list(range(1947, 2027)), 15)
