import argparse
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as SQLAlchemySession
from models import Phone, get_session
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Samsung Phone Advisor")

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set. Please check your .env file.")

try:
    session_maker = get_session(DATABASE_URL)
except Exception as e:
    raise ValueError(f"Failed to initialize database connection: {e}")

BASE_URL = "https://www.gsmarena.com/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

class Query(BaseModel):
    question: str

def fetch_page(url, retries=5, delay=5):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            print(f"Fetched {url} successfully on attempt {attempt + 1}")
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}. Retrying ({attempt + 1}/{retries})...")
            time.sleep(delay)
    print(f"Failed to fetch {url} after {retries} attempts.")
    return None

def parse_title_specs(title):
    specs = {}
    try:
        if "Features " in title:
            features_part = title.split("Features ")[1]
        else:
            features_part = title
        parts = [p.strip() for p in features_part.split(",")]
        for part in parts:
            if "display" in part.lower():
                specs["display"] = part
            elif "chipset" in part.lower():
                specs["chipset"] = part
            elif "battery" in part.lower():
                specs["battery"] = part
            elif "storage" in part.lower():
                specs["storage"] = part
            elif "ram" in part.lower():
                specs["ram"] = part
        date_match = re.search(r"Announced ([A-Za-z]+ \d{4})", title)
        specs["release_date"] = date_match.group(1) if date_match else None
        specs["camera"] = None
        specs["price"] = None
        return specs
    except Exception as e:
        print(f"Error parsing title: {e}")
        return specs

def parse_detail_page(soup):
    specs = {}
    try:
        # Find all tables, fallback to all if specific classes not found
        tables = soup.find_all("table")  # Simplified, as HTML shows no specific class
        print(f"Found {len(tables)} tables on detail page: {soup.title.text if soup.title else 'No title'}")
        
        for table in tables:
            th = table.find("th")
            table_category = th.text.strip() if th else "Unknown"
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    key = cells[0].text.strip()
                    value = cells[1].text.strip()
                    print(f"  Table '{table_category}': Key='{key}' Value='{value[:50]}...'")
                    
                    # Camera extraction: check key or data-spec
                    if any(c_phrase.lower() in key.lower() for c_phrase in ["Main Camera", "Camera", "Primary camera", "Rear camera"]) or cells[1].get("data-spec") == "cam1modules":
                        specs["camera"] = value
                        print(f"    → Extracted camera: {value[:50]}...")
                    
                    # Price extraction: handle €, ₹, $, US$, and decimals
                    if "Price" in key.lower() or cells[1].get("data-spec") == "price":
                        price_match = re.search(r'(?:€|₹|US\$|\$)\s*([\d,]+(?:\.\d{1,2})?)', value)
                        specs["price"] = float(price_match.group(1).replace(',', '')) if price_match else None
                        print(f"    → Extracted price: {specs.get('price', 'None')}")
        
        return specs
    except Exception as e:
        print(f"Error parsing detail page: {e}")
        return specs
    

def parse_phone_from_link(a_tag):
    href = a_tag.get('href', '')
    if not href:
        return None
    url = urljoin(BASE_URL, href)
    
    model_span = a_tag.select_one("strong span")
    model = model_span.text.strip() if model_span else None
    
    if not model:
        return None
    
    specs = {"model": model}
    
    img = a_tag.find("img")
    if img and img.get("title"):
        specs.update(parse_title_specs(img['title']))
    
    detail_soup = fetch_page(url)
    if detail_soup:
        specs.update(parse_detail_page(detail_soup))
    
    specs["url"] = url
    return specs

def scrape_samsung_phones(limit=25):
    soup = fetch_page("https://www.gsmarena.com/samsung-phones-9.php")
    if not soup:
        print("Failed to fetch GSMArena page.")
        return
    
    makers_div = soup.select_one("div.makers")
    if not makers_div:
        print("No makers div found.")
        return
    
    links = makers_div.find_all("a", href=True)
    session = session_maker()
    
    for i, a_tag in enumerate(links[:limit]):
        if 'galaxy' not in a_tag.get('href', '').lower():
            continue
        phone_model = a_tag.select_one("strong span").text.strip() if a_tag.select_one("strong span") else "Unknown"
        print(f"Processing {i+1}/{len(links[:limit])}: {phone_model}")
        
        phone_specs = parse_phone_from_link(a_tag)  # Assuming parse_phone_from_link was a typo
        if phone_specs and phone_specs.get("model"):
            existing = session.query(Phone).filter_by(model=phone_specs["model"]).first()
            if existing:
                for key, value in phone_specs.items():
                    if key in ["release_date", "display", "battery", "camera", "ram", "storage"] and value:
                        setattr(existing, key, value)
                if phone_specs.get("price") is not None:  # Explicit None check
                    existing.price = phone_specs["price"]
            else:
                new_phone = Phone(**{k: v for k, v in phone_specs.items() if k in Phone.__table__.columns.keys()})
                session.add(new_phone)
            try:
                session.commit()
                print(f"Saved/Updated {phone_specs['model']} - Camera: {phone_specs.get('camera', 'None')}, Price: {phone_specs.get('price', 'None')}")
            except Exception as e:
                print(f"Error saving {phone_specs['model']}: {e}")
                session.rollback()
        time.sleep(5)  # Increased delay
    
    session.close()

