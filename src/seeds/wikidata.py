"""Seed source: UK tech (and tech-adjacent finance) companies from Wikidata.

Builds a SPARQL query from the ID lists below, runs it against the Wikidata
Query Service, cleans the results and returns each company's website.

Selection rules:
  - matches at least one listed industry (P452) or type (P31)
  - country (P17) is the UK, or headquarters (P159) is in the UK
  - not dissolved (no P576)
  - has an official website (P856) and an English name
  - founded (P571) in or after TECH_CUTOFF if it matches any tech label,
    otherwise (finance-only) in or after FINANCE_CUTOFF;
    companies with no or unknown founding date are kept
"""

import json
from pathlib import Path

import httpx

from fetch import HEADERS, FetchError

from urls import ensure_scheme

ENDPOINT = "https://query.wikidata.org/sparql"
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
UK = "Q145"

TECH_CUTOFF = 1980
FINANCE_CUTOFF = 2000

TECH_INDUSTRIES = {
    "Q880371": "software industry",
    "Q638608": "software development",
    "Q11661": "information technology",
    "Q11016": "technology",
    "Q75": "Internet",
    "Q11660": "artificial intelligence",
    "Q19835007": "autonomous driving",
    "Q124102257": "cybersecurity industry",
    "Q189900": "information security",
    "Q870898": "computer security software",
    "Q3510521": "computer security",
    "Q2986369": "semiconductor industry",
    "Q941594": "video game industry",
    "Q1481411": "IT service management",
    "Q1540863": "information technology consulting",
    "Q2401742": "telecommunications industry",
    "Q484847": "e-commerce",
    "Q212930": "online shopping",
    "Q4382945": "online shop",
    "Q10932402": "food delivery",
    "Q16319025": "fintech",
    "Q4382277": "payment processing",
}

FINANCE_INDUSTRIES = {
    "Q837171": "financial services",
    "Q43015": "finance",
    "Q43183": "insurance",
    "Q806718": "economics of banking",
}

TECH_TYPES = {
    "Q18388277": "technology company",
    "Q620615": "mobile app",
    "Q1276157": "travel website",
    "Q4182287": "search engine",
}

FINANCE_TYPES = {
    "Q848507": "commercial bank",
    "Q60767305": "neobank",
    "Q39049085": "challenger bank",
}


def _values(ids) -> str:
    return " ".join(f"wd:{qid}" for qid in ids)


def build_query() -> str:
    all_industries = _values([*TECH_INDUSTRIES, *FINANCE_INDUSTRIES])
    all_types = _values([*TECH_TYPES, *FINANCE_TYPES])
    tech_industries = _values(TECH_INDUSTRIES)
    tech_types = _values(TECH_TYPES)

    return f"""
SELECT ?company (SAMPLE(?label) AS ?name) (SAMPLE(?website) AS ?site)
       (MIN(?inception) AS ?founded) (SAMPLE(?isTech) AS ?tech) WHERE {{
  {{
    VALUES ?industry {{ {all_industries} }}
    ?company wdt:P452 ?industry .
  }}
  UNION
  {{
    VALUES ?type {{ {all_types} }}
    ?company wdt:P31 ?type .
  }}

  {{ ?company wdt:P17 wd:{UK} . }}
  UNION
  {{ ?company wdt:P159/wdt:P17 wd:{UK} . }}

  FILTER NOT EXISTS {{ ?company wdt:P576 ?dissolved . }}

  ?company wdt:P856 ?website .
  ?company rdfs:label ?label .
  FILTER(LANG(?label) = "en")

  BIND(
    EXISTS {{ VALUES ?ti {{ {tech_industries} }} ?company wdt:P452 ?ti . }}
    || EXISTS {{ VALUES ?tt {{ {tech_types} }} ?company wdt:P31 ?tt . }}
    AS ?isTech
  )

  OPTIONAL {{ ?company wdt:P571 ?inception . }}
  FILTER(!BOUND(?inception) || isIRI(?inception)
         || YEAR(?inception) >= IF(?isTech, {TECH_CUTOFF}, {FINANCE_CUTOFF}))
}}
GROUP BY ?company
"""


def run_query(query: str, timeout: float = 120.0) -> list[dict]:
    """Send the query and return the raw result rows ('bindings')."""
    headers = {**HEADERS, "Accept": "application/sparql-results+json"}
    try:
        with httpx.Client(headers=headers, timeout=timeout) as client:
            response = client.post(ENDPOINT, data={"query": query})
            response.raise_for_status()
            return response.json()["results"]["bindings"]
    except httpx.HTTPStatusError as e:
        raise FetchError(f"Wikidata query failed with status {e.response.status_code}") from e
    except httpx.RequestError as e:
        raise FetchError(f"Wikidata query got no response: {e}") from e
    except (ValueError, KeyError) as e:
        raise FetchError(f"Wikidata returned an unexpected response: {e}") from e


def _value(row: dict, key: str) -> str | None:
    return row.get(key, {}).get("value")


def _year(value: str | None) -> int | None:
    """'1993-12-17T00:00:00Z' -> 1993; unknown-value links or missing -> None."""
    if value and value[:4].isdigit():
        return int(value[:4])
    return None


def parse_rows(rows: list[dict]) -> list[dict]:
    companies = {}
    for row in rows:
        qid = _value(row, "company").rsplit("/", 1)[-1]
        name = (_value(row, "name") or "").strip()
        website = (_value(row, "site") or "").strip()

        if not name or not website or name.lower().startswith("list of"):
            continue

        companies[qid] = {
            "qid": qid,
            "name": name,
            "website": ensure_scheme(website),
            "founded": _year(_value(row, "founded")),
            "is_tech": _value(row, "tech") == "true",
        }
    return sorted(companies.values(), key=lambda c: c["name"].lower())


def fetch_companies() -> list[dict]:
    """Query Wikidata and return cleaned company records."""
    return parse_rows(run_query(build_query()))


def get_company_sites() -> list[str]:
    """Return the website of every selected company, without duplicates."""
    return list(dict.fromkeys(c["website"] for c in fetch_companies()))


def save_companies(companies: list[dict], path: Path = DATA_DIR / "wikidata_companies.json") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(companies, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    companies = fetch_companies()
    save_companies(companies)
    tech = sum(c["is_tech"] for c in companies)
    print(f"Saved {len(companies)} companies ({tech} tech, {len(companies) - tech} finance-only)")