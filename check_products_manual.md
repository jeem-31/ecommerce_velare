# Manual Database Check Guide

## Para ma-check kung ilang products ang available sa bawat section:

### 1. Start your MySQL server first
- Open XAMPP Control Panel
- Start MySQL service
- Or start your MySQL service

### 2. Open phpMyAdmin or MySQL Workbench

### 3. Run these queries:

#### A. EXCLUSIVELY IN DEMAND (Best Sellers)
```sql
SELECT COUNT(*) as total_count
FROM products p
WHERE p.is_active = 1 AND p.total_sold > 0;

-- To see the actual products:
SELECT p.product_id, p.product_name, p.total_sold, pi.image_url
FROM products p
LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = 1
WHERE p.is_active = 1 AND p.total_sold > 0
ORDER BY p.total_sold DESC;
```

#### B. WHAT'S NEW (Latest Products)
```sql
SELECT COUNT(*) as total_count
FROM products p
WHERE p.is_active = 1;

-- To see the actual products:
SELECT p.product_id, p.product_name, p.created_at, pi.image_url
FROM products p
LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = 1
WHERE p.is_active = 1
ORDER BY p.created_at DESC;
```

#### C. BELOVED BY CONNOISSEURS (Top Rated)
```sql
SELECT COUNT(*) as total_count
FROM products p
WHERE p.is_active = 1 AND p.total_reviews > 0;

-- To see the actual products:
SELECT p.product_id, p.product_name, p.rating, p.total_reviews, pi.image_url
FROM products p
LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = 1
WHERE p.is_active = 1 AND p.total_reviews > 0
ORDER BY p.rating DESC, p.total_reviews DESC;
```

#### D. THE ART OF CHOICE (All Active Products)
```sql
SELECT COUNT(*) as total_count
FROM products p
WHERE p.is_active = 1;

-- To see the actual products:
SELECT p.product_id, p.product_name, pi.image_url
FROM products p
LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = 1
WHERE p.is_active = 1;
```

### 4. Check for products without images:
```sql
SELECT p.product_id, p.product_name
FROM products p
LEFT JOIN product_images pi ON p.product_id = pi.product_id AND pi.is_primary = 1
WHERE p.is_active = 1 AND pi.image_url IS NULL;
```

## Expected Results:
- **Exclusively In Demand**: Products with total_sold > 0
- **What's New**: All active products (sorted by created_at)
- **Beloved by Connoisseurs**: Products with total_reviews > 0
- **The Art of Choice**: All active products (random order)

## After running the test script:
Once MySQL is running, execute:
```bash
python test_product_counts.py
```

This will show you:
- Total count for each section
- Top 5 products in each section
- Products without images (if any)
