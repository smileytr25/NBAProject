import pandas as pd
from src.hoophub.crawler.fetch import fetch_response_status_code, read_html
from src.hoophub.crawler.urls import draft_url
from src.hoophub.parsers.draft import parse_draft
from src.hoophub.repository.save import save_to_db
from src.hoophub.repository.query import query_last_year_in_table, query_existing_years_in_table

def get_year_draft_results(year, page_limit):
    return parse_draft(
        read_html(draft_url(year), page_limit=page_limit, attrs={"id" : "stats"})[0]
    )

def check_for_drafts_to_scrape(page_limit):
    last_draft_in_db = int(query_last_year_in_table("draft_history", "Year", 2026))
    start_of_new_years = next_year_to_check = int(last_draft_in_db) + 1

    while True:
        if fetch_response_status_code(draft_url(next_year_to_check), page_limit=page_limit) != 200:
            break
        next_year_to_check += 1

    return list(range(start_of_new_years, next_year_to_check))

def get_drafts_not_already_existing(years):
    years_existing = query_existing_years_in_table("draft_history", "Year")
    return [year for year in years if year not in years_existing]
        
def get_selected_years_draft_results(years, page_limit):
    drafts = []
    for year in years:
        year_df = get_year_draft_results(year, page_limit)
        drafts.append(year_df)
        print(f"Draft history added for year: {year}")
    return pd.concat(drafts, axis=0, ignore_index=True) if drafts else pd.DataFrame()

def run(years, page_limit):
    years = get_drafts_not_already_existing(years)
    new_years = check_for_drafts_to_scrape(page_limit)
    years = list(set(years + new_years))

    if years:
        print(f"Getting draft history for years: {', '.join([str(i) for i in years])}")
        df = get_selected_years_draft_results(years, page_limit)
        save_to_db(df, "draft_history", if_exists="append")
    else:
        print("All years are accounted for.")
