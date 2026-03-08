"""Test script for multi-device login detection"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.supabase_helper import (
    create_user_session,
    get_active_sessions,
    check_new_device_login,
    deactivate_session
)
from blueprints.notification_helper import create_device_login_notification
from datetime import datetime
import secrets

def test_session_tracking():
    """Test the session tracking functionality"""
    print("=" * 60)
    print("🧪 TESTING MULTI-DEVICE LOGIN DETECTION")
    print("=" * 60)
    
    # Test user_id (use a real user_id from your database)
    test_user_id = 1  # Change this to a real user_id
    
    print(f"\n📋 Test User ID: {test_user_id}")
    
    # Test 1: Create first session (Chrome on Windows)
    print("\n" + "=" * 60)
    print("TEST 1: First Login (Chrome on Windows)")
    print("=" * 60)
    
    session_token_1 = secrets.token_urlsafe(32)
    device_info_1 = "Chrome on Windows"
    
    session_id_1 = create_user_session(
        user_id=test_user_id,
        session_token=session_token_1,
        device_info=device_info_1,
        browser="Chrome",
        os_name="Windows",
        ip_address="127.0.0.1"
    )
    
    if session_id_1:
        print(f"✅ Created session {session_id_1}")
    else:
        print("❌ Failed to create session")
        return
    
    # Check if new device (should be False - first login)
    is_new = check_new_device_login(test_user_id, device_info_1)
    print(f"🔍 Is new device? {is_new} (Expected: False)")
    
    # Test 2: Login from same device again
    print("\n" + "=" * 60)
    print("TEST 2: Second Login (Chrome on Windows - Same Device)")
    print("=" * 60)
    
    session_token_2 = secrets.token_urlsafe(32)
    
    session_id_2 = create_user_session(
        user_id=test_user_id,
        session_token=session_token_2,
        device_info=device_info_1,
        browser="Chrome",
        os_name="Windows",
        ip_address="127.0.0.1"
    )
    
    if session_id_2:
        print(f"✅ Created session {session_id_2}")
    
    is_new = check_new_device_login(test_user_id, device_info_1)
    print(f"🔍 Is new device? {is_new} (Expected: False)")
    
    # Test 3: Login from different device
    print("\n" + "=" * 60)
    print("TEST 3: Third Login (Firefox on Windows - Different Browser)")
    print("=" * 60)
    
    session_token_3 = secrets.token_urlsafe(32)
    device_info_3 = "Firefox on Windows"
    
    # Check BEFORE creating session
    is_new = check_new_device_login(test_user_id, device_info_3)
    print(f"🔍 Is new device? {is_new} (Expected: True)")
    
    session_id_3 = create_user_session(
        user_id=test_user_id,
        session_token=session_token_3,
        device_info=device_info_3,
        browser="Firefox",
        os_name="Windows",
        ip_address="127.0.0.1"
    )
    
    if session_id_3:
        print(f"✅ Created session {session_id_3}")
    
    # Create notification for new device
    if is_new:
        print("🔔 Creating notification for new device login...")
        create_device_login_notification(
            user_id=test_user_id,
            device_info=device_info_3,
            login_time=datetime.now()
        )
    
    # Test 4: Get all active sessions
    print("\n" + "=" * 60)
    print("TEST 4: Get All Active Sessions")
    print("=" * 60)
    
    active_sessions = get_active_sessions(test_user_id)
    print(f"📊 Active sessions: {len(active_sessions)}")
    
    for i, session in enumerate(active_sessions, 1):
        print(f"\n  Session {i}:")
        print(f"    - Device: {session.get('device_info')}")
        print(f"    - Browser: {session.get('browser')}")
        print(f"    - OS: {session.get('os')}")
        print(f"    - IP: {session.get('ip_address')}")
        print(f"    - Login: {session.get('login_time')}")
        print(f"    - Active: {session.get('is_active')}")
    
    # Test 5: Deactivate a session (logout)
    print("\n" + "=" * 60)
    print("TEST 5: Logout (Deactivate Session 1)")
    print("=" * 60)
    
    success = deactivate_session(session_token_1)
    if success:
        print(f"✅ Deactivated session 1")
    else:
        print(f"❌ Failed to deactivate session 1")
    
    # Check active sessions again
    active_sessions = get_active_sessions(test_user_id)
    print(f"📊 Active sessions after logout: {len(active_sessions)} (Expected: 2)")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 60)
    print("\n💡 Next Steps:")
    print("1. Check your notifications table for the new device notification")
    print("2. Login to the app from different browsers to test in real scenario")
    print("3. Check the user_sessions table to see all session records")

if __name__ == '__main__':
    try:
        test_session_tracking()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
