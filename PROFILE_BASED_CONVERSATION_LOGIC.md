# Profile-Based Conversation Logic
## Paano Naging Isang Profile Lang (Hindi Na Nag-Double)

---

## 🎯 Problem: Dati (Product-Based)

### Old System (Per Product/Delivery)
```
Buyer orders 3 products from same seller:
- Product A → Delivery 1 → Conversation 1
- Product B → Delivery 2 → Conversation 2  
- Product C → Delivery 3 → Conversation 3

Result: 3 SEPARATE conversations! 😱
```

**Issues:**
- Cluttered inbox
- Hard to track messages
- Confusing for users
- Duplicate conversations

---

## ✅ Solution: Profile-Based Conversations

### New System (Per User Profile)
```
Buyer orders 3 products from same seller:
- Product A → Delivery 1 ┐
- Product B → Delivery 2 ├─→ ONE Conversation
- Product C → Delivery 3 ┘

Result: 1 conversation only! 🎉
```

---

## 🔧 Implementation Logic

### 1. Database Structure

**Conversations Table:**
```sql
CREATE TABLE conversations (
  conversation_id INT PRIMARY KEY,
  buyer_id INT,           -- Links to buyer profile
  seller_id INT,          -- Links to seller profile
  rider_id INT,           -- Links to rider profile
  delivery_id INT,        -- ❌ NOT USED anymore (kept for compatibility)
  last_message TEXT,
  last_message_at TIMESTAMP,
  created_at TIMESTAMP
);
```

**Key Point:** 
- ❌ OLD: Used `delivery_id` to link conversation
- ✅ NEW: Use `buyer_id`, `seller_id`, `rider_id` to link conversation

---

### 2. Conversation Creation Logic

#### Python Backend (database/supabase_helper.py)

```python
def create_conversation(buyer_id, seller_id, initial_message, rider_id=None, delivery_id=None):
    """
    Create conversation OR reuse existing one
    
    KEY LOGIC: Check if conversation already exists between same people
    """
    
    # STEP 1: Check if conversation already exists
    if rider_id and buyer_id:
        # Rider-Buyer conversation
        existing = supabase.table('conversations').select('conversation_id')\
            .eq('rider_id', rider_id)\
            .eq('buyer_id', buyer_id)\
            .is_('seller_id', 'null')\
            .execute()
        
        if existing.data:
            # ✅ REUSE existing conversation
            return existing.data[0]['conversation_id']
    
    elif seller_id and buyer_id:
        # Seller-Buyer conversation
        existing = supabase.table('conversations').select('conversation_id')\
            .eq('seller_id', seller_id)\
            .eq('buyer_id', buyer_id)\
            .is_('rider_id', 'null')\
            .execute()
        
        if existing.data:
            # ✅ REUSE existing conversation
            return existing.data[0]['conversation_id']
    
    # STEP 2: No existing conversation, create new one
    conversation_data = {
        'buyer_id': buyer_id,
        'seller_id': seller_id,
        'rider_id': rider_id,
        # ❌ NOT setting delivery_id anymore
        'last_message': initial_message,
        'last_message_at': datetime.now().isoformat()
    }
    
    response = supabase.table('conversations').insert(conversation_data).execute()
    return response.data[0]['conversation_id']
```

