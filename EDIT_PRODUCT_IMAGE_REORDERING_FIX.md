# Edit Product - Image Reordering Fix

## Problem Summary
When editing a product and reordering variant images (changing the primary image), the changes were not being saved to the database. The terminal showed "Product updated successfully" but no image reordering logs appeared.

## Root Cause
The image reordering code was nested inside the "new images upload" check. This meant:
- If a variant had `variant_{id}_has_new_images` flag → reordering code would run
- If a variant only had `variant_{id}_image_order` (no new images) → reordering code was SKIPPED

**The issue:** When users just reordered existing images without uploading new ones, the reordering loop never executed.

## Solution Implemented

### 1. Restructured Image Processing Logic
Changed from nested structure to parallel processing:

**BEFORE (Nested - Broken):**
```python
for key in request.form.keys():
    if key.endswith('_has_new_images'):
        # Upload new images
        ...
        # Handle reordering (only runs if new images exist)
        if order_key in request.form:
            # Reorder images
```

**AFTER (Parallel - Fixed):**
```python
# Collect ALL variants with image data (new uploads OR reordering)
variant_ids_with_images = set()
for key in request.form.keys():
    if '_has_new_images' in key or '_image_order' in key:
        variant_ids_with_images.add(variant_id)

# Process each variant
for variant_id in variant_ids_with_images:
    # Upload new images if present
    if has_new_images_key in request.form:
        # Upload logic
    
    # Handle reordering (runs independently)
    if order_key in request.form:
        # Reorder logic
```

### 2. Enhanced URL Handling
Added support for both Supabase URLs and local paths:

```python
# Handle both Supabase URLs and local paths
raw_url = img_info['url']

if raw_url.startswith('http://') or raw_url.startswith('https://'):
    clean_url = raw_url  # Supabase URL - use as-is
else:
    clean_url = raw_url.lstrip('/')  # Local path - remove leading slash
```

### 3. Added Comprehensive Debug Logging
```python
print(f"📋 All form keys: {list(request.form.keys())}")
print(f"📦 Found {len(variant_ids_with_images)} variants with image data")
print(f"🔍 Checking for reordering key: {order_key}")
print(f"📦 Raw image order data: {image_order_raw}")
print(f"🔄 Reordering {len(image_order)} images for variant {variant_id}")
print(f"✅ New primary image: {clean_url[:80]}...")
```

## Changes Made

### File: `blueprints/seller_edit_products.py`

**Lines ~318-430:** Complete rewrite of variant image processing section

**Key Changes:**
1. Collect all variant IDs with image data upfront (line ~325)
2. Process each variant independently (line ~333)
3. Upload new images if present (line ~337-370)
4. Handle reordering separately (line ~373-425)
5. Support both Supabase URLs and local paths (line ~398-404)
6. Update variant's `image_url` to new primary (line ~418-422)

## Testing Checklist

- [x] Reorder images without uploading new ones → Should update primary image
- [x] Upload new images → Should save to Supabase Storage with full URLs
- [x] Upload new images AND reorder → Both operations should work
- [x] Handle Supabase URLs (https://...) correctly
- [x] Handle local paths (static/uploads/...) correctly
- [x] Update variant's `image_url` field to new primary image
- [x] Update `is_primary` flag in `product_images` table
- [x] Update `display_order` in `product_images` table

## Expected Terminal Output

When reordering images, you should now see:
```
🖼️ PROCESSING VARIANT IMAGES
📋 All form keys: ['name', 'category', 'variant_45_image_order', ...]
📦 Found 1 variants with image data: {'45'}

  Processing variant 45...
  🔍 Checking for reordering key: variant_45_image_order
  🔍 Key exists in form: True
  📦 Raw image order data: [{"url":"https://...", "isNew":false, ...}]
  🔄 Reordering 3 images for variant 45
    Updating image 0: https://lpbmlhncfnxtwzpyoqrp.supabase.co/storage... (primary: True)
    ✅ New primary image: https://lpbmlhncfnxtwzpyoqrp.supabase.co/storage...
    ✅ Updated variant 45 image_url to primary
✅ Product 160 updated successfully
```

## Related Files
- `blueprints/seller_edit_products.py` - Backend image processing
- `static/js/seller/seller-product-management.js` - Frontend form submission (line ~4113)

## Status
✅ **FIXED** - Image reordering now works independently of new image uploads
