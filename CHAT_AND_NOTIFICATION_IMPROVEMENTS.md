# Chat and Notification System Improvements

## Overview
This document outlines the improvements made to the notification and chat systems to provide better user experience and reduce inbox clutter.

---

## Changes Implemented

### 1. Notify Both Buyer and Seller on "Ready for Pickup"

**Problem**: Only the buyer was notified when an order was marked as "Ready for Pickup".

**Solution**: Both buyer and seller now receive notifications when the seller marks an order as ready for pickup.

**Implementation** (`blueprints/seller_product_management.py`):
```python
# When seller marks order as ready for pickup:
# 1. Update delivery status to 'pending'
# 2. Create consolidated notification message
# 3. Send notification to BOTH buyer and seller
```

**Notification Details**:
- **Buyer receives**: "📦 Order Ready for Pickup - Order #VEL-2026-00001 is ready for pickup. Items: Product A (x2), Product B (x1)"
- **Seller receives**: "📦 Order Ready for Pickup - You marked Order #VEL-2026-00001 is ready for pickup. Items: Product A (x2), Product B (x1)"

---

### 2. Consolidate Multiple Products into Single Message

**Problem**: When a buyer orders multiple products, separate notifications were sent for each product, cluttering the inbox.

**Solution**: All products in an order are now consolidated into a single notification message.

**Implementation**:
```python
# Build consolidated message
if len(order_items) > 1:
    # Multiple products - consolidate
    product_list = []
    for item in order_items:
        product_list.append(f"{item['product_name']} (x{item['quantity']})")
    products_text = ", ".join(product_list)
    message = f"Order #{order_number} is ready for pickup. Items: {products_text}"
elif len(order_items) == 1:
    # Single product
    item = order_items[0]
    message = f"Order #{order_number} is ready for pickup. Item: {item['product_name']} (x{item['quantity']})"
```

**Example**:
- **Before**: 3 separate notifications for 3 products
- **After**: 1 notification: "Order #VEL-2026-00001 is ready for pickup. Items: Dress (x1), Shoes (x2), Bag (x1)"

---

### 3. Single Chat Thread per User Profile

**Problem**: The chat system created a new conversation for each delivery, resulting in multiple chat threads between the same rider and buyer. This made the inbox cluttered and confusing.

**Solution**: Conversations are now based on user profiles, not individual deliveries. One rider-buyer pair = one conversation thread, regardless of how many orders they have.

**Key Changes**:

#### A. Updated `create_conversation()` Function (`database/supabase_helper.py`)

**Before**:
- Created new conversation for each delivery
- Linked conversation to `delivery_id`
- Multiple threads for same rider-buyer pair

**After**:
```python
def create_conversation(buyer_id, seller_id, initial_message, rider_id=None, delivery_id=None):
    """
    Create a new conversation OR return existing conversation between the same parties.
    
    IMPORTANT: Conversations are now based on user profiles, NOT per delivery.
    - If a conversation already exists between rider and buyer, reuse it.
    - If a conversation already exists between seller and buyer, reuse it.
    - This prevents cluttered inboxes with multiple threads for the same people.
    """
    # Check if conversation already exists between these parties
    if rider_id and buyer_id:
        # Check for existing rider-buyer conversation (ignore delivery_id)
        existing = supabase.table('conversations')
            .select('conversation_id')
            .eq('rider_id', rider_id)
            .eq('buyer_id', buyer_id)
            .is_('seller_id', 'null')
            .execute()
        
        if existing.data:
            # Reuse existing conversation
            return existing.data[0]['conversation_id']
    
    # Create new conversation if none exists
    # NOTE: delivery_id is NOT stored anymore
```

**Benefits**:
- One conversation per rider-buyer pair
- All messages about different orders appear in the same thread
- Cleaner inbox
- Better conversation context

#### B. Updated Rider Chat API (`blueprints/rider_chat.py`)

**Changes**:

1. **GET `/rider/chat/api/conversations`**
   - Now fetches conversations from `conversations` table (not `deliveries`)
   - Shows all active deliveries for each buyer as context
   - Groups deliveries by buyer_id

2. **GET `/rider/chat/api/messages/<buyer_id>`** (changed from `<delivery_id>`)
   - Now accepts `buyer_id` instead of `delivery_id`
   - Fetches/creates conversation based on rider-buyer pair
   - All messages for all deliveries between these two users appear here

3. **POST `/rider/chat/api/send-message`**
   - Now accepts `buyer_id` instead of `delivery_id`
   - Sends message to the shared conversation thread

**Response Format** (GET conversations):
```json
{
  "success": true,
  "conversations": [
    {
      "conversation_id": 123,
      "buyer_id": 456,
      "contact_name": "Juan Dela Cruz",
      "contact_avatar": "/static/images/profile.jpg",
      "contact_phone": "09171234567",
      "active_deliveries": [
        {
          "delivery_id": 789,
          "order_number": "VEL-2026-00001",
          "shop_name": "Sample Shop",
          "status": "assigned",
          "address": "123 Main St"
        },
        {
          "delivery_id": 790,
          "order_number": "VEL-2026-00002",
          "shop_name": "Another Shop",
          "status": "in_transit",
          "address": "456 Oak Ave"
        }
      ],
      "context_message": "Active orders: VEL-2026-00001, VEL-2026-00002",
      "last_message": "I'm on my way!",
      "last_message_time": "2026-04-09 10:30:00",
      "unread_count": 2
    }
  ]
}
```

