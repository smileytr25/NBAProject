import pandas as pd 

def parse_franchises(active_franchises: pd.DataFrame, defunct_franchises: pd.DataFrame):

    active_franchises["From"] = (active_franchises["From"].str[:2] + active_franchises["From"].str[-2:]).astype("int")
    active_franchises["To"] = (active_franchises["To"].str[:2] + active_franchises["To"].str[-2:]).astype("int")
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

    return team_histories, season_members   