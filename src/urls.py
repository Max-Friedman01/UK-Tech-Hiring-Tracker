from urllib.parse import urlparse

def ensure_scheme(link: str) -> str:
    link = link.strip()
    if not urlparse(link).scheme:
        link = "https://" + link
    return link

def link_to_host(link: str) -> str:
    link = link.strip()
    if not urlparse(link).scheme:
        link = "https://" + link
    parsed_link = urlparse(link)
    return f"{parsed_link.scheme}://{parsed_link.netloc.lower()}"