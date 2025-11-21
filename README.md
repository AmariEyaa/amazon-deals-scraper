# Amazon Deals Scraper & API

A comprehensive web scraping and API solution for tracking Amazon product deals, prices, and ratings.

## 🚀 Features

- **Web Scraper**: Extract product data from Amazon (title, brand, price, discounts, ratings, reviews)
- **Database Storage**: Store structured data in PostgreSQL/MongoDB
- **REST API**: Query and filter products with advanced search capabilities
- **Best Deals Endpoint**: Get top discounted and highly-rated products
- **Pagination & Sorting**: Efficient data retrieval with customizable sorting
- **Frontend Interface** (Optional): Visual search and filter interface

## 📋 Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Legal & Ethical Considerations](#legal--ethical-considerations)
- [Contributing](#contributing)
- [License](#license)

## 🛠 Tech Stack

- **Language**: Python 3.9+
- **Web Scraping**: Playwright (async, modern, better anti-detection)
- **API Framework**: FastAPI (auto-generates OpenAPI docs, async support)
- **Database**: PostgreSQL with SQLAlchemy ORM (structured data, complex queries)
- **Frontend**: React + Vite (modern, fast development)
- **Additional**: Redis (optional, for caching)

## 📁 Project Structure

```
amazon-deals-scraper/
├── scraper/              # Web scraping modules
│   ├── __init__.py
│   ├── amazon_scraper.py # Main scraper logic
│   ├── config.py         # Scraper configuration
│   └── utils.py          # Helper functions
├── api/                  # FastAPI application
│   ├── __init__.py
│   ├── main.py           # API entry point
│   ├── routes/           # API endpoints
│   ├── models.py         # Pydantic models
│   └── dependencies.py   # Shared dependencies
├── database/             # Database layer
│   ├── __init__.py
│   ├── connection.py     # DB connection manager
│   ├── models.py         # ORM/ODM models
│   └── operations.py     # CRUD operations
├── frontend/             # Frontend application (optional)
│   ├── src/
│   ├── public/
│   └── package.json
├── data/                 # Scraped data storage
│   ├── sample_products.json
│   └── sample_products.csv
├── tests/                # Unit and integration tests
├── logs/                 # Application logs
├── .env.example          # Environment variables template
├── .gitignore
├── requirements.txt      # Python dependencies
└── README.md
```

## 🔧 Installation

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 13+ or MongoDB 5+
- Node.js 16+ (for frontend, optional)
- Git

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/amazon-deals-scraper.git
   cd amazon-deals-scraper
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   # For PostgreSQL
   python database/init_db.py
   
   # For MongoDB (auto-creates collections)
   # No initialization needed
   ```

## ⚙️ Configuration

Create a `.env` file in the root directory:

```env
# Database Configuration
DATABASE_TYPE=postgresql  # or mongodb
DB_HOST=localhost
DB_PORT=5432
DB_NAME=amazon_deals
DB_USER=your_username
DB_PASSWORD=your_password

# MongoDB (if using)
MONGO_URI=mongodb://localhost:27017/amazon_deals

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=True

# Scraper Configuration
SCRAPER_DELAY=3  # Seconds between requests
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64)
MAX_RETRIES=3

# Optional: Proxy Configuration
USE_PROXY=false
PROXY_URL=http://proxy.example.com:8080
```

## 🚀 Usage

### Running the Scraper

```bash
python scraper/amazon_scraper.py --category electronics --pages 5
```

### Starting the API Server

```bash
# Development
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Running the Frontend (Optional)

```bash
cd frontend
npm install
npm run dev
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Get All Products
```http
GET /api/v1/products
```

**Query Parameters:**
- `category` (string): Filter by category
- `brand` (string): Filter by brand
- `min_price` (float): Minimum price
- `max_price` (float): Maximum price
- `min_rating` (float): Minimum rating (0-5)
- `min_discount` (int): Minimum discount percentage
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20)
- `sort_by` (string): Sort field (price, rating, discount)
- `order` (string): Sort order (asc, desc)

**Example:**
```bash
curl "http://localhost:8000/api/v1/products?category=electronics&min_discount=30&sort_by=discount&order=desc&page=1&limit=10"
```

#### 2. Get Product by ID
```http
GET /api/v1/products/{product_id}
```

#### 3. Get Best Deals
```http
GET /api/v1/best-deals
```

**Query Parameters:**
- `limit` (int): Number of deals to return (default: 20)
- `min_discount` (int): Minimum discount percentage (default: 20)
- `min_rating` (float): Minimum rating (default: 4.0)

**Example:**
```bash
curl "http://localhost:8000/api/v1/best-deals?limit=10&min_discount=40&min_rating=4.5"
```

#### 4. Get Categories
```http
GET /api/v1/categories
```

#### 5. Get Brands
```http
GET /api/v1/brands
```

### Interactive API Docs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🗄 Database Schema

### PostgreSQL Schema

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(255) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    brand VARCHAR(255),
    category VARCHAR(255),
    current_price DECIMAL(10, 2),
    original_price DECIMAL(10, 2),
    discount_percentage INTEGER,
    rating DECIMAL(3, 2),
    review_count INTEGER,
    product_url TEXT NOT NULL,
    image_url TEXT,
    availability VARCHAR(50),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_category ON products(category);
CREATE INDEX idx_brand ON products(brand);
CREATE INDEX idx_price ON products(current_price);
CREATE INDEX idx_discount ON products(discount_percentage);
CREATE INDEX idx_rating ON products(rating);
```

### MongoDB Schema

```json
{
  "_id": "ObjectId",
  "product_id": "string",
  "title": "string",
  "brand": "string",
  "category": "string",
  "current_price": "number",
  "original_price": "number",
  "discount_percentage": "number",
  "rating": "number",
  "review_count": "number",
  "product_url": "string",
  "image_url": "string",
  "availability": "string",
  "scraped_at": "date",
  "updated_at": "date"
}
```

## ⚖️ Legal & Ethical Considerations

⚠️ **Important Notice:**

- Amazon's Terms of Service prohibit automated scraping
- This project is for **educational purposes only**
- For production use, consider Amazon Product Advertising API (official)
- Always respect:
  - Rate limits (2-5 seconds between requests)
  - robots.txt directives
  - Website terms of service
  - User privacy and data protection laws

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

Eya Amari [https://www.linkedin.com/in/amari-eya/]

Project Link: [https://github.com/AmariEyaa/amazon-deals-scraper](https://github.com/AmariEyaa/amazon-deals-scraper)

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
- [Selenium](https://www.selenium.dev/)
- [PostgreSQL](https://www.postgresql.org/)

---

