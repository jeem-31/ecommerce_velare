# Rider Chat Logic Documentation

## Overview
Ang rider chat system ay nagbibigay ng direct communication channel sa pagitan ng rider at buyer tungkol sa specific delivery. Ang chat ay naka-link sa `delivery_id` at available lang para sa active deliveries.

---

## Current Implementation

### Key Features
- Riders can chat with buyers about specific deliveries
- Each conversation is linked to a `delivery_id`
- Chat is available for deliveries with status: `'assigned'`, `'in_transit'`, `'delivered'`
- Auto-creates conversation with initial greeting message when first accessed
- Tracks unread counts separately for buyer and rider
- Shows delivery context (order number, shop name, delivery address)

---

## Database Schema

### Tables Used

#### 1. conversations
```sql
- conversation_id (PK)
- buyer_id (FK → buyers.buyer_id)
- seller_id (FK → sellers.seller_id, nullable for rider-buyer chats)
- rider_id (FK → riders.rider_id)
- delivery_id (FK → deliveries.delivery_id)
- last_message (text)
- last_message_time (timestamp)
- buyer_unread_count (integer)
- seller_unread_count (integer)
- rider_unread_count (integer)
- created_at (timestamp)
```

#### 2. messages
```sql
- message_id (PK)
- conversation_id (FK → conversations.conversation_id)
- sender_type (text: 'buyer', 'seller', 'rider')
- sender_id (integer: user_id ng sender)
- message_text (text)
- is_read (boolean)
- created_at (timestamp)
```

#### 3. deliveries (for context)
```sql
- delivery_id (PK)
- order_id (FK)
- rider_id (FK)
- status (text)
- delivery_address (text)
- assigned_at (timestamp)
```

---

## API Endpoints

### 1. GET `/rider/chat`
**Purpose**: Main chat page for riders

**Authentication**: Requires `session['user_type'] == 'rider'`

**Returns**: Renders `rider/rider_chat.html` with rider data

**Flow**:
1. Check if user is logged in as rider
2. Get rider information from database
3. Render chat interface

---

### 2. GET `/rider/chat/api/conversations`
**Purpose**: Get all conversations for the logged-in rider

**Authentication**: Requires `session['user_type'] == 'rider'`

**Query Logic**:
```python
# Get deliveries assigned to rider with status: assigned, in_transit, delivered
supabase.table('deliveries')
  .select('order_id, delivery_id, status, delivery_address, assigned_at, orders(...)')
  .eq('rider_id', rider_id)
  .in_('status', ['assigned', 'in_transit', 'delivered'])
  .order('assigned_at', desc=True)
  .limit(50)
```

**Response Format**:
```json
{
  "success": true,
  "conversations": [
    {
      "conversation_id": "delivery_123",
      "delivery_id": 123,
      "order_id": 456,
      "order_number": "VEL-2026-00001",
      "contact_id": 789,
      "contact_name": "Juan Dela Cruz",
      "contact_avatar": "/static/images/profile.jpg",
      "contact_phone": "09171234567",
      "seller_shop": "Sample Shop",
      "delivery_status": "assigned",
      "delivery_address": "123 Main St, City",
      "last_message": "Delivery for Order #VEL-2026-00001",
      "last_message_time": "2026-04-09 10:30:00",
      "unread_count": 0,
      "contact_type": "buyer"
    }
  ]
}
```

---

### 3. GET `/rider/chat/api/messages/<delivery_id>`
**Purpose**: Get all messages for a specific delivery

**Authentication**: Requires `session['user_type'] == 'rider'`

**Flow**:
1. Verify rider owns the delivery
2. Get delivery and order information
3. Check if conversation exists
4. If NO conversation:
   - Create new conversation
   - Insert initial greeting message:
     ```
     "Hi! I'm your rider for Order #[ORDER_NUMBER] from [SHOP_NAME]. 
     I'll keep you updated on your delivery."
     ```
5. If conversation exists, get all messages
6. Mark messages as read for rider
7. Return formatted messages

