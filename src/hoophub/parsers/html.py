from bs4 import BeautifulSoup, Comment 

def get_element_from_comment(soup, wrapper_id, element_type, element_id):
    wrapper = soup.find("div", id=wrapper_id)
    
    element_comment = wrapper.find(
        string=lambda text: isinstance(text, Comment)
        and f'id="{element_id}"' in text
    )

    element_soup = BeautifulSoup(element_comment, "html.parser")
    element = element_soup.find(element_type, id=element_id)

    return element 