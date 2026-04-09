# Seller Dashboard Status Column Fix

## Issue
The Status column in seller_dashboard's orders table was using `delivery_status` instead of `order_status`, which was inconsistent with the Orders Management subtab in seller_product_management.

## Fix Applied

### File: `templates/seller/seller_dashboard.html`

**Before** (line 203-220):
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

**After**:
```html
<span class="status-badge status-{{ order.order_status }}">
    {% if order.order_status == 'pending' %}
        Pending
    {% elif order.order_status == 'in_transit' %}
        In Transit
    {% elif order.order_status == 'delivered' %}
        Delivered
    {% elif order.order_status == 'cancelled' %}
        Cancelled
    {% else %}
        {{ order.order_status }}
    {% endif %}
</span>
```

---

## Consistency Achieved

Now both pages use the same status source:

### 1. Seller Dashboard (Recent Orders)
- **Table**: `orders`
- **Column**: `order_status`
- **Values**: pending, in_transit, delivered, cancelled

### 2. Seller Product Management (Orders Subtab)
- **Table**: `orders`
- **Column**: `order_status`
- **Values**: pending, in_transit, delivered, cancelled

---

## Status Values

| Database Value | Display Label |
|---------------|---------------|
| `pending` | Pending |
| `in_transit` | In Transit |
| `delivered` | Delivered |
| `cancelled` | Cancelled |

---

## Backend Query

The backend query in `blueprints/seller_dashboard.py` (line 65-67) already fetches the correct data:

```python
recent_orders_response = supabase.table('orders').select(
    'order_id, order_number, created_at, subtotal, total_amount, 
     order_status,  # ← Used for Status column
     buyer_id, 
     buyers(first_name, last_name), 
     deliveries(status)'  # ← Still fetched but not used for Status display
).eq('seller_id', seller_id).order('created_at', desc=True).limit(10).execute()
```

---

## Why This Change?

1. ✅ **Consistency**: Both seller pages now show the same status
2. ✅ **Simplicity**: Uses main order status, not delivery sub-status
3. ✅ **Clarity**: Easier to understand for sellers
4. ✅ **Alignment**: Matches the Orders Management subtab behavior

---

## Note

The `delivery_status` is still fetched from the database (for potential future use in action buttons or detailed views), but it's no longer used for the Status column display.

---

## Status

✅ **FIXED** - Seller Dashboard now uses `orders.order_status` for the Status column, consistent with Orders Management subtab.