**Key Points:**
1. ✅ Check if conversation exists between same people
2. ✅ If exists, REUSE it (don't create new)
3. ✅ If not exists, CREATE new one
4. ❌ Don't use delivery_id to link

---

### 3. Loading Conversations Logic

#### Python Backend (blueprints/rider_chat.py)

```python
def get_rider_conversations_api():
    """
    Load conversations grouped by PROFILE, not by delivery
    """
    
    # STEP 1: Get all deliveries for this rider
    deliveries = supabase.table('deliveries').select('''
        delivery_id,
        order_id,
        status,
        orders (
            order_number,
            buyer_id,      # ← KEY: Get buyer_id
            seller_id      # ← KEY: Get seller_id
        )
    ''').eq('rider_id', rider_id).execute()
    
    # STEP 2: Group deliveries by buyer_id (not by delivery_id!)
    buyers_map = {}  # { buyer_id: [delivery1, delivery2, ...] }
    
    for delivery in deliveries:
        buyer_id = delivery['orders']['buyer_id']
        
        # Group by buyer_id
        if buyer_id not in buyers_map:
            buyers_map[buyer_id] = {
                'buyer_id': buyer_id,
                'deliveries': []
            }
        
        # Add delivery to this buyer's group
        buyers_map[buyer_id]['deliveries'].append({
            'delivery_id': delivery['delivery_id'],
            'order_number': delivery['orders']['order_number'],
            'status': delivery['status']
        })
    
    # STEP 3: Create ONE conversation per buyer
    conversations = []
    for buyer_id, buyer_data in buyers_map.items():
        # Get buyer info
        buyer = get_buyer_info(buyer_id)
        
        # Check if conversation exists
        conv = supabase.table('conversations').select('*')\
            .eq('rider_id', rider_id)\
            .eq('buyer_id', buyer_id)\
            .is_('seller_id', 'null')\
            .execute()
        
        # Create conversation object
        conversations.append({
            'conversation_id': conv.data[0]['conversation_id'] if conv.data else f'new_{buyer_id}',
            'buyer_id': buyer_id,
            'contact_name': f"{buyer['first_name']} {buyer['last_name']}",
            'active_deliveries': buyer_data['deliveries'],  # ← All deliveries for this buyer
            'context_message': format_deliveries(buyer_data['deliveries'])
        })
    
    return conversations
```

**Key Points:**
1. ✅ Group deliveries by `buyer_id` (not by `delivery_id`)
2. ✅ One conversation per buyer (even if multiple deliveries)
3. ✅ Show all deliveries in context message

---

### 4. Visual Example

#### Scenario: Buyer has 2 orders

**Database:**
```
deliveries table:
┌─────────────┬──────────┬──────────┬────────────────┬────────────┐
│ delivery_id │ order_id │ rider_id │ order_number   │ status     │
├─────────────┼──────────┼──────────┼────────────────┼────────────┤
│ 260         │ 549      │ 4        │ VEL-2026-0008  │ assigned   │
│ 269         │ 558      │ 4        │ VEL-2026-0014  │ in_transit │
└─────────────┴──────────┴──────────┴────────────────┴────────────┘

orders table:
┌──────────┬────────────────┬──────────┐
│ order_id │ order_number   │ buyer_id │
├──────────┼────────────────┼──────────┤
│ 549      │ VEL-2026-0008  │ 8        │
│ 558      │ VEL-2026-0014  │ 8        │  ← Same buyer!
└──────────┴────────────────┴──────────┘

conversations table:
┌─────────────────┬──────────┬──────────┬───────────┐
│ conversation_id │ buyer_id │ rider_id │ seller_id │
├─────────────────┼──────────┼──────────┼───────────┤
│ 36              │ 8        │ 4        │ NULL      │  ← ONE conversation only!
└─────────────────┴──────────┴──────────┴───────────┘
```

**Grouping Logic:**
```python
# Step 1: Get deliveries
deliveries = [
    {'delivery_id': 260, 'order_id': 549, 'buyer_id': 8, 'order_number': 'VEL-2026-0008'},
    {'delivery_id': 269, 'order_id': 558, 'buyer_id': 8, 'order_number': 'VEL-2026-0014'}
]

# Step 2: Group by buyer_id
buyers_map = {
    8: {  # ← buyer_id as key
        'buyer_id': 8,
        'deliveries': [
            {'delivery_id': 260, 'order_number': 'VEL-2026-0008', 'status': 'assigned'},
            {'delivery_id': 269, 'order_number': 'VEL-2026-0014', 'status': 'in_transit'}
        ]
    }
}

# Step 3: Create ONE conversation
conversation = {
    'conversation_id': 36,
    'buyer_id': 8,
    'contact_name': 'jeje mon',
    'active_deliveries': [
        {'order_number': 'VEL-2026-0008', 'status': 'assigned'},
        {'order_number': 'VEL-2026-0014', 'status': 'in_transit'}
    ],
    'context_message': '📦 VEL-2026-0008 • 🚚 VEL-2026-0014'
}
```

**Result in UI:**
```
┌─────────────────────────────────────────────┐
│  👤 jeje mon                      1h        │
│  Hi! I'm your rider for Orders...          │
│  📦 VEL-2026-0008 • 🚚 VEL-2026-0014       │
└─────────────────────────────────────────────┘
     ↑
   ONE conversation only!
```

---

## 🔑 Key Differences: Old vs New

### OLD System (Per Delivery)
```python
# ❌ Created conversation per delivery
for delivery in deliveries:
    conversation = create_conversation(
        buyer_id=delivery['buyer_id'],
        delivery_id=delivery['delivery_id']  # ← Links to specific delivery
    )
    conversations.append(conversation)

# Result: Multiple conversations for same buyer
```

### NEW System (Per Profile)
```python
# ✅ Group deliveries by buyer first
buyers_map = {}
for delivery in deliveries:
    buyer_id = delivery['buyer_id']
    if buyer_id not in buyers_map:
        buyers_map[buyer_id] = []
    buyers_map[buyer_id].append(delivery)

# ✅ Create ONE conversation per buyer
for buyer_id, deliveries in buyers_map.items():
    conversation = get_or_create_conversation(
        buyer_id=buyer_id,
        rider_id=rider_id
        # ❌ No delivery_id!
    )
    conversation['deliveries'] = deliveries  # ← All deliveries
    conversations.append(conversation)

# Result: ONE conversation per buyer
```

---

## 📱 Mobile App Implementation

### Flutter Logic

```dart
class ChatService {
  // Load conversations
  Future<List<ConversationModel>> loadConversations() async {
    final response = await http.get('/rider/chat/api/conversations');
    final data = json.decode(response.body);
    
    // Backend already grouped by profile
    // Just parse the response
    return (data['buyer_conversations'] as List)
        .map((c) => ConversationModel.fromJson(c))
        .toList();
  }
  
  // Send message - use buyer_id, NOT delivery_id
  Future<void> sendMessage(int buyerId, String message) async {
    await http.post(
      '/rider/chat/api/send-message',
      body: json.encode({
        'buyer_id': buyerId,  // ← Use buyer_id
        'message': message
      })
    );
  }
  
  // Load messages - use buyer_id, NOT delivery_id
  Future<List<MessageModel>> loadMessages(int buyerId) async {
    final response = await http.get('/rider/chat/api/messages/$buyerId');
    // ↑ Use buyer_id in URL
    
    final data = json.decode(response.body);
    return (data['messages'] as List)
        .map((m) => MessageModel.fromJson(m))
        .toList();
  }
}
```

**Key Points:**
1. ✅ Use `buyer_id` everywhere (not `delivery_id`)
2. ✅ Backend handles grouping
3. ✅ Frontend just displays grouped data

---

## 🎨 UI Display Logic

### Conversation List Item

```dart
Widget buildConversationItem(ConversationModel conversation) {
  // Show all active deliveries in subtitle
  String contextMessage = conversation.activeDeliveries
      .map((d) => '${d.getStatusEmoji()} ${d.orderNumber}')
      .join(' • ');
  
  return ListTile(
    title: Text(conversation.contactName),  // ← Buyer name
    subtitle: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(conversation.lastMessage),
        Text(contextMessage),  // ← Shows all orders
      ],
    ),
    onTap: () => openChat(conversation),
  );
}
```

**Display:**
```
┌─────────────────────────────────────────────┐
│  👤 jeje mon                                │
│  Hi! I'm your rider for Orders...          │
│  📦 VEL-2026-0008 • 🚚 VEL-2026-0014       │
│                                             │
│  ↑ ONE item showing BOTH orders            │
└─────────────────────────────────────────────┘
```

---

## 🔍 Debugging Tips

### Check if Grouping Works

**SQL Query:**
```sql
-- Check conversations per buyer
SELECT 
    buyer_id,
    COUNT(*) as conversation_count
FROM conversations
WHERE rider_id = 4
GROUP BY buyer_id
HAVING COUNT(*) > 1;

-- Should return EMPTY (no duplicates)
```

**Python Debug:**
```python
# In get_rider_conversations_api()
print(f"👥 Found {len(buyers_map)} unique buyers")
for buyer_id, data in buyers_map.items():
    print(f"  - Buyer {buyer_id}: {len(data['deliveries'])} deliveries")

# Expected output:
# 👥 Found 1 unique buyers
#   - Buyer 8: 2 deliveries
```

**Flutter Debug:**
```dart
// In loadConversations()
print('Loaded ${conversations.length} conversations');
for (var conv in conversations) {
  print('Buyer ${conv.buyerId}: ${conv.activeDeliveries.length} orders');
}

// Expected output:
// Loaded 1 conversations
// Buyer 8: 2 orders
```

---

## ✅ Checklist: Is Profile-Based Working?

- [ ] One conversation per buyer (not per delivery)
- [ ] Multiple orders show in same conversation
- [ ] Context message shows all orders with emoji
- [ ] Sending message uses buyer_id (not delivery_id)
- [ ] Loading messages uses buyer_id (not delivery_id)
- [ ] No duplicate conversations in database
- [ ] Conversation persists after delivery completed

---

## 🚨 Common Mistakes to Avoid

### ❌ Mistake 1: Using delivery_id
```dart
// WRONG
await http.post('/send-message', body: {
  'delivery_id': deliveryId,  // ❌ Don't use this!
  'message': message
});

// CORRECT
await http.post('/send-message', body: {
  'buyer_id': buyerId,  // ✅ Use buyer_id
  'message': message
});
```

### ❌ Mistake 2: Creating conversation per delivery
```python
# WRONG
for delivery in deliveries:
    create_conversation(
        buyer_id=buyer_id,
        delivery_id=delivery['delivery_id']  # ❌ Creates duplicate!
    )

# CORRECT
# Check if conversation exists first
existing = get_conversation(buyer_id=buyer_id, rider_id=rider_id)
if not existing:
    create_conversation(buyer_id=buyer_id, rider_id=rider_id)
```

### ❌ Mistake 3: Not grouping deliveries
```python
# WRONG
conversations = []
for delivery in deliveries:
    conversations.append({
        'buyer_id': delivery['buyer_id'],
        'delivery': delivery  # ❌ One conversation per delivery
    })

# CORRECT
buyers_map = {}
for delivery in deliveries:
    buyer_id = delivery['buyer_id']
    if buyer_id not in buyers_map:
        buyers_map[buyer_id] = []
    buyers_map[buyer_id].append(delivery)  # ✅ Group by buyer

conversations = [
    {'buyer_id': buyer_id, 'deliveries': deliveries}
    for buyer_id, deliveries in buyers_map.items()
]
```

---

## 📊 Summary

### The Magic Formula

```
OLD: 1 Delivery = 1 Conversation
     3 Deliveries = 3 Conversations 😱

NEW: 1 Buyer = 1 Conversation
     3 Deliveries (same buyer) = 1 Conversation 🎉
```

### Key Concepts

1. **Group by Profile** - Use buyer_id/seller_id as key
2. **Reuse Conversations** - Check if exists before creating
3. **Show All Orders** - Display multiple orders in context
4. **Profile-Based Linking** - Don't link to delivery_id

---

**Last Updated:** April 9, 2026
**Version:** 1.0
