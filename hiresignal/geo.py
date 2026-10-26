"""Location normalisation: free-text location -> (city, country, region, work mode)."""
from __future__ import annotations

import re

# city pattern -> (canonical city, country)
CITIES = [
    (r"san francisco|\bsf\b|bay area|palo alto|mountain view|menlo park|sunnyvale|san jose|"
     r"oakland|berkeley|redwood city|san mateo|cupertino|santa clara|south san francisco|emeryville",
     "SF Bay Area", "United States"),
    (r"new york|\bnyc\b|brooklyn|manhattan", "New York", "United States"),
    (r"seattle|bellevue|redmond|kirkland", "Seattle", "United States"),
    (r"boston|cambridge,? ma|somerville", "Boston", "United States"),
    (r"los angeles|\bla\b,? ca|santa monica|pasadena|culver city|irvine", "Los Angeles", "United States"),
    (r"austin", "Austin", "United States"), (r"chicago", "Chicago", "United States"),
    (r"denver|boulder", "Denver/Boulder", "United States"),
    (r"washington,? d\.?c|\bdc\b|arlington,? va|reston", "Washington DC", "United States"),
    (r"atlanta", "Atlanta", "United States"), (r"san diego", "San Diego", "United States"),
    (r"portland", "Portland", "United States"), (r"miami", "Miami", "United States"),
    (r"philadelphia", "Philadelphia", "United States"), (r"pittsburgh", "Pittsburgh", "United States"),
    (r"salt lake|lehi|provo", "Salt Lake City", "United States"), (r"dallas|houston", "Texas (Dallas/Houston)", "United States"),
    (r"minneapolis", "Minneapolis", "United States"), (r"raleigh|durham|research triangle", "Raleigh-Durham", "United States"),
    (r"phoenix|scottsdale", "Phoenix", "United States"), (r"nashville", "Nashville", "United States"),
    (r"toronto", "Toronto", "Canada"), (r"vancouver", "Vancouver", "Canada"),
    (r"montr[eé]al", "Montreal", "Canada"), (r"waterloo", "Waterloo", "Canada"), (r"ottawa", "Ottawa", "Canada"),
    (r"london", "London", "United Kingdom"), (r"manchester", "Manchester", "United Kingdom"),
    (r"edinburgh", "Edinburgh", "United Kingdom"), (r"cambridge,? uk|oxford", "Cambridge/Oxford", "United Kingdom"),
    (r"berlin", "Berlin", "Germany"), (r"m[uü]nchen|munich", "Munich", "Germany"),
    (r"hamburg", "Hamburg", "Germany"), (r"frankfurt", "Frankfurt", "Germany"),
    (r"k[oö]ln|cologne", "Cologne", "Germany"), (r"d[uü]sseldorf", "Düsseldorf", "Germany"),
    (r"stuttgart", "Stuttgart", "Germany"), (r"leipzig", "Leipzig", "Germany"),
    (r"n[uü]rnberg|nuremberg", "Nuremberg", "Germany"), (r"hannover|hanover", "Hanover", "Germany"),
    (r"karlsruhe", "Karlsruhe", "Germany"), (r"dresden", "Dresden", "Germany"), (r"bonn", "Bonn", "Germany"),
    (r"amsterdam", "Amsterdam", "Netherlands"), (r"rotterdam|utrecht|eindhoven|the hague", "Netherlands (other)", "Netherlands"),
    (r"paris", "Paris", "France"), (r"zurich|z[uü]rich", "Zurich", "Switzerland"), (r"geneva|gen[eè]ve|basel|lausanne", "Switzerland (other)", "Switzerland"),
    (r"stockholm", "Stockholm", "Sweden"), (r"copenhagen", "Copenhagen", "Denmark"), (r"oslo", "Oslo", "Norway"),
    (r"helsinki", "Helsinki", "Finland"), (r"dublin", "Dublin", "Ireland"), (r"lisbon|porto", "Lisbon/Porto", "Portugal"),
    (r"barcelona", "Barcelona", "Spain"), (r"madrid", "Madrid", "Spain"), (r"vienna|wien", "Vienna", "Austria"),
    (r"warsaw|krak[oó]w|wroc[lł]aw", "Poland (cities)", "Poland"), (r"prague", "Prague", "Czechia"),
    (r"tallinn", "Tallinn", "Estonia"), (r"milan|rome", "Italy (cities)", "Italy"), (r"brussels", "Brussels", "Belgium"),
    (r"tel aviv", "Tel Aviv", "Israel"), (r"dubai|abu dhabi", "UAE", "United Arab Emirates"),
    (r"bangalore|bengaluru", "Bengaluru", "India"), (r"mumbai|navi mumbai|thane", "Mumbai", "India"),
    (r"pune", "Pune", "India"), (r"hyderabad", "Hyderabad", "India"),
    (r"new delhi|delhi|gurgaon|gurugram|noida|\bncr\b", "Delhi NCR", "India"),
    (r"chennai", "Chennai", "India"), (r"kolkata", "Kolkata", "India"), (r"ahmedabad", "Ahmedabad", "India"),
    (r"singapore", "Singapore", "Singapore"), (r"tokyo", "Tokyo", "Japan"), (r"seoul", "Seoul", "South Korea"),
    (r"sydney", "Sydney", "Australia"), (r"melbourne", "Melbourne", "Australia"), (r"auckland", "Auckland", "New Zealand"),
    (r"s[aã]o paulo", "São Paulo", "Brazil"), (r"mexico city|ciudad de m[eé]xico", "Mexico City", "Mexico"),
    (r"buenos aires", "Buenos Aires", "Argentina"), (r"lagos", "Lagos", "Nigeria"), (r"nairobi", "Nairobi", "Kenya"),
]
CITIES = [(re.compile(p, re.I), c, k) for p, c, k in CITIES]

