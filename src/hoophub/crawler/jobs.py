from hoophub.repository.engine import get_nba_db_engine
from hoophub.crawler.urls import roster_url
from hoophub.crawler.fetch import fetch_response_text
from hoophub.crawler.cache import R2CacheBackend, Cache
import pandas as pd 
from tqdm.auto import tqdm 

def crawl_rosters():
    cache = Cache(R2CacheBackend())
    engine = get_nba_db_engine()

    with engine.connect() as conn:
        season_teams = pd.read_sql("SELECT Franchise, Year FROM season_teams", engine)
        mappings = pd.read_sql("SELECT * FROM team_abbreviation_to_teamname", engine)

    years = season_teams.Year.unique() 
    urls = [] 

    for year in years:
        teams = season_teams[season_teams.Year.eq(year)]
        year_mapping = mappings[mappings.start_year.le(year) & mappings.end_year.ge(year)]
        year_mapping = {tm : abbrev for tm, abbrev in zip(year_mapping["teamname"], year_mapping["abbreviation"])}

        abbrevs = teams["Franchise"].map(year_mapping).dropna().unique()
        urls += [roster_url(year, abbrev) for abbrev in abbrevs]

    for url in tqdm(urls, desc="Caching roster pages", unit="page"):
        print(url)
        doc = cache.get(url)

        if doc is not None:
            print("Using cached file")
            continue 

        response_text = fetch_response_text(url, progress_writer=tqdm.write)
        cache.save(url, response_text)

    return urls 

if __name__ == "__main__":
    cache = Cache(R2CacheBackend())
    print(cache.get("https://www.basketball-reference.com/teams/NYK/1970.html"))


    
