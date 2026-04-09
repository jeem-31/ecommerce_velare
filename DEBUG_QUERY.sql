-- Check what the API is returning
-- Run this to see what conversations are being created

-- 1. Check existing conversations for rider_id = 4
SELECT 
    c.conversation_id,
    c.buyer_id,
    c.rider_id,
    c.seller_id,
    c.delivery_id,
    c.last_message,
    c.last_message_at
FROM conversations c
WHERE c.rider_id = 4
ORDER BY c.last_message_at DESC;

-- 2. Check if there are multiple conversations for buyer_id = 8
SELECT 
    c.conversation_id,
    c.buyer_id,
    c.rider_id,
    c.seller_id,
    c.delivery_id,
    COUNT(*) OVER (PARTITION BY c.buyer_id, c.rider_id) as conversation_count
FROM conversations c
WHERE c.rider_id = 4 AND c.buyer_id = 8;

-- 3. Check deliveries grouped by buyer (what the API should return)
SELECT 
    o.buyer_id,
    COUNT(d.delivery_id) as delivery_count,
    STRING_AGG(o.order_number, ', ' ORDER BY d.assigned_at DESC) as order_numbers,
    STRING_AGG(d.status::text, ', ' ORDER BY d.assigned_at DESC) as statuses
FROM deliveries d
JOIN orders o ON d.order_id = o.order_id
WHERE d.rider_id = 4
  AND d.status IN ('assigned', 'in_transit')
GROUP BY o.buyer_id;
