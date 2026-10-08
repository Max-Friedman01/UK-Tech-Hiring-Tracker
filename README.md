# Scraper Project

UK Tech Hiring Tracker

A Python data pipeline that discovers UK technology companies, crawls their websites to find their public job boards, and collects their open roles into a database every day, building a history of who is hiring, for what, and for how long.

It queries a knowledge graph (Wikidata) to build a list of companies, crawling company websites to discover which hiring platform each one uses, collecting job postings through a public API, and storing everything in SQLite in a way that tracks job posting statisitcs over time.
