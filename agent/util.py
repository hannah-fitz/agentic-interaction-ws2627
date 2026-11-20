from datetime import date as Date
from difflib import get_close_matches


CITY_ALIASES = {
    "muenchen": "muenchen",
    "munich": "muenchen",
    "ulm": "ulm",
}



def formatDate(date: str) -> str:

    parsed_date = Date.fromisoformat(date)

    if parsed_date.isoformat() != date:
        raise ValueError("Das Datum muss YYYY-MM-DD entsprechen.")

    return parsed_date





def normalize_city(city: str) -> str:
    normalized = city.strip().casefold()
    normalized = (
        normalized.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )

    if normalized in CITY_ALIASES:
        return CITY_ALIASES[normalized]

    # Short names need a lower cutoff to allow a single-character typo in "ulm".
    cutoff = 0.66 if len(normalized) <= 3 else 0.75
    matches = get_close_matches(normalized, CITY_ALIASES, n=2, cutoff=cutoff)
    matching_cities = {CITY_ALIASES[match] for match in matches}
    if len(matching_cities) == 1:
        return matching_cities.pop()

    return normalized