**Response Format**:
```json
{
  "success": true,
  "messages": [
    {
      "message_id": 1,
      "sender_id": 123,
      "sender_type": "rider",
      "message_text": "Hi! I'm your rider...",
      "is_read": true,
      "created_at": "2026-04-09 10:30:00"
    }
  ]
}
```

---

### 4. POST `/rider/chat/api/send-message`
**Purpose**: Send a message from rider to buyer

**Authentication**: Requires `session['user_type'] == 'rider'`

**Request Body**:
```json
{
  "delivery_id": 123,
  "message": "I'm on my way to pick up your order!"
}
```

**Flow**:
1. Verify rider owns the delivery
2. Get buyer_id from delivery
3. Get or create conversation
4. Insert message with `sender_type='rider'`
5. Update conversation's `last_message` and `last_message_time`
6. Increment `buyer_unread_count`

**Response Format**:
```json
{
  "success": true,
  "message": {
    "message_id": 456,
    "sender_id": 123,
    "sender_type": "rider",
    "message_text": "I'm on my way...",
    "created_at": "2026-04-09T10:30:00Z",
    "is_read": false
  }
}
```

---

## Conversation Flow

### Scenario: Rider accepts delivery and wants to chat with buyer

1. **Rider accepts delivery**
   - Delivery status changes to `'assigned'`
   - Rider can now see this delivery in their chat list

2. **Rider opens chat page**
   - GET `/rider/chat` → Loads chat interface
   - GET `/rider/chat/api/conversations` → Shows list of active deliveries

3. **Rider clicks on a conversation**
   - GET `/rider/chat/api/messages/<delivery_id>`
   - If first time: Auto-creates conversation with greeting message
   - Shows all messages in the conversation

4. **Rider sends message**
   - POST `/rider/chat/api/send-message`
   - Message saved with `sender_type='rider'`
   - Buyer's unread count increments
   - Buyer will see notification (if implemented)

