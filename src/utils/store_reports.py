import os
from supabase import create_client, Client

url: str = os.environ.get("DB_URL")
key: str = os.environ.get("DB_KEY")
supabase: Client = create_client()
