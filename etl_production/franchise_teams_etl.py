import pandas as pd 
from pathlib import Path 
from sqlalchemy import create_engine

def move_all_team_history_to_database():
    url = "https://www.basketball-reference.com/teams/"

    active_franchises = pd.read_html(url, attrs={"id" : "teams_active"})[0]
    active_franchises["From"] = (active_franchises["From"].str[:2] + active_franchises["From"].str[-2:]).astype("int")
    active_franchises["To"] = (active_franchises["To"].str[:2] + active_franchises["To"].str[-2:]).astype("int")

    defunct_franchises = pd.read_html(url, attrs={"id" : "teams_defunct"})[0]
    defunct_franchises["From"] = (defunct_franchises["From"].str[:2] + defunct_franchises["From"].str[-2:]).astype("int")
    defunct_franchises["To"] = (defunct_franchises["To"].str[:2] + defunct_franchises["To"].str[-2:]).astype("int")

    team_histories = pd.concat([active_franchises, defunct_franchises], axis=0)
    team_histories = team_histories[
        ~(
            team_histories.groupby("Franchise")["Yrs"].transform("size").gt(1)
            & team_histories["Yrs"].eq(team_histories.groupby("Franchise")["Yrs"].transform("max"))
        )
    ].copy()

    season_members = (
        team_histories.assign(Year=team_histories.apply(lambda r: range(int(r["From"]), int(r["To"]) + 1), axis=1))
        .explode("Year", ignore_index=True)
    )

    season_members["Year"] = season_members["Year"].astype(int)
    season_members = season_members[["Franchise", "Year"]]

    db_path = Path("~/Personal Project/data/nba.db").expanduser()
    engine = create_engine(f"sqlite:///{db_path}")

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

if __name__ == "__main__":
    move_all_team_history_to_database()