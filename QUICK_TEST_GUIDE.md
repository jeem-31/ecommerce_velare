# Quick Test Guide - Chat and Notification Improvements

## Test 1: Notifications on "Ready for Pickup"

### Steps:
1. Login as Seller
2. Go to Product Management → Orders tab
3. Find an order with status "Preparing"
4. Click "Ready for Pickup"

### Expected Result:
✅ Seller receives notification: "📦 Order Ready for Pickup - You marked Order #VEL-2026-00001 is ready for pickup. Items: Product A (x2), Product B (x1)"
✅ Buyer receives notification: "📦 Order Ready for Pickup - Order #VEL-2026-00001 is ready for pickup. Items: Product A (x2), Product B (x1)"

### Check:
- [ ] Both seller and buyer have notifications
- [ ] Multiple products are consolidated in one message
- [ ] Product names and quantities are correct

---

## Test 2: Rider Chat - Profile-Based Conversations

### Steps:
1. Login as Rider
2. Accept a delivery from Buyer A
3. Go to Chat page
4. Click on Buyer A's conversation

### Expected Result:
✅ Messages load successfully
✅ Can send messages
✅ Context shows: "Active orders: VEL-2026-00001"

### Additional Test:
5. Accept another delivery from the same Buyer A
6. Go back to Chat page
7. Click on Buyer A's conversation again

### Expected Result:
✅ Same conversation thread (not a new one)
✅ Context shows: "Active orders: VEL-2026-00001, VEL-2026-00002"
✅ All previous messages are still there

### Check:
- [ ] Conversation list loads
- [ ] Clicking on buyer loads messages
- [ ] Can send messages successfully
- [ ] Multiple deliveries use same thread
- [ ] Context message shows all active orders

---

## Test 3: Consolidated Product Notifications

### Steps:
1. Login as Buyer
2. Add 3 different products to cart
3. Checkout and place order
4. Login as Seller
5. Mark order as "Ready for Pickup"

### Expected Result:
✅ ONE notification (not 3 separate ones)
✅ Message lists all 3 products: "Items: Product A (x1), Product B (x2), Product C (x1)"

### Check:
- [ ] Only one notification received
- [ ] All products listed in the message
- [ ] Quantities are correct

---

## Common Issues and Solutions

### Issue: Messages not loading
**Solution**: Check browser console for errors. Make sure backend API is running.

### Issue: "delivery_id not found" error
**Solution**: Clear browser cache and reload. The JavaScript has been updated to use buyer_id.

### Issue: Multiple conversations for same buyer
**Solution**: This might be old data. New conversations will be profile-based. Old delivery-based conversations will naturally phase out.

### Issue: Notifications not appearing
**Solution**: Check that both buyer and seller user_ids are being retrieved correctly in the backend.

---

## Browser Console Checks

Open browser console (F12) and check for:

### When loading conversations:
```
💬 [CONVERSATIONS] Loading conversations...
📦 Found X conversations
✅ Returning X conversations
```

### When clicking on a conversation:
```
🖼️ Setting avatar for: Juan Dela Cruz
📸 Avatar path: /static/images/...
✅ Has avatar: true/false
```

### When loading messages:
```
💬 [MESSAGES] Loading messages for buyer X...
🔍 Rider ID: X
👤 Buyer ID: X
💬 Found X messages
✅ Returning X messages
```

### When sending a message:
```
📤 Sending message...
✅ Message sent successfully
```

---

## API Testing (Optional)

### Test Get Conversations:
```bash
curl http://localhost:5000/rider/chat/api/conversations \
  -H "Cookie: session=..."
```

Expected: JSON with conversations array containing buyer_id and active_deliveries

### Test Get Messages:
```bash
curl http://localhost:5000/rider/chat/api/messages/123 \
  -H "Cookie: session=..."
```

Expected: JSON with messages array

### Test Send Message:
```bash
curl -X POST http://localhost:5000/rider/chat/api/send-message \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"buyer_id": 123, "message": "Test message"}'
```

Expected: JSON with success: true and message object

---

## Rollback Instructions

If major issues occur:

1. **Revert JavaScript**:
   ```bash
   git checkout HEAD -- static/js/rider/rider_chat.js
   ```

2. **Revert Backend**:
   ```bash
   git checkout HEAD -- blueprints/rider_chat.py
   git checkout HEAD -- database/supabase_helper.py
   git checkout HEAD -- blueprints/seller_product_management.py
   ```

3. **Restart Server**:
   ```bash
   docker-compose restart
   ```

---

## Success Criteria

All tests pass when:
- ✅ Both buyer and seller receive notifications
- ✅ Multiple products are consolidated
- ✅ Rider chat loads conversations
- ✅ Messages load when clicking on buyer
- ✅ Can send messages successfully
- ✅ Multiple deliveries use same conversation thread
- ✅ Context shows all active orders
- ✅ No JavaScript errors in console
- ✅ No backend errors in logs

---

## Next Steps After Testing

1. Monitor logs for any errors
2. Check user feedback
3. Update mobile app to use new API endpoints
4. Consider adding more features:
   - Message search
   - Conversation archiving
   - Delivery tags in messages
   - Push notifications
