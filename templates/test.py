from supabase import create_client

SUPABASE_URL = "your_url"
SUPABASE_KEY = "your_key"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Supabase connected successfully")