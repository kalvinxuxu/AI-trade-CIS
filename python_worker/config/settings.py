from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "")
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "")
AKSHARE_MODE = os.getenv("AKSHARE_MODE", "free")
