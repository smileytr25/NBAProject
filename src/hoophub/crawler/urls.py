base_url = "https://www.basketball-reference.com"
leagues_base_url = base_url + "/leagues"

def get_league(year: int):
    return "NBA" if year >= 1950 else "BAA"

def league_page_subsection_url(year: int, subsection_name: str):
    return leagues_base_url + f"/{get_league(year)}_{year}.html#all_{subsection_name}"

def coaches_url(year: int):
    return leagues_base_url + f"/{get_league(year)}_{year}_coaches.html"

def draft_url(year: int):
    return base_url + f"/draft/{get_league(year)}_{year}.html"

def all_teams_url():
    return base_url + "/teams/"

def player_stats_url(year: int, stat_type: str):
    return leagues_base_url + f"/{get_league(year)}_{year}_{stat_type}.html"

def schedule_url(year: int, month: str):
    return leagues_base_url + f"/{get_league(year)}_{year}_games-{month}.html"

def standings_url(year: str):
    return leagues_base_url + f"/{get_league(year)}_{year}_standings.html"