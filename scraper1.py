# rightmove_scraper_display.py
import time
import requests
from bs4 import BeautifulSoup
import json
from IPython.display import Image, display

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MyPropertyBot/1.0; +https://example.com/bot-info)"
}

def fetch(url, session=None, delay=1.0):
    """Download a Rightmove property page politely."""
    sess = session or requests.Session()
    resp = sess.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    time.sleep(delay)  # polite delay
    return resp.text

def parse_ld_json(soup):
    """Try extracting JSON-LD structured data (preferred)."""
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string)
            if isinstance(data, dict) and data.get("@type") in ["House", "Apartment", "Product"]:
                return data
        except Exception:
            continue
    return None

def parse_rightmove(html):
    """Extract property details without relying on fragile classes."""
    soup = BeautifulSoup(html, "html.parser")

    # 1) JSON-LD first (best source if present)
    ld = parse_ld_json(soup)
    if ld:
        return ld

    # 2) Fallback to manual scraping
    data = {}

    # Title
    title_tag = soup.find("h1")
    if title_tag:
        data["title"] = title_tag.get_text(strip=True)

    # Address
    address_tag = soup.find("address")
    if address_tag:
        data["address"] = address_tag.get_text(strip=True)

    # Description
    desc_tag = soup.find(id="description")
    if desc_tag:
        data["description"] = desc_tag.get_text(separator="\n", strip=True)

    # Features (first <ul>)
    features = []
    feature_section = soup.find("ul")
    if feature_section:
        for li in feature_section.find_all("li"):
            text = li.get_text(strip=True)
            if text:
                features.append(text)
    if features:
        data["features"] = features

    # Price (search for £ in visible text)
    for tag in soup.find_all(text=True):
        if "£" in tag:
            data["price"] = tag.strip()
            break

    # Images (Rightmove hosted only)
    images = [
        img.get("src") for img in soup.find_all("img")
        if img.get("src") and "rightmove" in img.get("src")
    ]
    if images:
        data["images"] = list(dict.fromkeys(images))  # remove duplicates

    return data

if __name__ == "__main__":
    url = "" #Paste url of property listing here
    html = fetch(url)
    data = parse_rightmove(html)

    # Print structured JSON
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # Show images inline (works in Jupyter / IPython)
    if "images" in data:
        for img_url in data["images"]:
            display(Image(url=img_url))
