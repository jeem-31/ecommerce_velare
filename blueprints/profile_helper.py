"""
Helper functions for user profile data
Shared across all account page blueprints
"""
from flask import session
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_config import get_supabase_client

def get_user_profile_data():
    """Get current logged-in user's profile data for sidebar display"""
    if 'user_id' not in session or not session.get('logged_in'):
        return None
    
    try:
        supabase = get_supabase_client()
        
        # Get user email
        user_response = supabase.table('users').select('email').eq('user_id', session['user_id']).execute()
        
        if not user_response.data:
            return None
        
        # Get buyer profile
        buyer_response = supabase.table('buyers').select('first_name, last_name, gender, phone_number, profile_image').eq('user_id', session['user_id']).execute()
        
        if not buyer_response.data:
            return None
        
        # Combine data
        profile = {
            'email': user_response.data[0]['email'],
            'first_name': buyer_response.data[0]['first_name'],
            'last_name': buyer_response.data[0]['last_name'],
            'gender': buyer_response.data[0]['gender'],
            'phone_number': buyer_response.data[0]['phone_number'],
            'profile_image': buyer_response.data[0]['profile_image']
        }
        
        return profile
    except Exception as e:
        print(f"❌ Error getting profile data: {e}")
        return None
