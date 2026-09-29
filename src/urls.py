from urllib.parse import urlparse

def ensure_scheme(link: str) -> str:
    link = link.strip()
    if not urlparse(link).scheme:
        link = "https://" + link
    return link