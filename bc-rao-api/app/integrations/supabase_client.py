"""
Supabase client for server-side database operations.
Uses service role key for bypassing RLS when needed.
"""
from typing import Optional
from supabase import create_client, Client
from app.config import settings


_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client instance with service role key.
    Uses lazy initialization pattern for efficiency.

    Returns:
        Supabase Client instance for server-side operations
    """
    global _supabase_client

    if _supabase_client is None:
        _supabase_client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY
        )

    return _supabase_client
