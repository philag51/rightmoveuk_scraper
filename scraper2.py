# rightmove_scraper_extended.py
import time
import requests
from bs4 import BeautifulSoup
import json
from IPython.display import Image, display

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MyPropertyBot/1.0; +https://example.com/bot-info)"
}

def fetch(url, session=None, delay=1.0):
    sess = session or requests.Session()
    resp = sess.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    time.sleep(delay)
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
    soup = BeautifulSoup(html, "html.parser")
    data = {}

    # --- JSON-LD (structured if available) ---
    ld = parse_ld_json(soup)
    if ld:
        data["json_ld"] = ld

    # --- Basic ---
    title = soup.find("h1")
    if title: data["title"] = title.get_text(strip=True)

    address = soup.find("address")
    if address: data["address"] = address.get_text(strip=True)

    # --- Price ---
    for tag in soup.find_all(text=True):
        if "£" in tag:
            data["price"] = tag.strip()
            break

    # --- Property facts (property type, bedrooms, bathrooms, size, tenure) ---
    facts_section = soup.find_all("div")
    for div in facts_section:
        text = div.get_text(" ", strip=True)
        if "bedroom" in text.lower():
            data["bedrooms"] = text
        elif "bathroom" in text.lower():
            data["bathrooms"] = text
        elif "sq ft" in text.lower() or "sq m" in text.lower():
            data["size"] = text
        elif "freehold" in text.lower() or "leasehold" in text.lower():
            data["tenure"] = text
        elif "house" in text.lower() or "flat" in text.lower() or "apartment" in text.lower():
            data["property_type"] = text

    # --- Agent details ---
    agent_box = soup.find(string="Marketed by")
    if agent_box:
        parent = agent_box.find_parent()
        if parent:
            data["agent"] = parent.get_text(" ", strip=True)

    # --- Key information (council tax, parking, garden, accessibility) ---
    info_rows = soup.find_all("div")
    key_info = {}
    for div in info_rows:
        text = div.get_text(" ", strip=True)
        if "Council Tax" in text:
            key_info["council_tax"] = text
        if "Parking" in text:
            key_info["parking"] = text
        if "Garden" in text:
            key_info["garden"] = text
        if "Accessibility" in text:
            key_info["accessibility"] = text
    if key_info:
        data["key_info"] = key_info

    # --- Sale history ---
    sale_history = []
    sale_section = soup.find(id="propertyHistory")
    if sale_section:
        rows = sale_section.find_all("tr")
        for row in rows:
            cols = [c.get_text(" ", strip=True) for c in row.find_all("td")]
            if cols:
                sale_history.append(cols)
    if sale_history:
        data["sale_history"] = sale_history

    # --- Images ---
    images = [
        img.get("src") for img in soup.find_all("img")
        if img.get("src") and "rightmove" in img.get("src")
    ]
    if images:
        data["images"] = list(dict.fromkeys(images))

    return data

if __name__ == "__main__":
    url = "https://www.rightmove.co.uk/properties/166613036"
    html = fetch(url)
    data = parse_rightmove(html)

    # Print as JSON
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # Show images inline (Jupyter / IPython only)
    if "images" in data:
        for img_url in data["images"][:5]:
            display(Image(url=img_url))
