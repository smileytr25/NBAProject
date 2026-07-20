from pathlib import Path
from sqlalchemy import create_engine


def get_nba_db_engine():
    db_path = Path("~/Personal Project/data/nba.db").expanduser()
    return create_engine(f"sqlite:///{db_path}")
