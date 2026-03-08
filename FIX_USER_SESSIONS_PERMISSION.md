# Fix User Sessions Permission Error

## Problem
```
❌ Error creating user session: {'message': 'permission denied for sequence user_sessions_session_id_seq', 'code': '42501'}
```

## Root Cause
Ang `user_sessions` table ay gumagamit ng `SERIAL` type para sa `session_id`, which creates a sequence. Ang Supabase ay may restrictions sa sequence permissions.

## Solutions

### Option 1: Grant Sequence Permissions (Quick Fix)
Run this sa Supabase SQL Editor:

```sql
-- Grant permissions on the sequence
GRANT USAGE, SELECT ON SEQUENCE user_sessions_session_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE user_sessions_session_id_seq TO service_role;
GRANT USAGE, SELECT ON SEQUENCE user_sessions_session_id_seq TO anon;
```

File: `database/fix_user_sessions_permissions.sql`

### Option 2: Recreate Table with Identity Column (Recommended)
Mas better solution - use `GENERATED ALWAYS AS IDENTITY` instead of `SERIAL`:

1. Backup existing data (if any):
```sql
-- Check if may data
SELECT * FROM user_sessions;
```

2. Run the alternative fix:
```sql
-- See file: database/fix_user_sessions_alternative.sql
```

This creates:
- Table with `BIGINT GENERATED ALWAYS AS IDENTITY` (no sequence issues)
- Row Level Security policies
- Proper indexes
- Correct permissions

### Option 3: Disable Session Tracking (Temporary)
Kung gusto mo muna i-disable ang session tracking:

Sa `blueprints/auth.py`, comment out ang session creation:
```python
# === MULTI-DEVICE LOGIN DETECTION ===
# try:
#     from database.supabase_helper import create_user_session, check_new_device_login
#     ...
# except Exception as e:
#     print(f"⚠️ Session tracking error: {e}")
```

## Testing
After applying the fix:

1. Try to login
2. Check console - dapat walang error na
3. Verify sa database:
```sql
SELECT * FROM user_sessions ORDER BY login_time DESC LIMIT 5;
```

## Notes
- Option 2 is recommended kasi mas compatible sa Supabase
- `GENERATED ALWAYS AS IDENTITY` is the modern PostgreSQL way
- Walang sequence permission issues with identity columns
