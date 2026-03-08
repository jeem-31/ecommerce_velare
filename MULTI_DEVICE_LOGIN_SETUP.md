# Multi-Device Login Detection Setup

## 🎯 Feature Overview
This feature detects when a user logs in from a new device and sends them a notification. The notification is stored in the database, so it works across all devices (mobile, desktop, etc.) without requiring real-time connections.

## 📋 Setup Instructions

### Step 1: Run SQL Migration
You need to create the `user_sessions` table in your Supabase database.

1. Go to your Supabase Dashboard
2. Navigate to **SQL Editor**
3. Copy and paste the SQL from `database/add_user_sessions_table.sql`
4. Click **Run**

### Step 2: Verify Installation
Run this command to check if the table was created:
```bash
python run_session_migration.py
```

You should see: `✅ user_sessions table already exists!`

## 🔧 How It Works

### On Login:
1. System extracts device info from user agent (browser + OS)
2. Generates unique session token
3. Checks if user has other active sessions from different devices
4. If yes, creates a notification: "New login detected from [Device] at [Time]"
5. Stores session in `user_sessions` table

### On Logout:
1. Marks session as inactive (`is_active = false`)
2. Clears Flask session

### Notification Display:
- Notifications are stored in the `notifications` table
- They appear when user refreshes/reloads the page
- Works on mobile and desktop (no real-time required)

## 📊 Database Schema

### user_sessions table:
- `session_id` - Primary key
- `user_id` - Foreign key to users table
- `session_token` - Unique token for this session
- `device_info` - e.g., "Chrome on Windows"
- `browser` - e.g., "Chrome"
- `os` - e.g., "Windows"
- `ip_address` - User's IP address
- `login_time` - When session was created
- `last_activity` - Last activity timestamp
- `is_active` - Boolean (true = active, false = logged out)

## 🧪 Testing

### Test Scenario 1: Same Device
1. Login from Chrome on Windows
2. Logout
3. Login again from Chrome on Windows
4. ❌ No notification (same device)

### Test Scenario 2: Different Browser
1. Login from Chrome on Windows
2. Open Firefox on same computer
3. Login from Firefox
4. ✅ Notification appears: "New login from Firefox on Windows"

### Test Scenario 3: Mobile Device
1. Login from Chrome on Windows (desktop)
2. Open browser on phone
3. Login from phone
4. ✅ Notification appears: "New login from Chrome on Android"

## 🔐 Security Features

- Session tokens are cryptographically secure (32 bytes)
- IP addresses are logged for security auditing
- Inactive sessions are marked (not deleted) for audit trail
- Notifications alert users to suspicious logins

## 📝 Code Files Modified

1. `database/supabase_helper.py` - Added session management functions
2. `blueprints/auth.py` - Added session tracking to login/logout
3. `blueprints/notification_helper.py` - Added device login notification
4. `database/add_user_sessions_table.sql` - SQL migration

## ⚙️ Configuration

No configuration needed! The feature works automatically once the SQL migration is run.

## 🐛 Troubleshooting

### "Table doesn't exist" error
- Run the SQL migration in Supabase SQL Editor
- Verify with: `python run_session_migration.py`

### Notifications not appearing
- Check browser console for errors
- Verify notifications table has the new records
- Refresh the page (notifications load on page load)

### Session tracking not working
- Check Flask logs for errors
- Verify `session_token` is in Flask session
- Check `user_sessions` table for new records

## 🚀 Future Enhancements (Optional)

1. Add "Logout all other sessions" button
2. Show list of active sessions in user profile
3. Add email notifications for new device logins
4. Add geolocation based on IP address
5. Add session expiration (auto-logout after X days)
