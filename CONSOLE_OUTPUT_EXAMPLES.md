# 📊 Console Output Examples

This document shows what you'll see in the Flask console when the multi-device login detection is working.

## 🔐 First Login (No Notification)

```
🔍 User logging in: buyer@example.com
✅ User authenticated successfully
📱 Device info: Chrome on Windows
🔍 Checking for other active sessions...
📊 Found 0 active sessions
✅ First login - no notification needed
🔑 Generating session token...
✅ Created session for user 1 from Chrome on Windows
💾 Session token stored in Flask session
✅ Login successful - redirecting to /
```

## 🔔 New Device Login (Notification Created)

```
🔍 User logging in: buyer@example.com
✅ User authenticated successfully
📱 Device info: Firefox on Windows
🔍 Checking for other active sessions...
📊 Found 1 active sessions
  - Session 1: Chrome on Windows (active)
🔔 New device login detected: Firefox on Windows (existing: Chrome on Windows)
🔑 Generating session token...
✅ Created session for user 1 from Firefox on Windows
🔔 Creating device login notification for user_id=1, device=Firefox on Windows
✅ Created device login notification for user 1
💾 Session token stored in Flask session
✅ Login successful - redirecting to /
```

## 🔄 Same Device Login (No Notification)

```
🔍 User logging in: buyer@example.com
✅ User authenticated successfully
📱 Device info: Chrome on Windows
🔍 Checking for other active sessions...
📊 Found 2 active sessions
  - Session 1: Chrome on Windows (active)
  - Session 2: Firefox on Windows (active)
🔍 Checking if new device...
✅ Same device detected - no notification needed
🔑 Generating session token...
✅ Created session for user 1 from Chrome on Windows
💾 Session token stored in Flask session
✅ Login successful - redirecting to /
```

## 📱 Mobile Device Login (Notification Created)

```
🔍 User logging in: buyer@example.com
✅ User authenticated successfully
📱 Device info: Chrome on Android
🔍 Checking for other active sessions...
📊 Found 2 active sessions
  - Session 1: Chrome on Windows (active)
  - Session 2: Firefox on Windows (active)
🔔 New device login detected: Chrome on Android (existing: Chrome on Windows)
🔑 Generating session token...
✅ Created session for user 1 from Chrome on Android
🔔 Creating device login notification for user_id=1, device=Chrome on Android
✅ Created device login notification for user 1
💾 Session token stored in Flask session
✅ Login successful - redirecting to /
```

## 🚪 Logout

```
🔍 User logging out...
🔑 Session token: xK7j9mP2nQ8rT5vW1yZ4aB6cD3eF0gH8iJ1kL4mN7oP9
💾 Deactivating session in database...
✅ Deactivated session: xK7j9mP2nQ8rT5vW1yZ4aB6cD3eF0gH8iJ1kL4mN7oP9
🧹 Clearing Flask session...
✅ Logout successful - redirecting to /login
```

## ⚠️ Error Handling (Non-Breaking)

### Table Doesn't Exist Yet
```
🔍 User logging in: buyer@example.com
✅ User authenticated successfully
📱 Device info: Chrome on Windows
🔍 Checking for other active sessions...
❌ Error getting active sessions: {'message': "Could not find the table 'public.user_sessions'"}
⚠️ Session tracking error (non-critical): Table doesn't exist
✅ Login successful - redirecting to / (session tracking disabled)
```

### Database Connection Issue
```
🔍 User logging in: buyer@example.com
✅ User authenticated successfully
📱 Device info: Chrome on Windows
❌ Error creating user session: Connection timeout
⚠️ Session tracking error (non-critical): Connection timeout
✅ Login successful - redirecting to / (session tracking disabled)
```

## 🧪 Test Script Output

