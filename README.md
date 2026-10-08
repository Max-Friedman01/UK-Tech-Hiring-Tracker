# Scraper Project

UK Tech Hiring Tracker

A Python data pipeline that discovers UK technology companies, crawls their websites to find their public job boards, and collects their open roles into a database every day, building a history of who is hiring, for what, and for how long.

It queries a knowledge graph (Wikidata) to build a list of companies, crawling company websites to discover which hiring platform each one uses, collecting job postings through a public API, and storing everything in SQLite in a way that tracks job posting statisitcs over time.

## How it works

### 1. Wikidata Query

`wikidata.py` builds a query of all companies that meet certain wikidata industry/type IDs, such as software, fintech and cybersecurity, then runs this against the Wikidata query service. It filters for companies that have some location/office/headquarters in the UK, have a known name, a website and have not been dissolved.

It also filters for companies founded in/after the 1980s, and finance companies in/after the 2000s, to filter out centuries established firms and established banks - both of which, if they still exist, are unlikely to be putting job postings on less established sites with an open API.

It is key to understand that the sott of companies that hire on sites such as Greenhouse are more likely to be companies that are not massive, very well-established household names.

### 2. Careers page crawler

A crawler visits the company home page, and crawls from there, trying to find a job board link. For each company, it:

- tries common careers paths (`/careers`, `/jobs`, `/join-us`, `/vacancies`, `/en-gb/careers` and others), then careers subdomains (`careers.`, `jobs.`, `work.`);
- checks every fetched page for Greenhouse board references, both in links and in the **raw page text**, which catches boards embedded in scripts or in JSON data rendered by JavaScript;
- follows links in each page's main content breadth-first, level by level, up to a depth limit;
- shares a page budget and visited set across all of a company's candidate URLs, so no page is fetched twice.

This is all done with strict adherence to what is directed in each site's robots.txt

The key output is the job board id for the company, if one exists - e.g. NaturalMotions's id on Greenhouse is `nmcareers`.

### 3. Verification and Collection

After this, the job board ids can be verified, and once it passes this, some relevant information for the company can be pulled.

`collect.py` takes each company's board id, and for the relevant job board, pulls all job listings from that company, and collects all its details:

- platform
- job id
- board id
- title
- location
- departments
- offices
- url
- updated_at
- first published
- content (description)
- first seen
- last seen

These are then stored in an SQL database.

### 4. Analysis

`analysis.py` takes all these jobs and creates some statistics that may be relevant to someone looking to apply to jobs, such as:

- Jobs by company
- Jobs by department
- Job locations
- Job seniority
- Most relevant skills

This is all compiled in a report.

`word_frequency.py` can also look at the relative frequency of a given word in the raw text of the job postings.

## Results so far

| Stage                                        | Result         |
| -------------------------------------------- | -------------- |
| Companies from Wikidata                      | ~1,100         |
| Boards found by the first full crawl         | 18 (17 unique) |
| Verified boards collected                    | 16             |
| Jobs in the database                         | 3,800+         |
| Crawler accuracy on the known-board test set | 10 / 12        |

Several discovered board IDs do not match their company names (`payhawkio`, `tandemmoneylimited`, `nmcareers`, `wirelesslogic`), which a simple name-guessing approach would have missed. This is the main contribution of the crawler over guessing.

## Tech stack

Python, httpx, BeautifulSoup, tldextract, SQLite, SPARQL (Wikidata), Greenhouse Job Board API.
