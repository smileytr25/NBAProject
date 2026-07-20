import pandas as pd 

def parse_draft(df: pd.DataFrame, year: int):
    df.columns = [i[1] for i in df.columns.to_flat_index()]
    df = df[["Rk", "Pk", "Tm", "Player", "College"]].copy()
    df["Rk"] = pd.to_numeric(df["Rk"], errors="coerce")
    df = df[df.Rk.notna() & df.Player.notna()]
    df["College"] = df["College"].fillna("None")
    df["Year"] = year
    return df