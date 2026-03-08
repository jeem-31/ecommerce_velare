# Edit Product - Delete Functionality Fix

## Problem
The delete functionality in the Edit Product modal was not working:
1. **Delete Variant** - Clicking the delete button on a variant did nothing
2. **Delete Image** - Removing images from variants didn't actually delete them from the database

## Root Causes

### 1. Delete Variant Endpoint (MySQL)
The `/api/products/variants/<variant_id>` DELETE endpoint was still using MySQL:
```python
connection = get_db_connection()  # MySQL
cursor = connection.cursor(dictionary=True)
cursor.execute("DELETE FROM product_variants WHERE variant_id = %s", (variant_id,))
```

### 2. Delete Images Not Implemented
The backend was receiving `deletedImages` data from JavaScript but wasn't processing it at all. The data was being sent but ignored.

## Solutions Implemented

### 1. Migrated Delete Variant to Supabase

**File:** `blueprints/seller_product_management.py`

**Changes:**
- Replaced MySQL connection with Supabase client
- Updated query to use Supabase syntax
- Added proper ownership verification
- Delete variant images before deleting variant
- Enhanced logging with emojis

```python
@seller_product_management_bp.route('/api/products/variants/<int:variant_id>', methods=['DELETE'])
@seller_required
def delete_variant(variant_id):
    """Delete a variant using Supabase"""
    supabase = get_supabase_client()
    
    # Verify variant belongs to seller's product
    variant_check = supabase.table('product_variants').select(
        'product_id, products!inner(seller_id)'
    ).eq('variant_id', variant_id).execute()
    
    # Verify ownership
    if product_seller_id != seller_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Delete variant images first
    supabase.table('product_images').delete().eq('variant_id', variant_id).execute()
    
    # Delete variant
    supabase.table('product_variants').delete().eq('variant_id', variant_id).execute()
    
    return jsonify({'success': True, 'message': 'Variant deleted successfully'}), 200
```

### 2. Implemented Delete Images Functionality

**File:** `blueprints/seller_edit_products.py`

**Added:** Image deletion handling in `update_product()` function

```python
# Handle deleted images
deleted_images_data = request.form.get('deletedImages')
if deleted_images_data:
    deleted_images = json.loads(deleted_images_data)
    print(f"🗑️ Deleting {len(deleted_images)} images...")
    
    for img_info in deleted_images:
        variant_id = img_info.get('variantId')
        image_url = img_info.get('imageUrl')
        
        # Handle both Supabase URLs and local paths
        if image_url.startswith('http://') or image_url.startswith('https://'):
            clean_url = image_url
        else:
            clean_url = image_url.lstrip('/')
        
        # Delete from product_images table
        if variant_id:
            supabase.table('product_images').delete().eq('variant_id', variant_id).eq('image_url', clean_url).execute()
        else:
            # Product-level image (no variant_id)
            supabase.table('product_images').delete().eq('product_id', product_id).is_('variant_id', 'null').eq('image_url', clean_url).execute()
```

## Changes Made

### File: `blueprints/seller_product_management.py`

**Lines ~491-550:** Complete rewrite of `delete_variant()` function
- Migrated from MySQL to Supabase
- Added ownership verification with JOIN
- Delete variant images before deleting variant
- Enhanced error handling and logging

### File: `blueprints/seller_edit_products.py`

**Lines ~303-340:** Added deleted images handling
- Reads `deletedImages` from form data
- Loops through each deleted image
- Handles both Supabase URLs and local paths
- Deletes from `product_images` table
- Supports both variant images and product-level images

## Delete Flow

### Delete Variant
```
1. User clicks delete button on variant
2. JavaScript sends DELETE request to /api/products/variants/{variant_id}
3. Backend verifies ownership
4. Backend deletes all variant images from product_images table
5. Backend deletes variant from product_variants table
6. Returns success
7. Frontend refreshes product list
```

### Delete Image
```
1. User clicks X button on image
2. JavaScript adds image to imagesToDelete array
3. User clicks Save
4. JavaScript sends imagesToDelete in form data
5. Backend processes deletedImages
6. Backend deletes each image from product_images table
7. Returns success
8. Frontend refreshes product
```

## Database Operations

### Delete Variant
```sql
-- Delete variant images
DELETE FROM product_images WHERE variant_id = {variant_id}

-- Delete variant
DELETE FROM product_variants WHERE variant_id = {variant_id}
```

### Delete Image
```sql
-- For variant image
DELETE FROM product_images 
WHERE variant_id = {variant_id} 
AND image_url = {image_url}

-- For product-level image
DELETE FROM product_images 
WHERE product_id = {product_id} 
AND variant_id IS NULL 
AND image_url = {image_url}
```

## URL Handling

Both Supabase URLs and local paths are supported:

```python
# Supabase URL
"https://lpbmlhncfnxtwzpyoqrp.supabase.co/storage/v1/object/public/Images/..."
→ Use as-is

# Local path
"static/uploads/products/image.jpg"
→ Remove leading slash: "static/uploads/products/image.jpg"

# Local path with leading slash
"/static/uploads/products/image.jpg"
→ Remove leading slash: "static/uploads/products/image.jpg"
```

## Testing Checklist

### Delete Variant
- [x] Click delete on variant → Variant removed from database
- [x] Variant images also deleted from product_images table
- [x] Only owner can delete their variants (ownership check)
- [x] Product list refreshes after deletion
- [x] Success notification shown

### Delete Image
- [x] Click X on variant image → Image marked for deletion
- [x] Click Save → Image deleted from database
- [x] Handles Supabase URLs correctly
- [x] Handles local paths correctly
- [x] Can delete multiple images at once
- [x] Product-level images can be deleted
- [x] Variant images can be deleted

## Expected Terminal Output

### Delete Variant
```
🗑️ DELETE VARIANT REQUEST - Variant ID: 45
👤 Seller ID: 7
🔍 Verifying variant ownership...
✅ Variant belongs to product 160
🖼️ Deleting variant images...
🗑️ Deleting variant...
✅ Variant 45 deleted successfully
```

### Delete Images
```
🗑️ Deleting 2 images...
  🗑️ Deleting image: https://lpbmlhncfnxtwzpyoqrp.supabase.co/storage/v1/object/...
  ✅ Image deleted
  🗑️ Deleting image: static/uploads/products/20260210_120000_45_1_image.jpg
  ✅ Image deleted
✅ All marked images deleted
```

## Related Files
- `blueprints/seller_product_management.py` - Delete variant endpoint (lines ~491-550)
- `blueprints/seller_edit_products.py` - Delete images handling (lines ~303-340)
- `static/js/seller/seller-product-management.js` - Frontend delete logic (lines ~4083-4086)

## Status
✅ **FIXED** - Both delete variant and delete images now work correctly with Supabase
