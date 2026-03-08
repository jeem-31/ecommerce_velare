# Add Product - Categories and Duplicate Images Issue

## Current Categories (Add Product Form)

The Add Product form has the following category options:

```html
<select id="productCategory" name="productCategory" required>
    <option value="">Select Category</option>
    <option value="dresses">Dresses</option>
    <option value="skirts">Skirts</option>
    <option value="tops">Tops</option>
    <option value="blouses">Blouses</option>
    <option value="activewear-yoga">Activewear & Yoga Pants</option>
    <option value="lingerie">Lingerie</option>
    <option value="sleepwear">Sleepwear</option>
    <option value="jackets">Jackets</option>
    <option value="coats">Coats</option>
    <option value="shoes">Shoes</option>
    <option value="accessories">Accessories</option>
</select>
```

### Category Mapping (Form → Database)

| Form Value | Database Value |
|------------|----------------|
| `dresses` | `Dresses` |
| `skirts` | `Skirts` |
| `tops` | `Tops` |
| `blouses` | `Blouses` |
| `activewear-yoga` | `Active Wear-Yoga Pants` |
| `lingerie` | `Lingerie` |
| `sleepwear` | `Sleepwear` |
| `jackets` | `Jackets` |
| `coats` | `Coats` |
| `shoes` | `Shoes` |
| `accessories` | `Accessories` |

**Note:** Only `activewear-yoga` is currently being converted to database format. Other categories need conversion too!

---

## Duplicate Images Issue

### Problem Description
When adding a product with multiple variants of the same color (e.g., Red-S, Red-M, Red-L), duplicate images are being inserted into the `product_images` table.

### Root Cause Analysis

**Current Logic (Lines 420-442 in `seller_product_management.py`):**

```python
# Insert images linked to the first variant of each color
for color_hex, image_paths in color_image_map.items():
    # Get the first variant_id for this color
    variant_ids = variant_ids_by_color.get(color_hex, [])
    first_variant_id = variant_ids[0] if variant_ids else None
    
    for img_idx, image_path in enumerate(image_paths):
        is_primary = (image_counter == 0)  # First image overall is primary
        
        supabase.table('product_images').insert({
            'product_id': product_id,
            'variant_id': first_variant_id,  # ← ALL images linked to FIRST variant only
            'image_url': image_path,
            'is_primary': is_primary,
            'display_order': image_counter
        }).execute()
        
        image_counter += 1
```

**The Issue:**
- Images are grouped by color
- ALL images for a color are linked to the FIRST variant of that color
- If you have Red-S, Red-M, Red-L, all Red images are linked to Red-S only
- This is correct behavior, but might cause confusion

**However, there might be ACTUAL duplicates if:**
1. The same image is uploaded multiple times
2. The image-color mapping has duplicates
3. The loop is running multiple times somehow

### Potential Duplicate Scenarios

#### Scenario 1: Same Image Uploaded Multiple Times
If the user uploads the same image file multiple times, each upload creates a unique filename with timestamp:
```
20260210_120000_0_image.jpg
20260210_120000_1_image.jpg  ← Same image, different index
```

#### Scenario 2: Image-Color Mapping Has Duplicates
If the JavaScript sends duplicate entries in `imageColorMapping`:
```json
[
  {"colorHex": "#ff0000", "colorName": "Red"},
  {"colorHex": "#ff0000", "colorName": "Red"}  ← Duplicate
]
```

#### Scenario 3: Multiple Variants Same Color
This is EXPECTED behavior:
- Red-S, Red-M, Red-L all share the same images
- Images are linked to Red-S (first variant)
- Other variants (Red-M, Red-L) reference the same images through their color

### Database Structure

**product_variants table:**
```
variant_id | product_id | color | hex_code | size | image_url
-----------|------------|-------|----------|------|----------
45         | 100        | Red   | #ff0000  | S    | https://...image1.jpg
46         | 100        | Red   | #ff0000  | M    | https://...image1.jpg
47         | 100        | Red   | #ff0000  | L    | https://...image1.jpg
```

**product_images table:**
```
image_id | product_id | va