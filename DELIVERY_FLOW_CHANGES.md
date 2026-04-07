# Delivery Flow Changes Summary

## Date: April 7, 2026

## Changes Made

### Updated Flow:
```
NULL → preparing → pending → assigned → in_transit → delivered
```

---

## Files Modified

### 1. `blueprints/checkout_order.py`
**Line 197-203**: Changed initial delivery status from `'preparing'` to `None` (NULL)
```python
delivery_data = {
    'status': None  # NULL status - seller must click "Prepare Package" first
}
```

### 2. `blueprints/seller_product_management.py`
**Existing endpoint** (line 880-918): `/api/orders/<int:order_id>/preparing`
- Marks delivery status as `'preparing'`
- First step after order placement
- Allows buyer to see "Preparing Package"

**Existing endpoint** (line 922-959): `/api/orders/<int:order_id>/ready-for-pickup`
- Marks delivery status as `'pending'`
- Second step - makes order visible to riders
- Allows buyer to see "Pending Shipment"

### 3. `static/js/seller/seller-product-management.js`
**Line 4260**: Updated API endpoint call
```javascript
const response = await fetch(`/api/orders/${orderId}/prepare-package`, {
```

### 4. `templates/accounts/myAccount_purchases.html`
**Line 167-169**: Added NULL status handling for buyer view
```html
{% elif order.delivery_status == None or order.delivery_status == 'none' %}
    {% set display_label = 'Order Placed' %}
```

### 5. `blueprints/myAccount_purchases.py`
**Line 181**: Updated counts calculation to include NULL status
```python
elif order['delivery_status'] in ['pending', 'assigned', 'preparing'] or order['delivery_status'] is None:
```

### 6. `templates/seller/seller_dashboard.html`
**Line 205-207**: Added NULL status display for seller view
```html
{% if order.delivery_status == None or order.delivery_status == 'none' %}
    New Order
```

---

## Complete Flow Explanation

### Step 1: Buyer Places Order
- **Delivery Status**: `NULL`
- **Buyer sees**: "Order Placed"
- **Seller sees**: "Prepare Package" button
- **Rider sees**: Nothing (not in list)

### Step 2: Seller Clicks "Prepare Package"
- **API**: `POST /api/orders/{order_id}/preparing`
- **Delivery Status**: `NULL` → `'preparing'`
- **Buyer sees**: "Preparing Package"
- **Seller sees**: "Ready for Pickup" button
- **Rider sees**: Nothing (not in list)

### Step 3: Seller Clicks "Ready for Pickup"
- **API**: `POST /api/orders/{order_id}/ready-for-pickup`
- **Delivery Status**: `'preparing'` → `'pending'`
- **Buyer sees**: "Pending Shipment"
- **Seller sees**: Order marked as ready
- **Rider sees**: ✅ Order now appears in pickup list

### Step 4: Rider Accepts
- **Delivery Status**: `'pending'` → `'assigned'`
- **Buyer sees**: "Pending Shipment"
- **Rider sees**: Moved to "Active Delivery"

### Step 5: Rider Picks Up
- **Delivery Status**: `'assigned'` → `'in_transit'`
- **Buyer sees**: "In Transit"
- **Rider sees**: Delivery in progress

### Step 6: Rider Delivers
- **Delivery Status**: `'in_transit'` → `'delivered'`
- **Buyer sees**: "Delivered" + confirm button
- **Rider sees**: Delivery completed

---

## Testing Checklist

- [ ] Place new order - verify delivery status is NULL in database
- [ ] Check buyer's purchases page - should show "Order Placed"
- [ ] Check seller's dashboard - should show "New Order" status
- [ ] Click "Prepare Package" button - verify status changes to 'preparing'
- [ ] Check buyer's purchases page - should show "Preparing Package"
- [ ] Check rider's pickup list - should NOT show the order yet
- [ ] Click "Ready for Pickup" button - verify status changes to 'pending'
- [ ] Check buyer's purchases page - should show "Pending Shipment"
- [ ] Check rider's pickup list - should NOW show the order
- [ ] Rider accepts delivery - verify status changes to 'assigned'
- [ ] Rider picks up - verify status changes to 'in_transit'
- [ ] Rider delivers - verify status changes to 'delivered'

---

## Database Requirements

The `deliveries` table must allow NULL values for the `status` column:

```sql
ALTER TABLE deliveries 
ALTER COLUMN status DROP NOT NULL;
```

Or if creating new table:

```sql
CREATE TABLE deliveries (
    delivery_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    rider_id INTEGER REFERENCES riders(rider_id),
    status VARCHAR(20) CHECK (status IN ('preparing', 'pending', 'assigned', 'in_transit', 'delivered', 'cancelled') OR status IS NULL),
    -- other columns...
);
```

---

## Notes

- Riders will ONLY see deliveries with `status='pending'`
- NULL and 'preparing' statuses are NOT visible to riders
- Seller must take TWO actions: "Prepare Package" then "Ready for Pickup"
- Buyer sees status updates at each step