# Agent 1: Data Extractor (RAG-like retrieval)
def data_extractor(question: str, session: SQLAlchemySession):
    # Extract model names (e.g., "M36", "F56", "S25 FE")
    models = re.findall(r'(?:Samsung\s)?(?:Galaxy\s)?([A-Z]\d+(?:\s\w+)?)(?=\s+(?:and|or|vs)|$)', question, re.IGNORECASE)
    models = [m.strip() for m in models if m.strip()]
    
    print(f"Extracted models from query: {models}")
    
    if not models:
        print("No models extracted. Returning empty result.")
        return []
    
    phones = []
    for model in models:
        # Construct possible model variations
        full_model = f"Galaxy {model}" if not model.startswith("Galaxy") else model
        short_model = model.replace("Galaxy ", "") if model.startswith("Galaxy ") else model
        print(f"Searching for model: full='{full_model}', short='{short_model}'")
        
        # Query database with flexible matching
        phone = (session.query(Phone)
                 .filter(Phone.model.ilike(f"%{full_model}%") | Phone.model.ilike(f"%{short_model}%"))
                 .first())
        if phone:
            phones.append({
                "model": phone.model,
                "release_date": phone.release_date,
                "display": phone.display,
                "battery": phone.battery,
                "camera": phone.camera if phone.camera else "Unknown",
                "ram": phone.ram,
                "storage": phone.storage,
                "price": phone.price if phone.price is not None else "Unknown"
            })
            print(f"Found phone: {phone.model}")
        else:
            print(f"No match for model: full='{full_model}', short='{short_model}'")
    
    if len(phones) < 2 and "compare" in question.lower():
        print("Less than 2 phones found. Attempting broader search.")
        # Broader search for any relevant models
        all_phones = session.query(Phone).all()
        for term in models:
            if len(phones) >= 2:
                break
            phone = session.query(Phone).filter(Phone.model.ilike(f"%{term}%")).first()
            if phone and phone.model not in [p["model"] for p in phones]:
                phones.append({
                    "model": phone.model,
                    "release_date": phone.release_date,
                    "display": phone.display,
                    "battery": phone.battery,
                    "camera": phone.camera if phone.camera else "Unknown",
                    "ram": phone.ram,
                    "storage": phone.storage,
                    "price": phone.price if phone.price is not None else "Unknown"
                })
                print(f"Broad search found: {phone.model}")
    
    return phones

