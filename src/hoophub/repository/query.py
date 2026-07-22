from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from typing import Any
from hoophub.repository.engine import get_nba_db_engine

engine = get_nba_db_engine()

def query_last_year_in_table(table_name: str, year_col: str, default_max: Any = 1946):
    try:
        with engine.connect() as conn:
            query = text(f"SELECT MAX({year_col}) FROM {table_name}")
            last_year_in_db = conn.execute(query).fetchone()[0]
            return default_max if last_year_in_db is None else last_year_in_db
    except SQLAlchemyError:
        return default_max
    
def query_existing_years_in_table(table_name: str, year_col: str):
    try:
        with engine.connect() as conn:
            return [year[0] for year in conn.execute(text(f"SELECT DISTINCT {year_col} FROM {table_name}")).fetchall()]
    except SQLAlchemyError:
        return []
