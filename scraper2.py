# rightmove_property.py
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

class Property:
    """Represents a Rightmove property listing."""
    
    def __init__(self, url):
        self.url = url
        self.html = fetch(url)
        self.soup = BeautifulSoup(self.html, "html.parser")
        self.data = self._parse()
    
    def _parse(self):
        """Extract property details into a dictionary."""
        # Try JSON-LD first
        ld = parse_ld_json(self.soup)
        if ld:
            return ld
        
        # Fallback scrape
        data = {}

        # Title
        title_tag = self.soup.find("h1")
        if title_tag:
            data["title"] = title_tag.get_text(strip=True)

        # Address
        address_tag = self.soup.find("address")
        if address_tag:
            data["address"] = address_tag.get_text(strip=True)

        # Description
        desc_tag = self.soup.find(id="description")
        if desc_tag:
            data["description"] = desc_tag.get_text(separator="\n", strip=True)

        # Features
        features = []
        feature_section = self.soup.find("ul")
        if feature_section:
            for li in feature_section.find_all("li"):
                text = li.get_text(strip=True)
                if text:
                    features.append(text)
        if features:
            data["features"] = features

        # Price
        for tag in self.soup.find_all(string=True):
            if "£" in tag:
                data["price"] = tag.strip()
                break

        # Images
        images = [
            img.get("src") for img in self.soup.find_all("img")
            if img.get("src") and "rightmove" in img.get("src")
        ]
        if images:
            data["images"] = list(dict.fromkeys(images))  # remove duplicates

        return data
    
    def to_dict(self):
        """Return property data as dict."""
        return self.data
    
    def to_json(self, indent=2):
        """Return property data as JSON string."""
        return json.dumps(self.data, indent=indent, ensure_ascii=False)
    
    def show_images(self, limit=5):
        """Display property images inline (Jupyter/IPython only)."""
        if "images" in self.data:
            for img_url in self.data["images"][:limit]:
                display(Image(url=img_url))

if __name__ == "__main__":
    url = "" #Paste url of property listing here
    prop = Property(url)

    # Print JSON
    print(prop.to_json())

    # Show images
    prop.show_images()
