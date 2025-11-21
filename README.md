# Amazon Deals Scraper & API 🛒

A complete web scraping solution for tracking Amazon product deals with REST API. Built with Python, FastAPI, and PostgreSQL.

## 📋 Features

### ✅ Web Scraper
- Scrapes 12 data points: category, title, brand, price, original price, discount %, rating, reviews, product link, image, availability
- Respects robots.txt and rate limits (2-5s delays)
- Uses Playwright for JavaScript-rendered pages
- Saves to JSON and CSV formats

### ✅ Database
- PostgreSQL with SQLAlchemy ORM
- 4 tables: Products, Categories, PriceHistory, ScrapingSession
- Price tracking and history
- Data validation before insertion

### ✅ REST API (FastAPI)
- **GET /api/products** - List all products with pagination
- **GET /api/products/filter** - Filter by category, brand, price range, discount, rating
- **GET /api/best-deals** - Top discounted AND highly rated products ⭐
- **GET /api/categories** - List all categories
- OpenAPI documentation at `/docs`
- CORS enabled for frontend integration

### ✅ Optional Frontend
- Simple HTML/CSS/JavaScript interface
- Search and filter products visually
- Responsive design

---

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/AmariEyaa/amazon-deals-scraper.git
cd amazon-deals-scraper
```

### 2. Install Dependencies
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure Database
Create `.env` file:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/amazon_deals
```

Or use SQLite for testing:
```env
DATABASE_URL=sqlite:///./amazon_deals.db
```

### 4. Run Scraper
```bash
python scraper/amazon_scraper.py
```
Enter search term (e.g., "laptop") and max pages. Results saved to `data/` folder.

### 5. Start API Server
```bash
cd api
uvicorn main:app --reload
```
API available at: http://localhost:8000

### 6. View API Documentation
Open browser: http://localhost:8000/docs

---

## 📊 Sample Dataset

`data/sample_products.json` contains 50+ pre-scraped products with all required fields.

```json
{
  "product_id": "B08N5WRWNW",
  "title": "Lenovo IdeaPad Gaming 3...",
  "brand": "Lenovo",
  "price": 699.99,
  "original_price": 899.99,
  "discount_percent": 22.2,
  "rating": 4.5,
  "reviews": 1234,
  "category": "Electronics",
  "product_link": "https://amazon.com/...",
  "image_url": "https://m.media-amazon.com/...",
  "availability": "In Stock"
}
```

---

## 🔌 API Examples

### Get All Products (with pagination)
```bash
GET http://localhost:8000/api/products?skip=0&limit=20
```

### Filter Products
```bash
GET http://localhost:8000/api/products/filter?min_price=100&max_price=500&min_rating=4.0&category=Electronics
```

### Get Best Deals ⭐ (REQUIRED)
```bash
GET http://localhost:8000/api/best-deals?limit=10
```
Returns top products sorted by: `(discount_percent * 0.6) + (rating * 10)`

### Search by Category
```bash
GET http://localhost:8000/api/products/category/Electronics
```

---

## 📁 Project Structure

```
amazon-deals-scraper/
├── scraper/
│   ├── amazon_scraper.py      # Main scraper
│   └── scraper_to_db.py       # Database pipeline
├── database/
│   ├── models.py              # SQLAlchemy models
│   ├── crud.py                # Database operations
│   ├── connection.py          # DB connection
│   └── validator.py           # Data validation
├── api/
│   ├── main.py                # FastAPI app
│   ├── routes.py              # API endpoints
│   └── schemas.py             # Pydantic models
├── frontend/
│   └── index.html             # Optional UI
├── data/
│   └── sample_products.json   # Sample dataset
├── tests/
│   ├── test_scraper.py
│   └── test_ethical_scraping.py
├── postman_collection.json    # API examples
├── requirements.txt
└── README.md
```

---

## 🧪 Testing

### Test Scraper
```bash
python tests/test_scraper.py
```

### Test API
```bash
# Start API first
cd api
uvicorn main:app --reload

# In another terminal
python test_demo.py
```

### Use Postman Collection
Import `postman_collection.json` into Postman for pre-configured API requests.

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.12 |
| **Web Scraping** | Playwright, BeautifulSoup4 |
| **Database** | PostgreSQL 15 + SQLAlchemy 2.0 |
| **API Framework** | FastAPI 0.105 |
| **Data Processing** | Pandas, NumPy |
| **Logging** | Loguru |
| **Testing** | Pytest |

---

## ⚖️ Ethical Scraping

This project follows ethical web scraping practices:

✅ **Respects robots.txt** - Checks Amazon's robots.txt before scraping  
✅ **Rate limiting** - 2-5 second delays between requests  
✅ **User agent rotation** - Identifies as a bot  
✅ **No aggressive scraping** - Max 3 pages per session by default  
✅ **Error handling** - Exponential backoff on failures  
✅ **Educational purpose** - For learning and portfolio only  

⚠️ **Disclaimer**: This is for educational purposes. Always review and comply with Amazon's Terms of Service.

---

## 📝 API Documentation

### Swagger UI (Interactive)
http://localhost:8000/docs

### Postman Collection
Import `postman_collection.json` for example requests.



## 🚧 Known Limitations

- Amazon frequently updates their HTML structure (may require CSS selector updates)
- IP blocking possible with aggressive scraping (use proxies for production)
- Some products have missing data (handled gracefully with validation)

---

## 📄 License

MIT License - See LICENSE file

---

## 👤 Author

**Amari Eyaa**
- GitHub: [@AmariEyaa](https://github.com/AmariEyaa)

---

## 🙏 Acknowledgments

- FastAPI for excellent API framework
- Playwright for reliable browser automation
- SQLAlchemy for powerful ORM

---

**⭐ Star this repo if you find it useful!**
