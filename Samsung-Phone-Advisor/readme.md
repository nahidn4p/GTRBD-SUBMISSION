# Samsung Phone Advisor

A FastAPI-based application that scrapes Samsung phone specifications from GSMArena, stores them in a PostgreSQL database, and provides an API to answer user queries about phone comparisons or specifications. The system uses a regex-based data extractor and a review generator to process natural-language questions like "Compare Samsung Galaxy M36 and F56" or "Best battery under $1000".

## Features
- **Web Scraping**: Extracts phone specs (model, release date, display, battery, camera, RAM, storage, price) from GSMArena.
- **Database Storage**: Stores data in a PostgreSQL database using SQLAlchemy.
- **API Endpoint**: Handles comparison queries, single phone details, or filtered searches (e.g., best battery).
- **Robust Parsing**: Handles complex GSMArena HTML, including camera details with multiple modules and price variations (e.g., €, ₹).
- **Comparison Logic**: Compares phones based on camera (main and secondary lenses), battery, display, price, and release date.

## System Architecture

graph TD
    A[User] -->|POST /ask| B(FastAPI Server)
    B -->|Parse Query| C[Data Extractor]
    C -->|Regex: M36, F56| D{Extracted Models}
    D -->|SQL Query| E[PostgreSQL<br>samsung_phone_advisor]
    E -->|Return Specs| F[Phone Data]
    F -->|Compare| G[Review Generator]
    G -->|Format Answer| H[JSON Response]
    I[Scraper<br>python app.py --scrape] -->|Fetch| J[GSMArena<br>List & Detail Pages]
    J -->|Parse & Store| E



## Tech Stack
- **Backend**: Python 3.8+, FastAPI, SQLAlchemy
- **Database**: PostgreSQL
- **Scraping**: BeautifulSoup, Requests
- **Regex**: For model extraction and spec parsing
- **Server**: Uvicorn


## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- PostgreSQL (e.g., version 13+)
- `pip` for installing Python dependencies

### Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/samsung-phone-advisor.git
   cd samsung-phone-advisor

2. **Install Dependencies**

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary beautifulsoup4 requests
or
pip install -r requirements.txt
```

3. **Setup Postgresql**
 - Create the database:
```bash
psql -U postgres -c "CREATE DATABASE samsung_phone_advisor;"
```
 - Update the database URL in app.py if needed (default: postgresql://postgres:mypass123@localhost/samsung_phone_advisor).

4. **Run the Scraper:**
 - Populate the database with Samsung phone data:
 ```bash
 python app.py --scrape
 ```
 - This scrapes up to 25 phones from https://www.gsmarena.com/samsung-phones-9.php and their detail pages.

5. **Start the FastAPI Server:**
 ```bash
 uvicorn app:app --reload
 ```
 - API available at http://127.0.0.1:8000.

##USAGE

### API Endpoint
- **Endpoint**: `POST /ask`
- **Request Body**:
  ```json
  {
    "question": "Compare Samsung Galaxy M36 and F56"
  }
- Example Request:

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"question": "Compare Samsung Galaxy M36 and F56"}'
```   
- Example Response:

```bash
{
  "answer": "Galaxy M36 vs Galaxy F56:\n- Main camera resolution is similar (50MP).\n- Galaxy M36 includes a macro lens, Galaxy F56 does not.\n- Battery performance is similar (5000mAh).\n- Galaxy F56 has a larger display (6.74″ vs 6.7″).\n- Galaxy M36 price is $13999, Galaxy F56 price is unavailable.\nOverall, Galaxy M36 is recommended as it is newer (Jun 2025 vs May 2025)."
}
```

### Supported Queries
- Comparison: "Compare Samsung Galaxy M36 and F56"
- Single Phone Specs: "Tell me about Samsung Galaxy M36"
- Filtered Search: "Best battery under $1000"

### Database Schema
The phones table has the following columns:

| Column       | Type    | Description                                                   |
| ------------ | ------- | ------------------------------------------------------------- |
| id           | Integer | Primary Key                                                   |
| model        | String  | Phone model (e.g., "Galaxy M36")                              |
| release_date | String  | Release date (e.g., "Jun 2025")                               |
| display      | String  | Display size (e.g., "6.7″ display")                           |
| battery      | String  | Battery capacity (e.g., "5000 mAh battery")                   |
| camera       | String  | Camera specs (e.g., "50 MP, f/1.8, (wide), PDAF, OIS, 8 MP…") |
| ram          | String  | RAM size (e.g., "8 GB RAM")                                   |
| storage      | String  | Storage capacity (e.g., "256 GB storage")                     |
| price        | Float   | Price (e.g., 13999.0)                                         |
| url          | String  | GSMArena detail page URL                                      |


## Flow Explanation    

    1. User Query: Sent via POST to /ask (e.g., "Compare Samsung Galaxy M36 and F56").
    2. Data Extractor: Uses regex (([A-Z]\d+(?:\s\w+)?)(?=\s+(?:and|or|vs)|$)) to extract model names.
    3. Database Query: Retrieves phone specs from PostgreSQL using SQLAlchemy.
    4. Review Generator: Compares specs (camera, battery, display, price) and generates a human-readable response.
    5. Scraper: Fetches data from GSMArena list and detail pages, storing in the database.


## Troubleshooting    

- Empty Camera/Price Fields:
    - Cause: Scraper failed to parse GSMArena detail pages (e.g., due to rate limiting).
    - Fix: Re-run the scraper to fetch missing data:
        ```bash
        python app.py --scrape
        ```
    - Manual Fix (e.g., for Galaxy F56 price):
        ```bash
        UPDATE phones SET price = 12999 WHERE model = 'Galaxy F56';
        ```
        Verify in DB
        ```bash
        psql -U postgres -d samsung_phone_advisor -c "SELECT model, camera, price FROM phones WHERE model ILIKE '%M36%' OR model ILIKE '%F56%';"
        ```    
- Rate Limiting by GSMArena:
    - Cause: GSMArena blocks frequent requests (HTTP 403).
    - Fix: Increase delay in scrape_samsung_phones:
        ```bash
        time.sleep(5)  # Increase to 10 if needed
        ```
        Alternatively, use a proxy or VPN.
