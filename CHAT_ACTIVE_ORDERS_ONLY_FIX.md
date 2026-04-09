# Fix: Show Only Active Orders in Rider Chat

## Problem
1. ❌ Old/completed orders (VEL-2025-0001, etc.) still showing in chat
2. ❌ Need to show which order is being discussed in messages

## Solution

### 1. Show Only Active Deliveries (assigned, in_transit)

**Changed in `blueprints/rider_chat.py`**:

**Before**:
```python
.in_('status', ['assigned', 'in_transit', 'delivered'])
```

**After**:
```python
.in_('status', ['assigned', 'in_transit'])  # ONLY active, NOT delivered
```

**Result**:
- ✅ Only shows orders that are currently active
- ✅ Delivered orders are automatically removed from list
- ✅ No more old orders cluttering the chat

---

### 2. Better Context Display with Status Emojis

**Changed in `blueprints/rider_chat.py`**:

**Before**:
```python
context_message = f"Active orders: {', '.join(order_numbers)}"
```

**After**:
```python
# Show order with status emoji
order_details = []
for d in buyer_data['deliveries']:
    status_emoji = '📦' if d['status'] == 'assigned' else '🚚'
    order_details.append(f"{status_emoji} {d['order_number']}")
context_message = " • ".join(order_details)
```

**Result**:
- ✅ Shows status with emoji
- 📦 = Assigned (waiting for pickup)
- 🚚 = In Transit (on the way)

---

## Example Display

### Conversation List:
```
jojie mon
Start conversation
📦 VEL-2026-00001 • 🚚 VEL-2026-00003
```

### Chat Header:
```
jojie mon
📦 VEL-2026-00001 • 🚚 VEL-2026-00003
```

---

## What Gets Filtered Out

### NOT Shown:
- ❌ `status = NULL` (order just placed, seller hasn't prepared yet)
- ❌ `status = 'preparing'` (seller is preparing, not ready for pickup)
- ❌ `status = 'pending'` (ready for pickup but not assigned to this rider)
- ❌ `status = 'delivered'` (already completed)
- ❌ `status = 'cancelled'` (cancelled orders)

### Shown:
- ✅ `status = 'assigned'` (rider accepted, going to pick up) 📦
- ✅ `status = 'in_transit'` (rider picked up, delivering) 🚚

---

## Delivery Status Flow

```
NULL → preparing → pending → assigned → in_transit → delivered
                              ↑         ↑
                              📦        🚚
                              SHOWN IN CHAT
```

---

## Testing

1. **Login as Rider**
2. **Accept a delivery** (status becomes 'assigned')
3. **Go to Chat** - Should see buyer with 📦 order number
4. **Mark as Picked Up** (status becomes 'in_transit')
5. **Refresh Chat** - Should see 🚚 order number
6. **Mark as Delivered** (status becomes 'delivered')
7. **Refresh Chat** - Buyer should disappear from list (no active orders)

---

## Benefits

✅ **Cleaner List**: Only active orders shown
✅ **Clear Status**: Emoji shows if waiting for pickup or in transit
✅ **Auto-Cleanup**: Delivered orders automatically removed
✅ **No Confusion**: Old orders don't clutter the chat

---

## Files Modified

1. **blueprints/rider_chat.py**
   - Line ~60: Changed status filter to `['assigned', 'in_transit']`
   - Line ~160: Added status emoji to context message

---

## Summary

Nag-filter na lang ng active deliveries (assigned at in_transit) at nag-add ng emoji para makita agad ang status. Ang delivered orders ay automatic na nawawala sa list. Mas clean na ngayon! 🎉
