import pandas as pd 
from src.hoophub.repository.engine import get_nba_db_engine

def save_to_db(data: pd.DataFrame, table: str, if_exists: str):
    engine = get_nba_db_engine()
    data.to_sql(
        table,
        engine,
        if_exists=if_exists,
        index=False
    )

def save_awards_to_db(league_awards_df, all_nba_df, all_defensive_df, all_rookie_df, all_tourney_df):
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

def save_franchises_to_db(team_histories: pd.DataFrame, season_members: pd.DataFrame):
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


def save_standings_to_db(expanded_standings, team_vs_team):
    engine = get_nba_db_engine()
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