### Successful Test Run
```
============================================================
🧪 TESTING MULTI-DEVICE LOGIN DETECTION
============================================================

📋 Test User ID: 1

============================================================
TEST 1: First Login (Chrome on Windows)
============================================================
✅ Created session for user 1 from Chrome on Windows
✅ Created session 1
🔍 Is new device? False (Expected: False)

============================================================
TEST 2: Second Login (Chrome on Windows - Same Device)
============================================================
✅ Created session for user 1 from Chrome on Windows
✅ Created session 2
🔍 Is new device? False (Expected: False)

============================================================
TEST 3: Third Login (Firefox on Windows - Different Browser)
============================================================
🔔 New device login detected: Firefox on Windows (existing: Chrome on Windows)
🔍 Is new device? True (Expected: True)
✅ Created session for user 1 from Firefox on Windows
✅ Created session 3
🔔 Creating notification for new device login...
🔔 Creating device login notification for user_id=1, device=Firefox on Windows
✅ Created device login notification for user 1

============================================================
TEST 4: Get All Active Sessions
============================================================
📊 Active sessions: 3

  Session 1:
    - Device: Chrome on Windows
    - Browser: Chrome
    - OS: Windows
    - IP: 127.0.0.1
    - Login: 2026-02-16T14:30:00.000Z
    - Active: True

  Session 2:
    - Device: Chrome on Windows
    - Browser: Chrome
    - OS: Windows
    - IP: 127.0.0.1
    - Login: 2026-02-16T14:31:00.000Z
    - Active: True

  Session 3:
    - Device: Firefox on Windows
    - Browser: Firefox
    - OS: Windows
    - IP: 127.0.0.1
    - Login: 2026-02-16T14:32:00.000Z
    - Active: True

============================================================
TEST 5: Logout (Deactivate Session 1)
============================================================
✅ Deactivated session: xK7j9mP2nQ8rT5vW1yZ4aB6cD3eF0gH8iJ1kL4mN7oP9
✅ Deactivated session 1
📊 Active sessions after logout: 2 (Expected: 2)

============================================================
✅ ALL TESTS COMPLETED!
============================================================

💡 Next Steps:
1. Check your notifications table for the new device notification
2. Login to the app from different browsers to test in real scenario
3. Check the user_sessions table to see all session records
```

## 🔍 Database Queries to Verify

### Check Active Sessions
```sql
SELECT 
    session_id,
    user_id,
    device_info,
    browser,
    os,
    ip_address,
    login_time,
    is_active
FROM user_sessions
WHERE user_id = 1
ORDER BY login_time DESC;
```

Expected Output:
```
session_id | user_id | device_info          | browser | os      | ip_address  | login_time           | is_active
-----------+---------+----------------------+---------+---------+-------------+----------------------+-----------
3          | 1       | Firefox on Windows   | Firefox | Windows | 127.0.0.1   | 2026-02-16 14:32:00 | true
2          | 1       | Chrome on Windows    | Chrome  | Windows | 127.0.0.1   | 2026-02-16 14:31:00 | true
1          | 1       | Chrome on Windows    | Chrome  | Windows | 127.0.0.1   | 2026-02-16 14:30:00 | false
```

### Check Notifications
```sql
SELECT 
    notification_id,
    user_id,
    title,
    message,
    notification_type,
    is_read,
    created_at
FROM notifications
WHERE user_id = 1 AND notification_type = 'security'
ORDER BY created_at DESC;
```

Expected Output:
```
notification_id | user_id | title                        | message                                          | notification_type | is_read | created_at
----------------+---------+------------------------------+--------------------------------------------------+-------------------+---------+----------------------
1               | 1       | 🔐 New Device Login Detected | Your account was accessed from a new device:... | security          | false   | 2026-02-16 14:32:00
```

## 📱 Browser Console (Frontend)

When notification appears:
```javascript
// Notification loaded
console.log('📬 Loaded 1 new notification');
console.log('🔐 Security notification: New Device Login Detected');

// Notification displayed
console.log('✅ Notification rendered in dropdown');
```

## 🎯 What to Look For

### ✅ Success Indicators:
- `✅ Created session for user X from [Device]`
- `🔔 New device login detected`
- `✅ Created device login notification`
- `✅ Deactivated session`

### ⚠️ Warning Indicators (Non-Critical):
- `⚠️ Session tracking error (non-critical)`
- `⚠️ Could not deactivate session (non-critical)`
- Login still succeeds even with warnings

### ❌ Error Indicators (Critical):
- `❌ Login error`
- `❌ Database connection failed`
- These prevent login from succeeding

## 🔧 Debugging Tips

### Enable Verbose Logging
Add this to your Flask app:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Session Token
```python
from flask import session
print(f"Session token: {session.get('session_token')}")
```

### Verify User-Agent Parsing
```python
from flask import request
print(f"User-Agent: {request.headers.get('User-Agent')}")
```

### Test Database Connection
```python
from database.db_config import get_supabase_client
supabase = get_supabase_client()
print(f"Supabase connected: {supabase is not None}")
```
