import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_supabase_client():
    """
    Creates and returns a Supabase client.
    """
    try:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            print("❌ Supabase credentials not found in .env file")
            return None
        
        client = create_client(url, key)
        return client
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        return None

# Legacy functions for backward compatibility (no-op)
def get_db_connection():
    """Legacy function - returns None. Use get_supabase_client() instead."""
    print("⚠️ Warning: get_db_connection() is deprecated. Use get_supabase_client() instead.")
    return None

def close_db_connection(connection, cursor=None):
    """Legacy function - no-op. Supabase connections are managed automatically."""
    pass

