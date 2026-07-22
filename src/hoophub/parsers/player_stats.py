from src.hoophub.utils.text_cleaning import remove_accents
import pandas as pd 

def parse_player_stats(df: pd.DataFrame, year: int):
    df["Player"] = df["Player"].apply(remove_accents)
    df = df.drop(columns=["Rk", "Awards"])
    df = df.loc[df.Team.ne("2TM"), :]
    df["Year"] = year 
    return df 