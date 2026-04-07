# Pickup Timestamp Fix

## Issue
When rider clicks "Accept" on a delivery in the pickup list, the `picked_up_at` timestamp was being set immediately. This is incorrect.

## Correct Behavior
- `picked_up_at` should ONLY be set when rider clicks "Mark as Picked Up" after going to the seller's location
- When rider clicks "Accept", only `rider_id` and `status='assigned'` should be set

## Fix Applied

### File: `database/supabase_helper.py`

**Function**: `accept_delivery_supabase()` (line 765-785)

**Before**:
```python
response = supabase.table('deliveries').update({
    'rider_id': rider_id,
    'status': 'assigned',
    'picked_up_at': datetime.now().isoformat()  # ❌ WRONG - sets timestamp on accept
}).eq('delivery_id', delivery_id).execute()
```

**After**:
```python
response = supabase.table('deliveries').update({
    'rider_id': rider_id,
    'status': 'assigned'
    # ✅ CORRECT - NO picked_up_at here
}).eq('delivery_id', delivery_id).execute()
```

## Timeline

### Correct Flow:

1. **Rider Accepts Delivery** (from pickup list)
   - Sets: `rider_id`, `status='assigned'`
   - Does NOT set: `picked_up_at`
   - Delivery moves to "Active Delivery" page

2. **Rider Goes to Seller Location**
   - Rider clicks "Mark as Picked Up"
   - Calls: `mark_delivery_picked_up(delivery_id)`
   - Sets: `status='in_transit'`, `picked_up_at=NOW()`
   - ✅ This is when `picked_up_at` is recorded

3. **Rider Delivers Package**
   - Rider clicks "Mark as Delivered"
   - Calls: `mark_delivery_delivered(delivery_id)`
   - Sets: `status='delivered'`, `delivered_at=NOW()`

## Verification

The `mark_delivery_picked_up()` function (line 824-842) correctly sets `picked_up_at`:

```python
def mark_delivery_picked_up(delivery_id):
    """Mark a delivery as picked up (rider has collected the package from seller)"""
    response = supabase.table('deliveries').update({
        'status': 'in_transit',
        'picked_up_at': datetime.now().isoformat()  # ✅ CORRECT - sets on actual pickup
    }).eq('delivery_id', delivery_id).execute()
```

## Status

✅ **FIXED** - `picked_up_at` now only sets when rider marks as picked up, not on accept.
