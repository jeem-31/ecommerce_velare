# Seller Orders Management - Database Query

## Location
**File**: `blueprints/seller_product_management.py`  
**Function**: `list_seller_orders()` (line 768-878)  
**Route**: `/api/orders` (GET)

---

## Main Query

```python
orders_response = supabase.table('orders').select(
    'order_id, order_number, created_at, subtotal, total_amount, order_status, buyer_id, buyers(first_name, last_name), deliveries(status)'
).eq('seller_id', seller_id).order('created_at', desc=True).execute()
```

---

## Tables Used

### 1. **`orders`** (Main Table)
Columns fetched:
- `order_id` - Primary key
- `order_number` - Order reference number (e.g., VEL-2026-0001)
- `created_at` - When order was placed
- `subtotal` - Order subtotal amount
- `total_amount` - Total order amount
- `order_status` - Order status (pending, delivered, cancelled)
- `buyer_id` - Reference to buyer

**Filter**: `.eq('seller_id', seller_id)` - Only orders for this seller

### 2. **`buyers`** (Joined Table)
Columns fetched:
- `first_name` - Buyer's first name
- `last_name` - Buyer's last name

**Used for**: Display buyer name in orders list

### 3. **`deliveries`** (Joined Table)
Columns fetched:
- `status` - Delivery status

**Possible values**:
- `NULL` - Order just placed (seller hasn't started)
- `'preparing'` - Seller preparing package
- `'pending'` - Ready for pickup (visible to riders)
- `'assigned'` - Rider accepted
- `'in_transit'` - Rider picked up, on the way
- `'delivered'` - Delivered to buyer
- `'cancelled'` - Cancelled

---

## Status Field Logic

The **status** displayed in Orders Management comes from **TWO sources**:

### 1. **`orders.order_status`**
Main order status:
- `'pending'` - Order is active
- `'delivered'` - Order completed
- `'cancelled'` - Order cancelled

### 2. **`deliveries.status`**
Delivery/fulfillment status:
- `NULL` → "New Order"
- `'preparing'` → "Preparing"
- `'pending'` → "Pending" (ready for pickup)
- `'assigned'` → "Assigned to Rider"
- `'in_transit'` → "In Transit"
- `'delivered'` → "Delivered"
- `'cancelled'` → "Cancelled"

---

## Display Logic (in Template)

**File**: `templates/seller/seller_dashboard.html` (line 205-220)

```html
<span class="status-badge status-{{ order.delivery_status or order.order_status }}">
    {% if order.delivery_status == None or order.delivery_status == 'none' %}
        New Order
    {% elif order.delivery_status == 'preparing' %}
        Preparing
    {% elif order.delivery_status == 'pending' or order.order_status == 'pending' %}
        Pending
    {% elif order.delivery_status == 'assigned' %}
        Assigned to Rider
    {% elif order.delivery_status == 'in_transit' or order.order_status == 'in_transit' %}
        In Transit
    {% elif order.delivery_status == 'delivered' or order.order_status == 'delivered' %}
        Delivered
    {% elif order.order_status == 'cancelled' %}
        Cancelled
    {% else %}
        {{ order.delivery_status or order.order_status }}
    {% endif %}
</span>
```

---

## Priority

**`deliveries.status`** is checked FIRST, then falls back to **`orders.order_status`**

This means:
1. If delivery has a status → Show delivery status
2. If delivery status is NULL → Show order status
3. If order is cancelled → Show "Cancelled"

---

## Additional Queries

The function also fetches:

### Order Items
```python
supabase.table('order_items').select(
    'order_id, product_id, product_name, quantity, unit_price, variant_color, variant_size'
).in_('order_id', order_ids).execute()
```

### Product Images
```python
supabase.table('product_images').select(
    'product_id, image_url'
).eq('is_primary', True).in_('product_id', product_ids).execute()
```

---

## Summary

**Main Status Field**: `deliveries.status`  
**Fallback Status**: `orders.order_status`  
**Tables**: `orders`, `deliveries`, `buyers`, `order_items`, `product_images`  
**Key Column**: `deliveries.status` (NULL, preparing, pending, assigned, in_transit, delivered, cancelled)