# Agent 2: Review Generator
def review_generator(phones, question: str):
    if not phones:
        return "No data available for the requested phones."
    
    if "compare" in question.lower():
        if len(phones) < 2:
            return "Please specify two phones for comparison."
        p1, p2 = phones[0], phones[1]
        comparison = f"{p1['model']} vs {p2['model']}:\n"
        
        # Camera comparison
        if p1['camera'] != "Unknown" and p2['camera'] != "Unknown":
            # Clean newlines and extract main camera MP
            mp1 = int(re.search(r'(\d+)\s*MP', p1['camera'].replace('\r\n', ' ')).group(1)) if re.search(r'(\d+)\s*MP', p1['camera'].replace('\r\n', ' ')) else 0
            mp2 = int(re.search(r'(\d+)\s*MP', p2['camera'].replace('\r\n', ' ')).group(1)) if re.search(r'(\d+)\s*MP', p2['camera'].replace('\r\n', ' ')) else 0
            if mp1 > mp2:
                comparison += f"- {p1['model']} has a better main camera ({mp1}MP vs {mp2}MP).\n"
            elif mp2 > mp1:
                comparison += f"- {p2['model']} has a better main camera ({mp2}MP vs {mp1}MP).\n"
            else:
                comparison += f"- Main camera resolution is similar ({mp1}MP).\n"
            
            # Check for secondary cameras
            has_macro1 = 'macro' in p1['camera'].lower()
            has_macro2 = 'macro' in p2['camera'].lower()
            if has_macro1 and not has_macro2:
                comparison += f"- {p1['model']} includes a macro lens, {p2['model']} does not.\n"
            elif has_macro2 and not has_macro1:
                comparison += f"- {p2['model']} includes a macro lens, {p1['model']} does not.\n"
        else:
            comparison += f"- Camera details unavailable for comparison.\n"
        
        # Battery comparison
        if p1['battery'] and p2['battery']:
            mah1 = int(re.search(r'(\d+)\s*mAh', p1['battery']).group(1)) if re.search(r'(\d+)\s*mAh', p1['battery']) else 0
            mah2 = int(re.search(r'(\d+)\s*mAh', p2['battery']).group(1)) if re.search(r'(\d+)\s*mAh', p2['battery']) else 0
            if mah1 > mah2:
                comparison += f"- {p1['model']} has better battery life ({mah1}mAh vs {mah2}mAh).\n"
            elif mah2 > mah1:
                comparison += f"- {p2['model']} has better battery life ({mah2}mAh vs {mah1}mAh).\n"
            else:
                comparison += f"- Battery performance is similar ({mah1}mAh).\n"
        
        # Display comparison
        if p1['display'] and p2['display']:
            size1 = float(re.search(r'(\d+\.?\d?)″', p1['display']).group(1)) if re.search(r'(\d+\.?\d?)″', p1['display']) else 0
            size2 = float(re.search(r'(\d+\.?\d?)″', p2['display']).group(1)) if re.search(r'(\d+\.?\d?)″', p2['display']) else 0
            if size1 > size2:
                comparison += f"- {p1['model']} has a larger display ({size1}″ vs {size2}″).\n"
            elif size2 > size1:
                comparison += f"- {p2['model']} has a larger display ({size2}″ vs {size1}″).\n"
            else:
                comparison += f"- Display size is similar ({size1}″).\n"
        
        # Price comparison
        if p1['price'] != "Unknown" and p2['price'] != "Unknown":
            if p1['price'] < p2['price']:
                comparison += f"- {p1['model']} is more affordable (${p1['price']} vs ${p2['price']}).\n"
            elif p2['price'] < p1['price']:
                comparison += f"- {p2['model']} is more affordable (${p2['price']} vs ${p1['price']}).\n"
            else:
                comparison += f"- Prices are similar (${p1['price']}).\n"
        elif p1['price'] != "Unknown":
            comparison += f"- {p1['model']} price is ${p1['price']}, {p2['model']} price is unavailable.\n"
        elif p2['price'] != "Unknown":
            comparison += f"- {p2['model']} price is ${p2['price']}, {p1['model']} price is unavailable.\n"
        else:
            comparison += f"- Price details unavailable for comparison.\n"
        
        # Recommendation based on release date
        if p1['release_date'] and p2['release_date']:
            from datetime import datetime
            try:
                date1 = datetime.strptime(p1['release_date'], "%b %Y")
                date2 = datetime.strptime(p2['release_date'], "%b %Y")
                if date1 > date2:
                    comparison += f"Overall, {p1['model']} is recommended as it is newer ({p1['release_date']} vs {p2['release_date']})."
                else:
                    comparison += f"Overall, {p2['model']} is recommended as it is newer ({p2['release_date']} vs {p1['release_date']})."
            except ValueError:
                comparison += f"Overall, both models are comparable."
        else:
            comparison += f"Overall, both models are comparable."
        
        return comparison
    elif "best battery under $1000" in question.lower():
        under_1000 = [p for p in phones if p['price'] != "Unknown" and p['price'] < 1000]
        if under_1000:
            best = max(under_1000, key=lambda p: int(re.search(r'(\d+)\s*mAh', p['battery']).group(1)) if re.search(r'(\d+)\s*mAh', p['battery']) else 0)
            return f"The {best['model']} has the best battery ({best['battery']}) under $1000."
        return "No phones under $1000 found or price data unavailable."
    else:
        if not phones:
            return "No phone data available."
        p = phones[0]
        return f"{p['model']} specs: Display: {p['display']}, Battery: {p['battery']}, Camera: {p['camera']}, RAM: {p['ram']}, Storage: {p['storage']}, Price: ${p['price']}, Released: {p['release_date']}."    
# Unified Response
def compose_response(question: str):
    session = session_maker()  # Correctly instantiate a new session
    try:
        phones = data_extractor(question, session)
        answer = review_generator(phones, question)
    finally:
        session.close()
    return {"answer": answer}

@app.post("/ask")
async def ask(query: Query):
    if not query.question:
        raise HTTPException(status_code=400, detail="Question is required.")
    return compose_response(query.question)

@app.get("/")
async def root():
    return {"message": "Samsung Phone Advisor is running. Use /ask endpoint."}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scrape", action="store_true", help="Run scraper to populate DB")
    args = parser.parse_args()
    if args.scrape:
        print("Scraping Samsung phones...")
        scrape_samsung_phones(limit=25)
    else:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)