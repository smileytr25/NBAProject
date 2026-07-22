from bs4 import BeautifulSoup, Comment 
import bs4 
def get_element_from_comment(soup: BeautifulSoup, wrapper_id: str, element_type: str, element_id: str) -> bs4.element.Tag | None:
    wrapper = soup.find("div", id=wrapper_id)
    
    element_comment = wrapper.find(
        string=lambda text: isinstance(text, Comment)
        and f'id="{element_id}"' in text
    )

    element_soup = BeautifulSoup(element_comment, "html.parser")
    element = element_soup.find(element_type, id=element_id)

    return element 