5. **Buyer replies** (from buyer's chat interface)
   - Message saved with `sender_type='buyer'`
   - Rider's unread count increments
   - Rider sees new message in real-time (if polling/websocket implemented)

6. **Delivery completes**
   - Status changes to `'delivered'`
   - Chat remains accessible for reference
   - Conversation stays in history

---

## Important Rules

### When Chat is Available
- Delivery status MUST be: `'assigned'`, `'in_transit'`, or `'delivered'`
- Rider MUST be assigned to the delivery (`deliveries.rider_id` matches logged-in rider)
- Buyer MUST be the order owner (`orders.buyer_id`)

### When Chat is NOT Available
- Delivery status is `NULL`, `'preparing'`, or `'pending'` (not yet assigned to rider)
- Delivery is `'cancelled'`
- Rider is not assigned to the delivery

### Conversation Creation
- Conversation is created automatically when rider first opens chat for a delivery
- Initial greeting message is sent automatically
- One conversation per delivery (unique constraint on `delivery_id`)

### Unread Count Management
- When rider sends message → `buyer_unread_count++`
- When buyer sends message → `rider_unread_count++`
- When rider opens chat → `rider_unread_count = 0` (mark as read)
- When buyer opens chat → `buyer_unread_count = 0` (mark as read)

---

## Helper Functions Used (from supabase_helper.py)

```python
# Get rider by user_id
get_rider_by_user_id(user_id)

# Conversation management
create_conversation(buyer_id, seller_id, initial_message, rider_id, delivery_id)
update_conversation_last_message(conversation_id, message_text)
get_conversation_messages(conversation_id)

# Message management
insert_message(conversation_id, sender_type, sender_id, message_text)
mark_messages_as_read_rider(conversation_id)

# Unread count management
increment_buyer_unread_count(conversation_id)
increment_rider_unread_count(conversation_id)

# Data cleaning
clean_supabase_data(data)
fix_image_urls_in_data(data)
```

---

## Frontend Implementation Notes

### Chat Interface Components
1. **Conversation List** (left sidebar)
   - Shows all active deliveries
   - Displays buyer name, avatar, order number
   - Shows delivery status and address
   - Highlights unread conversations

2. **Message Thread** (main area)
   - Shows all messages for selected delivery
   - Displays sender type (rider/buyer)
   - Shows timestamps
   - Auto-scrolls to latest message

3. **Message Input** (bottom)
   - Text input for new message
   - Send button
   - Character limit (optional)

### Real-time Updates (Future Enhancement)
- Currently uses polling or manual refresh
- Can be upgraded to WebSocket for real-time messaging
- Can add push notifications for new messages

---

## Flutter Mobile App Integration

### API Calls Needed

#### 1. Get Conversations
```dart
GET /rider/chat/api/conversations
Headers: Cookie with session
```

#### 2. Get Messages
```dart
GET /rider/chat/api/messages/{delivery_id}
Headers: Cookie with session
```

#### 3. Send Message
```dart
POST /rider/chat/api/send-message
Headers: Cookie with session
Body: {
  "delivery_id": 123,
  "message": "Message text"
}
```

### Flutter Implementation Tips

```dart
// Model for Conversation
class RiderConversation {
  final String conversationId;
  final int deliveryId;
  final int orderId;
  final String orderNumber;
  final String contactName;
  final String contactAvatar;
  final String contactPhone;
  final String sellerShop;
  final String deliveryStatus;
  final String deliveryAddress;
  final String lastMessage;
  final String lastMessageTime;
  final int unreadCount;
}

// Model for Message
class ChatMessage {
  final int messageId;
  final int senderId;
  final String senderType; // 'rider' or 'buyer'
  final String messageText;
  final bool isRead;
  final String createdAt;
}

// Service for Chat API
class RiderChatService {
  Future<List<RiderConversation>> getConversations() async {
    // Call GET /rider/chat/api/conversations
  }
  
  Future<List<ChatMessage>> getMessages(int deliveryId) async {
    // Call GET /rider/chat/api/messages/{deliveryId}
  }
  
  Future<ChatMessage> sendMessage(int deliveryId, String message) async {
    // Call POST /rider/chat/api/send-message
  }
}
```

### UI Recommendations
- Use ListView for conversation list
- Use ListView.builder for messages (reverse order for chat)
- Implement pull-to-refresh for new messages
- Add loading indicators
- Show delivery context at top of chat (order number, shop, address)
- Different message bubble colors for rider vs buyer
- Show timestamps
- Add "typing..." indicator (future enhancement)

---

## Testing Checklist

### Backend Testing
- [ ] Rider can see only their assigned deliveries
- [ ] Conversation auto-creates on first message
- [ ] Initial greeting message is sent
- [ ] Messages are saved correctly
- [ ] Unread counts increment properly
- [ ] Messages marked as read when opened
- [ ] Unauthorized access is blocked
- [ ] Error handling works for invalid delivery_id

### Frontend Testing
- [ ] Conversation list loads correctly
- [ ] Messages display in correct order
- [ ] Sender type is visually distinct
- [ ] Timestamps are formatted correctly
- [ ] Send button works
- [ ] Empty message is blocked
- [ ] Loading states are shown
- [ ] Error messages are displayed
- [ ] Profile images load correctly
- [ ] Delivery context is visible

### Integration Testing
- [ ] Rider sends message → Buyer receives
- [ ] Buyer sends message → Rider receives
- [ ] Unread count updates in real-time
- [ ] Chat persists after delivery completion
- [ ] Multiple conversations work independently

---

## Summary

Ang rider chat system ay simple pero effective na paraan para makipag-communicate ang rider sa buyer tungkol sa delivery. Ang key points ay:

1. **One conversation per delivery** - Bawat delivery may sariling chat thread
2. **Auto-initialization** - Automatic na lumilikha ng conversation with greeting message
3. **Status-based access** - Available lang kung assigned, in_transit, or delivered
4. **Unread tracking** - May separate unread count para sa buyer at rider
5. **Delivery context** - Makikita ang order number, shop name, at delivery address

Ang implementation ay straightforward at madaling i-integrate sa Flutter mobile app gamit ang existing API endpoints.
