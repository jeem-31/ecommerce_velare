# Velare E-Commerce - Quick Reference Summary

## 🎯 Key Changes Made (Latest Session)

### 1. Delivery Flow Enhancement
**Problem**: Orders appeared in rider's pickup list immediately after buyer placed order.

**Solution**: Added 3-step seller process:
```
Buyer places order → status = NULL (Seller sees "Prepare Package")
                          ↓
Seller clicks "Prepare Package" → status = 'preparing' (Buyer sees "Preparing Package")
                          ↓
Seller clicks "Ready for Pickup" → status = 'pending' (Rider CAN NOW see)
```

**Files Changed**:
- `blueprints/checkout_order.py` - Initial status = NULL
- `blueprints/seller_product_management.py` - Added `/preparing` endpoint
- `database/supabase_helper.py` - Updated `get_pending_deliveries()`
- `templates/accounts/myAccount_purchases.html` - Added NULL status display

---

### 2. Pickup Timestamp Fix
**Problem**: `picked_up_at` was set when rider accepted delivery, not when actually picked up.

**Solution**: 
- Removed `picked_up_at` from `accept_delivery_supabase()`
- Only set `picked_up_at` in `mark_delivery_picked_up()` when rider clicks "Mark as Picked Up"

**Files Changed**:
- `database/supabase_helper.py` - Fixed `accept_delivery_supabase()`

---

### 3. Network Retry Logic
**Problem**: Network errors causing login failures.

**Solution**: Added automatic retry (up to 3 times, 1 second delay)
```python
def supabase_retry(func, max_retries=3, delay=1):
    # Retries network errors automatically
    # Does NOT retry validation/auth errors
```

**Files Changed**:
- `database/supabase_helper.py` - Added `supabase_retry()` function
- `blueprints/auth.py` - Applied retry to login queries

---

### 4. Seller Dashboard Status Fix
**Problem**: Dashboard used `deliveries.status` instead of `orders.order_status`.

**Solution**: Changed to use `orders.order_status` for consistency.

**Files Changed**:
- `templates/seller/seller_dashboard.html` - Updated status display

---

## 📊 Complete Order Flow

```
1. Buyer Places Order
   ├─ orders.order_status = 'pending'
   ├─ deliveries.status = NULL
   └─ Buyer sees: "Order Placed"

2. Seller Prepares Package
   ├─ deliveries.status = 'preparing'
   └─ Buyer sees: "Preparing Package"

3. Seller Marks Ready
   ├─ deliveries.status = 'pending'
   └─ Rider sees: Order in pickup list ✅

4. Rider Accepts
   ├─ deliveries.status = 'assigned'
   ├─ deliveries.rider_id = X
   └─ picked_up_at = NOT SET YET ⚠️

5. Rider Picks Up (at seller)
   ├─ deliveries.status = 'in_transit'
   ├─ deliveries.picked_up_at = NOW() ✅
   └─ Buyer sees: "In Transit"

6. Rider Delivers (at buyer)
   ├─ deliveries.status = 'delivered'
   ├─ deliveries.delivered_at = NOW()
   └─ Buyer sees: "Confirm Receipt" button

7. Buyer Confirms Receipt
   ├─ orders.order_received = TRUE
   ├─ orders.order_status = 'delivered'
   └─ Buyer can write review
```

---

## 🗄️ Key Database Tables

### orders
- `order_status`: pending, in_transit, delivered, cancelled
- `order_received`: boolean (buyer confirmation)

### deliveries
- `status`: NULL, preparing, pending, assigned, in_transit, delivered, cancelled
- `rider_id`: NULL until rider accepts
- `picked_up_at`: Set when rider picks up (NOT on accept)
- `delivered_at`: Set when rider delivers

### Status Priority
- Display: Use `deliveries.status` for tracking
- Overall: Use `orders.order_status` for order state

---

## 🔑 Important Rules

1. **Riders only see `status='pending'`** deliveries
2. **`picked_up_at` sets on pickup, NOT accept**
3. **Seller must take 2 actions**: Prepare → Ready
4. **Buyer confirms receipt** before writing reviews
5. **Network errors auto-retry** up to 3 times

---

## 📱 For Flutter Implementation

### Critical Queries

**Get Pending Deliveries (Rider)**:
```dart
final deliveries = await supabase
  .from('deliveries')
  .select('*, orders(*, buyers(*), sellers(*))')
  .eq('status', 'pending')
  .is_('rider_id', null);
```

**Get Buyer Orders**:
```dart
final orders = await supabase
  .from('orders')
  .select('*, deliveries(*), sellers(*)')
  .eq('buyer_id', buyerId)
  .order('created_at', ascending: false);
```

**Accept Delivery**:
```dart
await supabase
  .from('deliveries')
  .update({
    'rider_id': riderId,
    'status': 'assigned',
    // NO picked_up_at here!
  })
  .eq('delivery_id', deliveryId);
```

**Mark as Picked Up**:
```dart
await supabase
  .from('deliveries')
  .update({
    'status': 'in_transit',
    'picked_up_at': DateTime.now().toIso8601String(),
  })
  .eq('delivery_id', deliveryId);
```

### Status Display Logic

```dart
String getDeliveryStatusLabel(String? status) {
  switch (status) {
    case null:
      return 'Order Placed';
    case 'preparing':
      return 'Preparing Package';
    case 'pending':
      return 'Ready for Pickup';
    case 'assigned':
      return 'Rider Assigned';
    case 'in_transit':
      return 'In Transit';
    case 'delivered':
      return 'Delivered';
    case 'cancelled':
      return 'Cancelled';
    default:
      return status ?? 'Unknown';
  }
}
```

---

## 🚀 API Endpoints

### Seller
```
POST /api/orders/{order_id}/preparing
POST /api/orders/{order_id}/ready-for-pickup
```

### Rider
```
GET  /rider/pickup/api/pending-deliveries
POST /rider/pickup/api/accept-delivery
POST /rider/active-delivery/api/pickup-item
POST /rider/active-delivery/api/deliver-item
```

### Buyer
```
GET  /myAccount_purchases
POST /api/confirm_order_received/{order_id}
POST /place_order
```

---

## 📝 Testing Checklist

- [ ] Buyer places order → status = NULL
- [ ] Seller sees "Prepare Package" button
- [ ] Seller clicks "Prepare Package" → status = 'preparing'
- [ ] Buyer sees "Preparing Package"
- [ ] Rider does NOT see order yet
- [ ] Seller clicks "Ready for Pickup" → status = 'pending'
- [ ] Rider NOW sees order in pickup list
- [ ] Rider accepts → status = 'assigned', NO picked_up_at
- [ ] Rider marks picked up → status = 'in_transit', picked_up_at = NOW()
- [ ] Rider delivers → status = 'delivered', delivered_at = NOW()
- [ ] Buyer confirms receipt → order_received = TRUE

---

## 📚 Documentation Files

1. `FLUTTER_MOBILE_APP_REFERENCE.md` - Complete guide
2. `DELIVERY_FLOW_VERIFICATION.md` - Detailed flow explanation
3. `DELIVERY_FLOW_CHANGES.md` - Changes summary
4. `PICKUP_TIMESTAMP_FIX.md` - Timestamp fix details
5. `NETWORK_RETRY_LOGIC.md` - Retry implementation
6. `SELLER_DASHBOARD_STATUS_FIX.md` - Status fix details

---

**Last Updated**: April 9, 2026  
**GitHub**: https://github.com/jeem-31/ecommerce_velare  
**Docker**: Running on port 5000 ✅