---

## Database Schema Changes

### conversations table
```sql
-- delivery_id is now OPTIONAL (nullable)
-- Conversations are identified by rider_id + buyer_id OR seller_id + buyer_id
-- No longer creating separate conversations per delivery

ALTER TABLE conversations
MODIFY COLUMN delivery_id INT NULL;

-- Add unique constraint to prevent duplicate conversations
-- (This should be done carefully to avoid breaking existing data)
```

**Note**: Existing conversations with `delivery_id` will continue to work, but new conversations will not use `delivery_id`.

---

## Migration Strategy

### For Existing Data

1. **Conversations**: Existing delivery-based conversations will continue to work
2. **New Conversations**: Will be profile-based (no delivery_id)
3. **Gradual Migration**: Old conversations will naturally phase out as they become inactive

### For Frontend/Mobile App

**Changes Required**:

1. **Rider Chat List**:
   - Group conversations by buyer (not by delivery)
   - Show active deliveries as context under each buyer
   - Display: "Active orders: VEL-2026-00001, VEL-2026-00002"

2. **Chat Messages**:
   - Change API call from `/messages/<delivery_id>` to `/messages/<buyer_id>`
   - Show all messages for this rider-buyer pair
   - Add delivery context in UI (e.g., "Regarding Order #VEL-2026-00001")

3. **Send Message**:
   - Change request body from `{"delivery_id": 123, "message": "..."}` 
   - To: `{"buyer_id": 456, "message": "..."}`

---

## Testing Checklist

### Notifications
- [ ] Seller marks order ready → Both buyer and seller receive notification
- [ ] Multiple products → Single consolidated notification
- [ ] Notification message includes all product names and quantities
- [ ] Notification appears in both buyer and seller notification lists

### Chat System
- [ ] Rider chats with buyer about Order A → Creates conversation
- [ ] Same rider chats with same buyer about Order B → Uses same conversation
- [ ] Conversation list shows all active deliveries for each buyer
- [ ] Messages are grouped by buyer, not by delivery
- [ ] Unread counts work correctly
- [ ] Old delivery-based conversations still accessible

### Edge Cases
- [ ] Rider has multiple deliveries for same buyer
- [ ] Buyer orders from multiple sellers (different conversations)
- [ ] Conversation exists, then new delivery assigned
- [ ] No active deliveries but conversation exists

---

## Benefits

### For Users
1. **Cleaner Inbox**: One conversation per person, not per order
2. **Better Context**: See all active orders in one place
3. **Easier Communication**: No need to switch between multiple threads
4. **Complete Notifications**: Both parties are informed of status changes

### For System
1. **Reduced Database Rows**: Fewer conversation records
2. **Better Performance**: Less data to query and display
3. **Simpler Logic**: Profile-based is more intuitive than delivery-based
4. **Scalability**: Works better as order volume grows

---

## API Changes Summary

### Modified Endpoints

| Endpoint | Before | After |
|----------|--------|-------|
| Get Messages | `GET /rider/chat/api/messages/<delivery_id>` | `GET /rider/chat/api/messages/<buyer_id>` |
| Send Message | `POST /rider/chat/api/send-message` with `delivery_id` | `POST /rider/chat/api/send-message` with `buyer_id` |
| Get Conversations | Returns delivery-based list | Returns profile-based list with delivery context |

### New Response Fields

**Conversations Response**:
- `active_deliveries`: Array of all active deliveries for this buyer
- `context_message`: Summary text like "Active orders: VEL-2026-00001, VEL-2026-00002"
- `buyer_id`: Direct buyer ID (no need to look up from delivery)

---

## Code Files Modified

1. **blueprints/seller_product_management.py**
   - `mark_order_ready_for_pickup()`: Added notifications for both buyer and seller with consolidated product list

2. **database/supabase_helper.py**
   - `create_conversation()`: Check for existing conversation, reuse if found

3. **blueprints/rider_chat.py**
   - `get_rider_conversations_api()`: Fetch profile-based conversations with delivery context
   - `get_buyer_messages()`: Changed from `get_delivery_messages()`, accepts buyer_id
   - `send_rider_message()`: Changed to accept buyer_id instead of delivery_id

---

## Future Enhancements

1. **Conversation Archiving**: Archive conversations when all deliveries are completed
2. **Message Search**: Search messages across all conversations
3. **Delivery Tags**: Tag messages with specific order numbers for reference
4. **Push Notifications**: Real-time push notifications for new messages
5. **Read Receipts**: Show when messages are read by the other party
6. **Typing Indicators**: Show when the other person is typing

---

## Rollback Plan

If issues arise, rollback steps:

1. Revert `create_conversation()` to create delivery-based conversations
2. Revert rider chat endpoints to use `delivery_id`
3. Revert notification changes (remove seller notification)
4. Database: No schema changes were made, so no rollback needed

---

## Summary

These improvements make the notification and chat systems more user-friendly and efficient:

✅ Both buyer and seller are notified when orders are ready for pickup
✅ Multiple products are consolidated into single notifications
✅ One chat thread per user profile (not per delivery)
✅ Cleaner inbox with better conversation context
✅ Easier to track multiple orders with the same person

The changes maintain backward compatibility while providing a better user experience going forward.
