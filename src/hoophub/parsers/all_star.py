from bs4 import BeautifulSoup, Comment
import pandas as pd 

def parse_all_star_rosters(html: str, year: int) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")
    wrapper = soup.find("div", id="all_all_star_game_rosters")

    if not wrapper:
        return []
    
    all_star_comment = wrapper.find(string=lambda text: isinstance(text, Comment)
                                    and 'id="div_all_star_game_rosters"' in text)
    
    all_star_soup = BeautifulSoup(all_star_comment, "html.parser")
    all_star_div = all_star_soup.find("div", id="div_all_star_game_rosters")

    all_star1 = all_star_div.find("div", id="all_star_game_rosters_1")
    all_star2 = all_star_div.find("div", id="all_star_game_rosters_2")
    all_star3 = all_star_div.find("div", id="all_star_game_rosters_3")

    all_stars = []

    if all_star1:
        for name in all_star1.find_all("p"):
            all_stars.append(name.find("a").text)

    if all_star2:
        for name in all_star2.find_all("p"):
            all_stars.append(name.find("a").text)

    if all_star3:
        for name in all_star3.find_all("p"):
            all_stars.append(name.find("a").text)
    
    if all_stars:
        all_star_df = pd.DataFrame({"Player" : all_stars})
        all_star_df["Year"] = year 

        return all_star_df 
    else:
        return pd.DataFrame() 
