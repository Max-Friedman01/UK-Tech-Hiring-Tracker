import httpx
from bs4 import BeautifulSoup
from fetch import fetch

site = "https://en.wikipedia.org/wiki/Forbes_list_of_the_most_valuable_football_clubs"

response = fetch(site)

soup = BeautifulSoup(response.text, "html.parser")

table = soup.select_one("table.wikitable")
rows = {}
for i, tr in enumerate(table.select("tr")[1:], start=1):
    cells = [td.get_text(strip=True) for td in tr.select("td , th")]
    if len(cells) > 2:
        rows[i] = cells[2]
print(rows)

