# Amazon Scraper Module

## Files Created

### Core Files:
- `__init__.py` - Package initialization
- `config.py` - Configuration and settings (selectors, delays, URLs)
- `utils.py` - Utility functions (price cleaning, rating parsing, etc.)
- `amazon_scraper.py` - Main scraper with Playwright implementation

### Test Files:
- `tests/test_scraper.py` - Simple test script to run the scraper

## Features Implemented

### ✅ Step 5 Complete:

1. **Request Handling with Rate Limiting**
   - Random delays between 2-5 seconds (configurable)
   - Retry logic with exponential backoff (max 3 retries)
   - Timeout handling (30 seconds default)

2. **Parsers for All Data Fields:**
   - ✅ Product title
   - ✅ Brand (extracted from title)
   - ✅ Category (from search keyword)
   - ✅ Current price
   - ✅ Original price
   - ✅ Discount percentage (calculated)
   - ✅ Rating (stars)
   - ✅ Review count
   - ✅ Product URL
   - ✅ Image URL
   - ✅ Product ID
   - ✅ Sponsored status
   - ✅ Timestamp

3. **Error Handling:**
   - Try-except blocks for each extraction
   - Graceful handling of missing elements
   - Returns None for missing data instead of crashing
   - Logging for all errors and warnings

4. **Additional Features:**
   - Playwright stealth mode (hides automation detection)
   - Random user agent rotation
   - Async/await for better performance
   - Context manager support
   - JSON export functionality

## How to Run

### Test the scraper:
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run test (will open browser window)
python tests/test_scraper.py
```

### Run manually:
```bash
# Direct execution
python scraper/amazon_scraper.py
```

## Configuration

Edit `.env` file to customize:
- `SCRAPER_MIN_DELAY` - Minimum delay between requests (default: 2)
- `SCRAPER_MAX_DELAY` - Maximum delay between requests (default: 5)
- `MAX_RETRIES` - Retry attempts on failure (default: 3)
- `MAX_PRODUCTS_PER_SESSION` - Product limit per session (default: 100)
- `MAX_PAGES` - Maximum pages to scrape (default: 5)

## Next Steps

After testing, you can:
1. Adjust CSS selectors in `config.py` if needed
2. Integrate with database (Phase 3)
3. Build API endpoints (Phase 4)
4. Add more anti-detection measures if blocked

## Notes

⚠️ **Important:**
- Browser window opens by default (headless=False) for testing
- First run scrapes 2 pages of "laptop" results
- Results saved to `data/amazon_products.json`
- Check logs for any selector issues
