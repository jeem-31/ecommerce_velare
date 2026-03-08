# Add Variant - Multiple Images Fix

## Problem
When adding a new variant through the "Add Variant" modal in the Product List, only ONE image was being saved per variant, even though users could upload multiple images.

## Root Cause
The backend code was incorrectly processing the image array. It assumed one image per variant:

```python
# OLD CODE (BROKEN)
for index, variant in enumerate(new_variants):
    # Only gets ONE image per variant
    if index < len(new_variant_images):
        image_file = new_variant_images[index]
        # ... save only this one image
```

**The issue:** 
- JavaScript sends ALL images in a flat array: `[img1_v1, img2_v1, img3_v1, img1_v2, img2_v2]`
- JavaScript also sends `numImages` for each variant to indicate how many images belong to it
- Backend was ignoring `numImages` and only taking one image per variant

## Solution Implemented

### Enhanced New Variant Creation Logic

**Key Changes:**
1. Read `numImages` from each variant data
2. Track image index across all variants (not per variant)
3. Upload ALL images for each variant to Supabase Storage
4. Insert each image into `product_images` table with proper metadata
5. Set variant's `image_url` to the first (primary) image

```python
# Track image index across all variants
image_index = 0

for variant_index, variant in enumerate(new_variants):
    num_images = int(variant.get('numImages', 0))
    
    # Create variant first to get variant_id
    variant_response = supabase.table('product_variants').insert({...}).execute()
    new_variant_id = variant_response.data[0]['variant_id']
    
    # Upload ALL images for this variant
    first_image_url = None
    for img_idx in range(num_images):
        if image_index < len(new_variant_images):
            image_file = new_variant_images[image_index]
            
            # Upload to Supabase Storage
            image_url = upload_to_supabase_storage(image_file, unique_filename)
            
            # Insert into product_images table
            supabase.table('product_images').insert({
                'product_id': product_id,
                'variant_id': new_variant_id,
                'image_url': image_url,
                'is_primary': (img_idx == 0),
                'display_order': img_idx
            }).execute()
            
            if img_idx == 0:
                first_image_url = image_url
            
            image_index += 1  # Move to next image in flat array
    
    # Update variant's image_url to first image
    if first_image_url:
        supabase.table('product_variants').update({
            'image_url': first_image_url
        }).eq('variant_id', new_variant_id).execute()
```

## Changes Made

### File: `blueprints/seller_edit_products.py`

**Lines ~302-375:** Complete rewrite of new variant creation logic

**Key Improvements:**
1. **Reads `numImages`** from variant data (line ~318)
2. **Creates variant first** to get `variant_id` (lines ~321-332)
3. **Loops through all images** for each variant (lines ~337-365)
4. **Uploads to Supabase Storage** with full URLs (line ~346)
5. **Inserts into `product_images`** table with metadata (lines ~349-356)
6. **Sets primary image** correctly (line ~351)
7. **Updates variant's `image_url`** to first image (lines ~368-372)

## Image Processing Flow

### Before (Broken)
```
Variant 1: Gets image at index 0 only
Variant 2: Gets image at index 1 only
Variant 3: Gets image at index 2 only
Result: 1 image per variant, rest are ignored
```

### After (Fixed)
```
Variant 1 (3 images): Gets images at index 0, 1, 2
Variant 2 (2 images): Gets images at index 3, 4
Variant 3 (1 image):  Gets image at index 5
Result: All images saved correctly
```

## Database Structure

### Tables Updated

**1. product_variants**
- `variant_id` - Auto-generated
- `image_url` - Set to first (primary) image URL

**2. product_images**
- `product_id` - Product ID
- `variant_id` - Variant ID
- `image_url` - Full Supabase Storage URL
- `is_primary` - TRUE for first image, FALSE for others
- `display_order` - 0, 1, 2, 3... (order of images)

## Image URL Format

All images are now uploaded to Supabase Storage with full URLs:
```
https://lpbmlhncfnxtwzpyoqrp.supabase.co/storage/v1/object/public/Images/static/uploads/products/20260210_120000_45_0_image.jpg
```

Format breakdown:
- `20260210_120000` - Timestamp
- `45` - Variant ID
- `0` - Image index (0 = primary)
- `image.jpg` - Original filename

## Testing Checklist

- [x] Add variant with 1 image → Should save 1 image
- [x] Add variant with 3 images → Should save all 3 images
- [x] Add variant with 5 images → Should save all 5 images
- [x] Add multiple variants with different image counts → All images saved correctly
- [x] First image marked as primary (`is_primary = TRUE`)
- [x] Images have correct `display_order` (0, 1, 2, 3...)
- [x] Variant's `image_url` points to first image
- [x] All images uploaded to Supabase Storage with full URLs

## Expected Terminal Output

When adding variants:
```
➕ Adding 2 new variants with 5 total images...
  Variant 1: Red M - 3 images
  ✅ Created variant 45
    ✅ Uploaded image 1/3: 20260210_120000_45_0_red_front.jpg
    ✅ Uploaded image 2/3: 20260210_120000_45_1_red_back.jpg
    ✅ Uploaded image 3/3: 20260210_120000_45_2_red_side.jpg
  ✅ Set variant image_url to first image
  Variant 2: Blue L - 2 images
  ✅ Created variant 46
    ✅ Uploaded image 1/2: 20260210_120000_46_0_blue_front.jpg
    ✅ Uploaded image 2/2: 20260210_120000_46_1_blue_back.jpg
  ✅ Set variant image_url to first image
```

## Related Files
- `blueprints/seller_edit_products.py` - Backend variant creation (lines ~302-375)
- `static/js/seller/seller-product-management.js` - Frontend form submission (lines ~3706-3713)

## Status
✅ **FIXED** - All variant images now save correctly to Supabase Storage
