import unicodedata 

def remove_accents(name):
    if name is None:
        return None

    normalized = unicodedata.normalize("NFKD", name)
    return "".join(
        char for char in normalized
        if not unicodedata.combining(char)
    )