COUNTRIES = [
    (r"\bu\.?s\.?a?\.?\b|united states|\bus[\s\-]based\b|\bus only\b|\bus/canada\b", "United States"),
    (r"\bu\.?k\.?\b|united kingdom|england|scotland|\bwales\b", "United Kingdom"),
    (r"germany|deutschland", "Germany"), (r"canada", "Canada"), (r"netherlands|holland", "Netherlands"),
    (r"france", "France"), (r"spain|espa[nñ]a", "Spain"), (r"portugal", "Portugal"), (r"ireland", "Ireland"),
    (r"switzerland", "Switzerland"), (r"austria|[oö]sterreich", "Austria"), (r"poland", "Poland"),
    (r"sweden", "Sweden"), (r"denmark", "Denmark"), (r"norway", "Norway"), (r"finland", "Finland"),
    (r"italy", "Italy"), (r"belgium", "Belgium"), (r"czech", "Czechia"), (r"romania", "Romania"),
    (r"greece", "Greece"), (r"estonia", "Estonia"), (r"ukraine", "Ukraine"), (r"israel", "Israel"),
    (r"india", "India"), (r"singapore", "Singapore"), (r"japan", "Japan"), (r"australia", "Australia"),
    (r"new zealand", "New Zealand"), (r"brazil|brasil", "Brazil"), (r"mexico", "Mexico"),
    (r"argentina", "Argentina"), (r"colombia", "Colombia"), (r"philippines", "Philippines"),
    (r"south africa", "South Africa"), (r"nigeria", "Nigeria"), (r"kenya", "Kenya"), (r"pakistan", "Pakistan"),
    (r"united arab emirates|\buae\b", "United Arab Emirates"),
]
COUNTRIES = [(re.compile(p, re.I), c) for p, c in COUNTRIES]

US_STATES = re.compile(
    r",\s*(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|"
    r"NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b")
US_STATE_NAMES = re.compile(
    r"\b(california|texas|florida|colorado|massachusetts|washington state|oregon|georgia|illinois|"
    r"virginia|north carolina|utah|arizona|michigan|ohio|pennsylvania|new jersey|minnesota)\b", re.I)

REGION = {
    "United States": "North America", "Canada": "North America", "Mexico": "Latin America",
    "Brazil": "Latin America", "Argentina": "Latin America", "Colombia": "Latin America",
    "India": "Asia", "Singapore": "Asia", "Japan": "Asia", "South Korea": "Asia", "Philippines": "Asia",
    "Pakistan": "Asia", "Israel": "Middle East", "United Arab Emirates": "Middle East",
    "Australia": "Oceania", "New Zealand": "Oceania", "South Africa": "Africa", "Nigeria": "Africa", "Kenya": "Africa",
}

GLOBAL = re.compile(r"worldwide|anywhere|global|\bremote\s*$|all countries|any location", re.I)
EUROPE_WIDE = re.compile(r"\beurope\b|\beu\b|\bemea\b|\bcet\b", re.I)
REMOTE = re.compile(r"remote|work from home|\bwfh\b|distributed|home[\s\-]?office", re.I)
HYBRID = re.compile(r"hybrid|flexible office|\d\s?days?\s?(?:/|a|per)\s?week in", re.I)
ONSITE = re.compile(r"on[\s\-]?site|in[\s\-]office|in[\s\-]person|\boffice\b", re.I)


def work_mode(text: str, remote_flag=None) -> str:
    t = text or ""
    if HYBRID.search(t):
        return "Hybrid"
    if remote_flag is True or REMOTE.search(t):
        return "Remote"
    if ONSITE.search(t) or remote_flag is False:
        return "Onsite"
    return "Unspecified"


def normalise(location: str | None) -> dict:
    """Return city, country and region for a free-text location."""
    loc = (location or "").strip()
    out = {"city": None, "country": None, "region": None}
    if not loc:
        return out
    for rg, city, country in CITIES:
        if rg.search(loc):
            out.update(city=city, country=country)
            break
    if not out["country"]:
        if US_STATES.search(loc) or US_STATE_NAMES.search(loc):
            out["country"] = "United States"
        else:
            for rg, country in COUNTRIES:
                if rg.search(loc):
                    out["country"] = country
                    break
    if out["country"]:
        out["region"] = REGION.get(out["country"], "Europe")
    elif EUROPE_WIDE.search(loc):
        out["region"] = "Europe"
    elif GLOBAL.search(loc):
        out["region"] = "Global / Anywhere"
    return out
