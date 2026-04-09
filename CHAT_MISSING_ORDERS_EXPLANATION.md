# Why Some Orders Are Missing from Chat

## Problem
Order #14 (and possibly others) are not showing in the rider chat conversation list.

## Reason
The chat system now only shows **ACTIVE** deliveries with status:
- ✅ `'assigned'` - Rider accepted, going to pick up
- ✅ `'in_transit'` - Rider picked up, delivering

## Orders NOT Shown:
- ❌ `status = NULL` - Order just placed, seller hasn't prepared
- ❌ `status = 'preparing'` - Seller is preparing
- ❌ `status = 'pending'` - Ready for pickup but not assigned to THIS rider
- ❌ `status = 'delivered'` - Already completed
- ❌ `status = 'cancelled'` - Cancelled

## How to Check Order #14 Status

### Option 1: Check in Database
```sql
SELECT order_id, order_number, status 
FROM deliveries 
WHERE order_id = 14;
```

### Option 2: Check in Rider Dashboard
1. Go to Delivery Management
2. Look for Order #14
3. Check its status

## Possible Reasons Order #14 is Missing:

1. **Already Delivered** - Status is 'delivered', so it's removed from active chat
2. **Not Assigned to This Rider** - Another rider has it
3. **Still Pending** - Seller marked it ready but this rider hasn't accepted it yet
4. **Cancelled** - Order was cancelled

## Solution

### If Order #14 Should Be Shown:
Check the delivery status and make sure it's either:
- `'assigned'` AND `rider_id` matches current rider
- `'in_transit'` AND `rider_id` matches current rider

### To See All Orders (Including Delivered):
Change the query in `blueprints/rider_chat.py` line ~60:

**Current** (Active only):
```python
.in_('status', ['assigned', 'in_transit'])
```

**To Show All** (Including delivered):
```python
.in_('status', ['assigned', 'in_transit', 'delivered'])
```

But this is NOT recommended because it will clutter the chat with old orders.

---

## About Order Context in Messages

### Current Implementation:
- Order context is shown in the **conversation header**
- Format: `📦 VEL-2026-00008 • 🚚 VEL-2026-00014`
- Shows ALL active orders for that buyer

### Why Not Per Message:
The `messages` table doesn't have an `order_id` column, so we can't link individual messages to specific orders.

### To Add Order Context Per Message:
Would need to:
1. Add `order_id` column to `messages` table
2. Update `insert_message()` to accept order_id
3. Update frontend to show order badge on each message

**SQL Migration Needed**:
```sql
ALTER TABLE messages ADD COLUMN order_id INT NULL;
ALTER TABLE messages ADD FOREIGN KEY (order_id) REFERENCES orders(order_id);
```

---

## Summary

**Order #14 is missing because**:
- It's probably not in 'assigned' or 'in_transit' status
- OR it's not assigned to the current rider
- OR it's already delivered

**Order context is shown**:
- ✅ In conversation header (all active orders)
- ❌ Not per message (would need database changes)

Check the delivery status of Order #14 to confirm why it's not showing.
