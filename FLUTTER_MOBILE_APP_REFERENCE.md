# Velare E-Commerce - Mobile App Development Reference

## Overview
This document provides a comprehensive guide for implementing the Velare E-Commerce mobile app in Flutter, based on the web application's current implementation.

---

## Table of Contents
1. [Database Schema](#database-schema)
2. [Order & Delivery Flow](#order--delivery-flow)
3. [User Roles & Permissions](#user-roles--permissions)
4. [API Endpoints](#api-endpoints)
5. [Status Management](#status-management)
6. [Rider Chat System](#rider-chat-system)
7. [Key Features](#key-features)
8. [Important Notes](#important-notes)

---

## Database Schema

### Main Tables

#### 1. **users** (Authentication)
```sql
- user_id (PK)
- email
- password (plain text - consider hashing for mobile)
- user_type (buyer, seller, rider, admin)
- status (active, pending, suspended, banned)
- created_at
```

#### 2. **buyers**
```sql
- buyer_id (PK)
- user_id (FK → users)
- first_name
- last_name
- phone_number
- profile_image
- address, city, province, postal_code
```

#### 3. **sellers**
```sql
- seller_id (PK)
- user_id (FK → users)
- shop_name
- shop_logo
- first_name, last_name
- phone_number
- address, city, province, postal_code
```

#### 4. **riders**
```sql
- rider_id (PK)
- user_id (FK → users)
- first_name, last_name
- phone_number
- profile_image
- vehicle_type
- driver_license_file_path
- orcr_file_path
- status (available, busy)
```

#### 5. **orders** (Main Order Table)
```sql
- order_id (PK)
- order_number (e.g., VEL-2026-0001)
- buyer_id (FK → buyers)
- seller_id (FK → sellers)
- address_id (FK → addresses)
- subtotal
- shipping_fee
- discount_amount
- total_amount
- commission_amount (5% of subtotal)
- voucher_id (FK → vouchers, nullable)
- order_status (pending, in_transit, delivered, cancelled)
- order_received (boolean - buyer confirmation)
- created_at
- updated_at
```

#### 6. **deliveries** (Delivery Tracking)
```sql
- delivery_id (PK)
- order_id (FK → orders)
- rider_id (FK → riders, nullable)
- pickup_address (seller's address)
- delivery_address (buyer's address)
- delivery_fee
- paid_by_platform (boolean - free shipping voucher)
- status (NULL, preparing, pending, assigned, in_transit, delivered, cancelled)
- assigned_at
- picked_up_at
- delivered_at
- created_at
```

#### 7. **order_items**
```sql
- order_item_id (PK)
- order_id (FK → orders)
- product_id (FK → products)
- product_name
- materials
- variant_color
- variant_size
- quantity
- unit_price
- subtotal
```

#### 8. **products**
```sql
- product_id (PK)
- seller_id (FK → sellers)
- product_name
- description
- materials
- price
- category
- rating (average)
- total_reviews
- total_sold
- is_active (boolean)
- created_at
```

#### 9. **product_variants**
```sql
- variant_id (PK)
- product_id (FK → products)
- color
- size
- stock_quantity
- image_url
- hex_code (color hex)
```

#### 10. **addresses**
```sql
- address_id (PK)
- user_type (buyer, seller)
- user_ref_id (buyer_id or seller_id)
- full_address
- city
- province
- postal_code
- is_default (boolean)
```

---

## Order & Delivery Flow

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Buyer Places Order                                     │
├─────────────────────────────────────────────────────────────────┤
│ Tables Updated:                                                 │
│   - orders: INSERT (order_status = 'pending')                  │
│   - deliveries: INSERT (status = NULL)                         │
│   - order_items: INSERT (all items)                            │
│   - product_variants: UPDATE (stock_quantity -= quantity)      │
│   - products: UPDATE (total_sold += quantity)                  │
│   - cart: DELETE (remove purchased items)                      │
│                                                                 │
│ Buyer sees: "Order Placed"                                     │
│ Seller sees: "Prepare Package" button                          │
│ Rider sees: NOTHING                                            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Seller Clicks "Prepare Package"                        │
├─────────────────────────────────────────────────────────────────┤
│ API: POST /api/orders/{order_id}/preparing                     │
│                                                                 │
│ Tables Updated:                                                 │
│   - deliveries: UPDATE (status = 'preparing')                  │
│                                                                 │
│ Buyer sees: "Preparing Package"                                │
│ Seller sees: "Ready for Pickup" button                         │
│ Rider sees: NOTHING                                            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Seller Clicks "Ready for Pickup"                       │
├─────────────────────────────────────────────────────────────────┤
│ API: POST /api/orders/{order_id}/ready-for-pickup              │
│                                                                 │
│ Tables Updated:                                                 │
│   - deliveries: UPDATE (status = 'pending')                    │
│                                                                 │
│ Buyer sees: "Pending Shipment"                                 │
│ Seller sees: "Waiting for Rider"                               │
│ Rider sees: ✅ Order appears in "List for Pickup"              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Rider Accepts Delivery                                 │
├─────────────────────────────────────────────────────────────────┤
│ API: POST /rider/pickup/api/accept-delivery                    │
│                                                                 │
│ Tables Updated:                                                 │
│   - deliveries: UPDATE (status = 'assigned', rider_id = X)     │
│   - riders: UPDATE (status = 'busy')                           │
│                                                                 │
│ Buyer sees: "Pending Shipment"                                 │
│ Seller sees: "Rider Assigned"                                  │
│ Rider sees: Moved to "Active Delivery"                         │
│                                                                 │
│ ⚠️ NOTE: picked_up_at is NOT set yet                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Rider Picks Up Package (at seller location)            │
├─────────────────────────────────────────────────────────────────┤
│ API: POST /rider/active-delivery/api/pickup-item               │
│                                                                 │
│ Tables Updated:                                                 │
│   - deliveries: UPDATE (status = 'in_transit',                 │
│                         picked_up_at = NOW())                  │
│                                                                 │
│ Buyer sees: "In Transit" + "Rider is on the way..."            │
│ Seller sees: "In Transit"                                      │
│ Rider sees: "Mark as Delivered" button                         │
│                                                                 │
│ ✅ picked_up_at timestamp is set HERE                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Rider Delivers Package (at buyer location)             │
├─────────────────────────────────────────────────────────────────┤
│ API: POST /rider/active-delivery/api/deliver-item              │
│                                                                 │
│ Tables Updated:                                                 │
│   - deliveries: UPDATE (status = 'delivered',                  │
│                         delivered_at = NOW())                  │
│   - riders: UPDATE (status = 'available')                      │
│                                                                 │
│ Buyer sees: "Delivered" + "Confirm Receipt" button             │
│ Seller sees: "Delivered"                                       │
│ Rider sees: Delivery completed                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: Buyer Confirms Receipt                                 │
├─────────────────────────────────────────────────────────────────┤
│ API: POST /api/confirm_order_received/{order_id}               │
│                                                                 │
│ Tables Updated:                                                 │
│   - orders: UPDATE (order_received = TRUE,                     │
│                     order_status = 'delivered')                │
│                                                                 │
│ Buyer sees: "Write a Review" button                            │
│ Seller sees: Order completed                                   │
│ Rider sees: Delivery completed                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## User Roles & Permissions

### 1. Buyer
**Can:**
- Browse products
- Add to cart
- Place orders
- View order history
- Track deliveries
- Confirm receipt
- Write reviews
- Manage addresses
- Use vouchers
- Report users

**Cannot:**
- See orders before placing
- Cancel after rider picks up
- Access seller/rider features

### 2. Seller
**Can:**
- Manage products (add, edit, archive)
- View orders
- Mark "Prepare Package"
- Mark "Ready for Pickup"
- View sales reports
- Manage vouchers
- View customer feedback
- Report users

**Cannot:**
- Cancel orders after rider accepts
- See rider location
- Directly contact riders

### 3. Rider
**Can:**
- View available pickups (status='pending')
- Accept deliveries
- Mark as picked up
- Mark as delivered
- View earnings
- Update profile
- Report users

**Cannot:**
- See orders before seller marks ready
- Cancel after picking up
- Access buyer/seller features

### 4. Admin
**Can:**
- Manage all users
- Approve accounts
- View all orders
- Manage vouchers
- View reports
- Handle disputes
- Manage payouts

---

## API Endpoints

### Authentication
```
POST /login
POST /register_buyer
POST /register_seller
POST /register_rider
POST /logout
```

### Buyer Endpoints
```
GET  /myAccount_purchases
GET  /api/get_order_reviews/{order_id}
POST /api/submit_review
POST /api/confirm_order_received/{order_id}
POST /api/cancel_order/{order_id}
GET  /checkout?cart_ids=[]
POST /place_order
```

### Seller Endpoints
```
GET  /seller/dashboard
GET  /seller/product-management
GET  /api/orders (list seller orders)
POST /api/orders/{order_id}/preparing
POST /api/orders/{order_id}/ready-for-pickup
GET  /api/products/sold
```

### Rider Endpoints
```
GET  /rider/pickup
GET  /rider/pickup/api/pending-deliveries
POST /rider/pickup/api/accept-delivery
GET  /rider/active-delivery
GET  /rider/active-delivery/api/active-deliveries
POST /rider/active-delivery/api/pickup-item
POST /rider/active-delivery/api/deliver-item
```

### Product Endpoints
```
GET  /browse_product
GET  /view_item/{product_id}
GET  /view_shop/{seller_id}
GET  /api/featured-products
```

---

## Status Management

### Order Status (`orders.order_status`)
Used for: Overall order state

| Value | Display | When Set |
|-------|---------|----------|
| `pending` | Pending | Order placed |
| `in_transit` | In Transit | (Not used - use delivery_status) |
| `delivered` | Delivered | Buyer confirms receipt |
| `cancelled` | Cancelled | Order cancelled |

### Delivery Status (`deliveries.status`)
Used for: Delivery tracking

| Value | Display | When Set | Visible To |
|-------|---------|----------|------------|
| `NULL` | Order Placed | Order placed | Buyer, Seller |
| `preparing` | Preparing Package | Seller clicks "Prepare" | Buyer, Seller |
| `pending` | Ready for Pickup | Seller clicks "Ready" | Buyer, Seller, Rider |
| `assigned` | Rider Assigned | Rider accepts | All |
| `in_transit` | In Transit | Rider picks up | All |
| `delivered` | Delivered | Rider delivers | All |
| `cancelled` | Cancelled | Order cancelled | All |

### Important Rules:
1. **Riders only see deliveries with `status='pending'`**
2. **`picked_up_at` is set when rider marks as picked up, NOT on accept**
3. **`delivered_at` is set when rider marks as delivered**
4. **Buyer must confirm receipt to write reviews**

---

## Rider Chat System

### Overview
Riders can communicate directly with buyers through a profile-based chat system. Each rider-buyer pair has ONE conversation thread, regardless of how many deliveries they have together.

### Key Changes (April 2026)
- **Profile-Based Conversations**: One conversation per rider-buyer pair (not per delivery)
- **Consolidated Messages**: All messages about different orders appear in the same thread
- **Delivery Context**: Active deliveries are shown as context in the conversation list
- **Cleaner Inbox**: No more multiple threads for the same people

### Database Tables

#### conversations
```sql
- conversation_id (PK)
- buyer_id (FK)
- seller_id (FK, nullable)
- rider_id (FK, nullable)
- delivery_id (FK, nullable - DEPRECATED, not used for new conversations)
- last_message (text)
- last_message_time (timestamp)
- buyer_unread_count (integer)
- seller_unread_count (integer)
- rider_unread_count (integer)
- created_at (timestamp)
```

**Important**: New conversations do NOT use `delivery_id`. Conversations are identified by `rider_id + buyer_id` or `seller_id + buyer_id`.

#### messages
```sql
- message_id (PK)
- conversation_id (FK)
- sender_type (text: 'buyer', 'seller', 'rider')
- sender_id (integer: user_id)
- message_text (text)
- is_read (boolean)
- created_at (timestamp)
```

### Chat Availability Rules
- Chat is available when rider has active deliveries with buyer (status: `'assigned'`, `'in_transit'`, `'delivered'`)
- Conversation persists even after all deliveries are completed
- One conversation thread per rider-buyer pair
- All messages about different orders appear in the same thread

### API Endpoints for Rider Chat

#### 1. Get Rider Conversations
```
GET /rider/chat/api/conversations
```

**Response:**
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

#### 2. Get Messages for Buyer (Profile-Based)
```
GET /rider/chat/api/messages/<buyer_id>
```

**Note**: Changed from `<delivery_id>` to `<buyer_id>` for profile-based conversations.

**Response:**
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

#### 3. Send Message
```
POST /rider/chat/api/send-message
Body: {
  "buyer_id": 456,
  "message": "I'm on my way!"
}
```

**Note**: Changed from `delivery_id` to `buyer_id`.

**Response:**
```json
{
  "success": true,
  "message": {
    "message_id": 789,
    "sender_id": 123,
    "sender_type": "rider",
    "message_text": "I'm on my way!",
    "created_at": "2026-04-09T10:30:00Z",
    "is_read": false
  }
}
```

### Flutter Implementation Example

```dart
// Model
class RiderConversation {
  final int conversationId;
  final int buyerId;
  final String contactName;
  final String contactAvatar;
  final List<ActiveDelivery> activeDeliveries;
  final String contextMessage;
  final int unreadCount;
}

class ActiveDelivery {
  final int deliveryId;
  final String orderNumber;
  final String shopName;
  final String status;
  final String address;
}

class ChatMessage {
  final int messageId;
  final String senderType; // 'rider' or 'buyer'
  final String messageText;
  final bool isRead;
  final DateTime createdAt;
}

// Service
class RiderChatService {
  Future<List<RiderConversation>> getConversations() async {
    final response = await http.get('/rider/chat/api/conversations');
    // Parse and return conversations with active deliveries
  }
  
  Future<List<ChatMessage>> getMessages(int buyerId) async {
    final response = await http.get('/rider/chat/api/messages/$buyerId');
    // Parse and return messages
  }
  
  Future<ChatMessage> sendMessage(int buyerId, String message) async {
    final response = await http.post('/rider/chat/api/send-message',
      body: {'buyer_id': buyerId, 'message': message});
    // Parse and return sent message
  }
}
```

### Chat Flow
1. Rider accepts delivery → Status becomes `'assigned'`
2. Rider opens chat → Finds/creates conversation with buyer (profile-based)
3. Rider sends message → Message added to shared conversation thread
4. Rider accepts another delivery for same buyer → Uses SAME conversation thread
5. Buyer replies → Message appears in the same thread
6. All messages about different orders appear together

### UI Recommendations
- Show conversation list grouped by buyer (not by delivery)
- Display active deliveries as context under each buyer name
- Show "Active orders: VEL-2026-00001, VEL-2026-00002" in conversation preview
- Different message bubble colors for rider vs buyer
- Display timestamps
- Add delivery context tags in messages (optional)
- Implement pull-to-refresh for new messages
- Add loading indicators

### Important Notes
- **One conversation per rider-buyer pair** - All messages about different orders appear in the same thread
- **Delivery context is shown** - Active deliveries are displayed in the conversation list
- **No more cluttered inbox** - No multiple threads for the same people
- **Backward compatible** - Old delivery-based conversations still work

For detailed implementation, see `RIDER_CHAT_LOGIC.md` and `CHAT_AND_NOTIFICATION_IMPROVEMENTS.md`

---

## Key Features

### 1. Cart Management
- Add to cart with variant selection
- Update quantity
- Remove items
- Buy now (direct checkout)
- Persist cart in database

### 2. Checkout Process
- Select delivery address
- Apply vouchers (discount or free shipping)
- Calculate shipping fee (₱49.00 per seller)
- Calculate commission (5% of subtotal)
- Group items by seller
- Generate order numbers (VEL-YYYY-NNNN)

### 3. Voucher System
- Types: `discount`, `free_shipping`
- Can be seller-specific or platform-wide
- One-time use per buyer
- Expiration dates
- Minimum purchase requirements

### 4. Product Variants
- Color + Size combinations
- Individual stock tracking
- Variant-specific images
- Hex color codes for display

### 5. Reviews & Ratings
- Only after buyer confirms receipt
- 1-5 star rating
- Optional review text
- Updates product average rating
- Updates total review count

### 6. Address Management
- Multiple addresses per user
- Default address selection
- Used for both buyers and sellers
- Format: full_address, city, province, postal_code

### 7. Notifications
- Order status updates
- Delivery updates
- Review reminders
- Stored in `notifications` table

---

## Important Notes

### Network Retry Logic
The web app implements automatic retry for network errors:
```python
# Retries up to 3 times with 1 second delay
# Handles: httpx.ConnectError, RemoteProtocolError, ConnectionError
# Does NOT retry: Validation errors, Auth errors
```

**For Flutter**: Implement similar retry logic using `dio` interceptors or `retry` package.

### Image Handling
- Product images stored in Supabase Storage
- URLs can be:
  - Full URL: `https://...`
  - Relative: `static/uploads/products/...`
- Primary image flag: `is_primary = true`
- Multiple images per product/variant

### Timestamps
- All timestamps in ISO 8601 format
- Use `DateTime.parse()` in Flutter
- Display in local timezone

### Money/Decimal Values
- Store as DECIMAL(10,2) in database
- Always use 2 decimal places
- Format: ₱1,234.56

### Order Number Generation
```
Format: VEL-YYYY-NNNN
Example: VEL-2026-0001

Logic:
1. Get current year
2. Query last order number for that year
3. Increment counter
4. Format with leading zeros
```

### Commission Calculation
```
Commission = Subtotal × 0.05 (5%)
Seller receives: Subtotal - Commission
Platform receives: Commission
```

### Shipping Fee Logic
```
Base fee: ₱49.00 per seller
Multiple sellers: ₱49.00 ÷ number of sellers
Free shipping voucher: paid_by_platform = true
```

---

## Flutter Implementation Tips

### 1. State Management
Recommended: **Riverpod** or **Bloc**
- Separate providers for each user role
- Global state for cart
- Local state for forms

### 2. API Client
Use **Dio** with:
- Base URL configuration
- Interceptors for auth tokens
- Retry logic for network errors
- Request/response logging

### 3. Database
Use **Supabase Flutter SDK**:
```dart
import 'package:supabase_flutter/supabase_flutter.dart';

// Initialize
await Supabase.initialize(
  url: 'YOUR_SUPABASE_URL',
  anonKey: 'YOUR_SUPABASE_ANON_KEY',
);

// Query example
final response = await Supabase.instance.client
  .from('orders')
  .select('*, deliveries(*)')
  .eq('buyer_id', buyerId)
  .order('created_at', ascending: false);
```

### 4. Real-time Updates
Implement Supabase real-time subscriptions for:
- Order status changes
- Delivery updates
- New notifications

```dart
final subscription = Supabase.instance.client
  .from('deliveries')
  .stream(primaryKey: ['delivery_id'])
  .eq('rider_id', riderId)
  .listen((data) {
    // Update UI
  });
```

### 5. Image Caching
Use **cached_network_image** package:
```dart
CachedNetworkImage(
  imageUrl: product.imageUrl,
  placeholder: (context, url) => CircularProgressIndicator(),
  errorWidget: (context, url, error) => Icon(Icons.error),
)
```

### 6. Maps Integration
For rider tracking:
- **Google Maps Flutter** or **Mapbox**
- Show pickup and delivery locations
- Real-time rider location updates

### 7. Push Notifications
Use **Firebase Cloud Messaging**:
- Order status updates
- Delivery notifications
- Chat messages

---

## Testing Checklist

### Buyer Flow
- [ ] Register and login
- [ ] Browse products
- [ ] Add to cart
- [ ] Apply voucher
- [ ] Place order
- [ ] Track delivery
- [ ] Confirm receipt
- [ ] Write review

### Seller Flow
- [ ] Register and login
- [ ] Add product with variants
- [ ] View orders
- [ ] Mark "Prepare Package"
- [ ] Mark "Ready for Pickup"
- [ ] View sales reports

### Rider Flow
- [ ] Register and login
- [ ] View available pickups
- [ ] Accept delivery
- [ ] Mark as picked up
- [ ] Mark as delivered
- [ ] View earnings

### Edge Cases
- [ ] Network errors (retry logic)
- [ ] Out of stock items
- [ ] Cancelled orders
- [ ] Multiple sellers in one order
- [ ] Free shipping voucher
- [ ] Order without variants

---

## Database Queries Reference

### Get Buyer Orders
```sql
SELECT 
  o.*,
  d.status as delivery_status,
  b.first_name, b.last_name,
  s.shop_name
FROM orders o
LEFT JOIN deliveries d ON o.order_id = d.order_id
LEFT JOIN buyers b ON o.buyer_id = b.buyer_id
LEFT JOIN sellers s ON o.seller_id = s.seller_id
WHERE o.buyer_id = ?
ORDER BY o.created_at DESC;
```

### Get Rider Pending Deliveries
```sql
SELECT 
  d.*,
  o.order_number, o.total_amount,
  b.first_name, b.last_name, b.phone_number,
  s.shop_name, s.phone_number as seller_phone
FROM deliveries d
JOIN orders o ON d.order_id = o.order_id
JOIN buyers b ON o.buyer_id = b.buyer_id
JOIN sellers s ON o.seller_id = s.seller_id
WHERE d.status = 'pending' 
  AND d.rider_id IS NULL
ORDER BY d.created_at ASC;
```

### Get Seller Orders
```sql
SELECT 
  o.*,
  d.status as delivery_status,
  b.first_name, b.last_name
FROM orders o
LEFT JOIN deliveries d ON o.order_id = d.order_id
LEFT JOIN buyers b ON o.buyer_id = b.buyer_id
WHERE o.seller_id = ?
ORDER BY o.created_at DESC;
```

---

## Contact & Support

For questions about the implementation:
- Check the documentation files in the repository
- Review the web app source code
- Test the web app at `http://localhost:5000`

---

**Last Updated**: April 9, 2026  
**Version**: 1.0  
**Status**: Production Ready ✅
