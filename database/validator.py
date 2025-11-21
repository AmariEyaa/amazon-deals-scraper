"""Data validation for products before database insertion"""
from typing import Dict, Optional, List
from datetime import datetime
from loguru import logger


def validate_product_data(product_data: Dict) -> tuple[bool, Optional[str]]:
    """
    Validate product data before insertion
    
    Returns:
        (is_valid, error_message)
    """
    required_fields = ['product_id', 'title']
    
    # Check required fields
    for field in required_fields:
        if field not in product_data or not product_data[field]:
            return False, f"Missing required field: {field}"
    
    # Validate product_id format (Amazon ASIN)
    product_id = product_data['product_id']
    if not isinstance(product_id, str) or len(product_id) != 10:
        return False, f"Invalid product_id format: {product_id} (must be 10 characters)"
    
    # Validate title length
    title = product_data['title']
    if not isinstance(title, str) or len(title) < 5:
        return False, f"Title too short: {len(title)} characters"
    
    # Validate prices if present
    if 'current_price' in product_data:
        price = product_data['current_price']
        if price is not None:
            if not isinstance(price, (int, float)) or price < 0:
                return False, f"Invalid current_price: {price}"
    
    if 'original_price' in product_data:
        price = product_data['original_price']
        if price is not None:
            if not isinstance(price, (int, float)) or price < 0:
                return False, f"Invalid original_price: {price}"
    
    # Validate rating if present
    if 'rating' in product_data:
        rating = product_data['rating']
        if rating is not None:
            if not isinstance(rating, (int, float)) or not (0 <= rating <= 5):
                return False, f"Invalid rating: {rating} (must be between 0 and 5)"
    
    # Validate review_count if present
    if 'review_count' in product_data:
        count = product_data['review_count']
        if count is not None:
            if not isinstance(count, int) or count < 0:
                return False, f"Invalid review_count: {count}"
    
    # Validate discount_percentage if present
    if 'discount_percentage' in product_data:
        discount = product_data['discount_percentage']
        if discount is not None:
            if not isinstance(discount, (int, float)) or not (0 <= discount <= 100):
                return False, f"Invalid discount_percentage: {discount}"
    
    # Validate URLs if present
    url_fields = ['product_url', 'image_url']
    for field in url_fields:
        if field in product_data and product_data[field]:
            url = product_data[field]
            if not isinstance(url, str) or not url.startswith(('http://', 'https://')):
                return False, f"Invalid {field}: {url}"
    
    return True, None


def clean_product_data(raw_data: Dict) -> Dict:
    """
    Clean and normalize product data from scraper
    
    Converts scraper output format to database format
    """
    cleaned = {}
    
    # Direct mappings
    field_mappings = {
        'product_id': 'product_id',
        'title': 'title',
        'brand': 'brand',
        'category': 'category',
        'current_price': 'current_price',
        'original_price': 'original_price',
        'discount_percentage': 'discount_percentage',
        'rating': 'rating',
        'review_count': 'review_count',
        'product_url': 'product_url',
        'image_url': 'image_url',
        'availability': 'availability',
        'is_sponsored': 'is_sponsored',
    }
    
    for raw_key, db_key in field_mappings.items():
        if raw_key in raw_data and raw_data[raw_key] is not None:
            cleaned[db_key] = raw_data[raw_key]
    
    # Handle price conversions (scraper might return strings like "$29.99")
    for price_field in ['current_price', 'original_price']:
        if price_field in raw_data and isinstance(raw_data[price_field], str):
            try:
                # Remove $ and , characters
                price_str = raw_data[price_field].replace('$', '').replace(',', '')
                cleaned[price_field] = float(price_str)
            except (ValueError, AttributeError):
                cleaned[price_field] = None
    
    # Handle review_count (might be string like "1,234")
    if 'review_count' in raw_data and isinstance(raw_data['review_count'], str):
        try:
            count_str = raw_data['review_count'].replace(',', '')
            cleaned['review_count'] = int(count_str)
        except (ValueError, AttributeError):
            cleaned['review_count'] = None
    
    # Set default timestamps
    now = datetime.utcnow()
    cleaned['first_seen_at'] = now
    cleaned['last_updated_at'] = now
    cleaned['created_at'] = now
    
    return cleaned


def validate_product_batch(products_data: List[Dict]) -> tuple[List[Dict], List[Dict]]:
    """
    Validate a batch of products
    
    Returns:
        (valid_products, invalid_products_with_errors)
    """
    valid = []
    invalid = []
    
    for product in products_data:
        is_valid, error = validate_product_data(product)
        
        if is_valid:
            valid.append(product)
        else:
            logger.warning(f"Invalid product {product.get('product_id', 'unknown')}: {error}")
            invalid.append({
                'product': product,
                'error': error
            })
    
    logger.info(f"Validation: {len(valid)} valid, {len(invalid)} invalid out of {len(products_data)}")
    
    return valid, invalid


def prepare_product_for_db(raw_product: Dict) -> Optional[Dict]:
    """
    Complete pipeline: clean and validate product data
    
    Returns:
        Cleaned product dict if valid, None if invalid
    """
    cleaned = clean_product_data(raw_product)
    is_valid, error = validate_product_data(cleaned)
    
    if not is_valid:
        logger.warning(f"Product validation failed: {error}")
        return None
    
    return cleaned
