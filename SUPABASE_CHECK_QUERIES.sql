-- ============================================================================
-- SUPABASE CHECK QUERIES
-- Run these queries in Supabase SQL Editor to check the data
-- ============================================================================

-- 1. CHECK MESSAGES TABLE STRUCTURE
-- See if order_id column exists
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'messages'
ORDER BY ordinal_position;

-- 2. CHECK ALL DELIVERIES FOR RIDER (replace 21 with actual rider_id)
-- This will show why Order #14 might be missing
SELECT 
    d.delivery_id,
    d.order_id,
    d.status,
    d.rider_id,
    o.order_number,
    o.buyer_id,
    b.first_name || ' ' || b.last_name as buyer_name
FROM deliveries d
JOIN orders o ON d.order_id = o.order_id
JOIN buyers b ON o.buyer_id = b.buyer_id
WHERE d.rider_id = 21  -- CHANGE THIS to your rider_id
ORDER BY d.assigned_at DESC;

-- 3. CHECK SPECIFIC ORDER #14
-- See the status and who it's assigned to
SELECT 
    d.delivery_id,
    d.order_id,
    d.status,
    d.rider_id,
    d.assigned_at,
    d.picked_up_at,
    d.delivered_at,
    o.order_number,
    o.order_status,
    o.buyer_id
FROM deliveries d
JOIN orders o ON d.order_id = o.order_id
WHERE o.order_number = 'VEL-2026-00014'  -- CHANGE THIS to actual order number
   OR d.order_id = 14;  -- Or use order_id directly

-- 4. CHECK ACTIVE DELIVERIES (what the chat shows)
-- This is what the rider chat API returns
SELECT 
    d.delivery_id,
    d.order_id,
    d.status,
    o.order_number,
    o.buyer_id,
    b.first_name || ' ' || b.last_name as buyer_name
FROM deliveries d
JOIN orders o ON d.order_id = o.order_id
JOIN buyers b ON o.buyer_id = b.buyer_id
WHERE d.rider_id = 21  -- CHANGE THIS to your rider_id
  AND d.status IN ('assigned', 'in_transit')
ORDER BY d.assigned_at DESC;

-- 5. CHECK CONVERSATIONS TABLE
-- See existing conversations for this rider
SELECT 
    c.conversation_id,
    c.buyer_id,
    c.seller_id,
    c.rider_id,
    c.delivery_id,
    c.last_message,
    c.last_message_at,
    b.first_name || ' ' || b.last_name as buyer_name
FROM conversations c
LEFT JOIN buyers b ON c.buyer_id = b.buyer_id
WHERE c.rider_id = 21  -- CHANGE THIS to your rider_id
ORDER BY c.last_message_at DESC;

-- 6. CHECK MESSAGES FOR A CONVERSATION
-- See all messages in a specific conversation
SELECT 
    m.message_id,
    m.conversation_id,
    m.sender_type,
    m.sender_id,
    m.message_text,
    m.is_read,
    m.created_at
FROM messages m
WHERE m.conversation_id = 3  -- CHANGE THIS to actual conversation_id
ORDER BY m.created_at ASC;

-- 7. CHECK BUYER'S ORDERS
-- See all orders for a specific buyer
SELECT 
    o.order_id,
    o.order_number,
    o.order_status,
    d.delivery_id,
    d.status as delivery_status,
    d.rider_id,
    r.first_name || ' ' || r.last_name as rider_name
FROM orders o
LEFT JOIN deliveries d ON o.order_id = d.order_id
LEFT JOIN riders r ON d.rider_id = r.rider_id
WHERE o.buyer_id = 8  -- CHANGE THIS to actual buyer_id
ORDER BY o.created_at DESC;

-- 8. CHECK IF ORDER_ID COLUMN EXISTS IN MESSAGES
-- This will tell us if we can add order context per message
SELECT 
    COUNT(*) as has_order_id_column
FROM information_schema.columns
WHERE table_name = 'messages' 
  AND column_name = 'order_id';
-- Result: 0 = doesn't exist, 1 = exists

-- 9. CHECK DELIVERY STATUS COUNTS
-- See how many deliveries are in each status
SELECT 
    d.status,
    COUNT(*) as count
