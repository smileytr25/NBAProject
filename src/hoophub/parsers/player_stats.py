from src.hoophub.utils.text_cleaning import remove_accents

def parse_player_stats(df, year):
    df["Player"] = df["Player"].apply(remove_accents)
    df = df.drop(columns=["Rk", "Awards"])
    df = df.loc[df.Team.ne("2TM"), :]
    df["Year"] = year 
    return df 