FROM deliveries d
WHERE d.rider_id = 21  -- CHANGE THIS to your rider_id
GROUP BY d.status
ORDER BY count DESC;

-- 10. CHECK DUPLICATE CONVERSATIONS
-- See if there are multiple conversations for same rider-buyer pair
SELECT 
    c.rider_id,
    c.buyer_id,
    COUNT(*) as conversation_count,
    STRING_AGG(c.conversation_id::text, ', ') as conversation_ids
FROM conversations c
WHERE c.rider_id = 21  -- CHANGE THIS to your rider_id
  AND c.seller_id IS NULL
GROUP BY c.rider_id, c.buyer_id
HAVING COUNT(*) > 1;

-- ============================================================================
-- QUERIES TO FIX ISSUES
-- ============================================================================

-- 11. ADD ORDER_ID COLUMN TO MESSAGES (if needed)
-- Run this if you want to add order context per message
ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS order_id INTEGER REFERENCES orders(order_id);

-- 12. CREATE INDEX FOR BETTER PERFORMANCE
-- Run these to speed up queries
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversations_rider_buyer ON conversations(rider_id, buyer_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_rider_status ON deliveries(rider_id, status);

-- 13. CLEAN UP OLD DELIVERY-BASED CONVERSATIONS
-- Remove conversations that have delivery_id (old system)
-- WARNING: This will delete old conversations!
-- DELETE FROM conversations WHERE delivery_id IS NOT NULL;

-- 14. MERGE DUPLICATE CONVERSATIONS
-- If there are multiple conversations for same rider-buyer pair
-- This is a complex operation, run carefully!
-- (You'll need to manually merge based on the results from query #10)

-- ============================================================================
-- USEFUL QUERIES FOR DEBUGGING
-- ============================================================================

-- 15. CHECK RECENT ACTIVITY
-- See recent deliveries, messages, and conversations
SELECT 
    'delivery' as type,
    d.delivery_id as id,
    d.status,
    d.assigned_at as timestamp,
    o.order_number as details
FROM deliveries d
JOIN orders o ON d.order_id = o.order_id
WHERE d.rider_id = 21
UNION ALL
SELECT 
    'message' as type,
    m.message_id as id,
    m.sender_type as status,
    m.created_at as timestamp,
    LEFT(m.message_text, 50) as details
FROM messages m
JOIN conversations c ON m.conversation_id = c.conversation_id
WHERE c.rider_id = 21
ORDER BY timestamp DESC
LIMIT 20;

-- 16. CHECK UNREAD MESSAGE COUNTS
-- See unread counts for all conversations
SELECT 
    c.conversation_id,
    c.buyer_id,
    b.first_name || ' ' || b.last_name as buyer_name,
    c.buyer_unread_count,
    c.rider_unread_count,
    c.last_message_at
FROM conversations c
JOIN buyers b ON c.buyer_id = b.buyer_id
WHERE c.rider_id = 21  -- CHANGE THIS to your rider_id
ORDER BY c.last_message_at DESC;

-- ============================================================================
-- INSTRUCTIONS
-- ============================================================================

/*
HOW TO USE THESE QUERIES:

1. Go to Supabase Dashboard
2. Click on "SQL Editor" in the left sidebar
3. Click "New Query"
4. Copy and paste the queries you want to run
5. IMPORTANT: Replace the placeholder values:
   - rider_id = 21 (change to actual rider_id)
   - buyer_id = 8 (change to actual buyer_id)
   - conversation_id = 3 (change to actual conversation_id)
   - order_number = 'VEL-2026-00014' (change to actual order number)
6. Click "Run" or press Ctrl+Enter

RECOMMENDED ORDER:
1. Run query #1 to check messages table structure
2. Run query #2 to see all deliveries for rider
3. Run query #3 to check specific Order #14
4. Run query #4 to see what chat shows
5. Run query #8 to check if order_id column exists

If you want to add order context per message:
- Run query #11 to add order_id column
- Run query #12 to add indexes for performance

SAFETY NOTES:
- Queries 1-10 are READ-ONLY (safe to run)
- Queries 11-14 MODIFY DATA (be careful!)
- Always backup before running DELETE or ALTER queries
*/
