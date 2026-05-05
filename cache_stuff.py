# api/v0/endpoints/cache_mgmt.py
"""
Cache management endpoints for the Atlassian API.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from fastapi.responses import JSONResponse
from core.config import settings
from services.v0.admins.atlassianadmins import ADMIN_USERS

router = APIRouter()

def verify_cache_key(request: Request):
    """Verify the user is an admin."""
    current_user = request.headers.get("x-knox-id", None)
    
    if not current_user or current_user not in ADMIN_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Admin access required"
        )
    return current_user


@router.post("/clear-restricted-users", status_code=200)
async def clear_restricted_users_cache_endpoint(
    api_key: str = Depends(verify_cache_key)
) -> JSONResponse:
    """
    Clear the restricted users cache (Jira and Confluence).
    
    This endpoint forces a fresh query from HR data and API calls, bypassing the cached results.
    The cache automatically expires after 1 hour, but this allows manual invalidation for testing.
    
    Security:
        Requires X-Knox-ID header with valid admin key.
        
    Returns:
        JSONResponse: Success message with status
    """
    from services.util.cache_utils import clear_restricted_users_cache
    
    success = await clear_restricted_users_cache()
    status_code = 200 if success else 500
    message = ("Restricted users cache cleared successfully" 
               if success else "Failed to clear restricted users cache")
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "success" if success else "error",
            "message": message
        }
    )


@router.post("/clear-all", status_code=200)
async def clear_all_caches_endpoint(
    api_key: str = Depends(verify_cache_key)
) -> JSONResponse:
    """
    Clear all caches in the application.
    
    Use with caution as this affects all cached data, not just restricted users.
    
    Security:
        Requires X-Cache-Key header with valid API key.
        
    Returns:
        JSONResponse: Success message with status
    """
    from services.util.cache_utils import clear_all_caches
    
    success = await clear_all_caches()
    status_code = 200 if success else 500
    message = ("All caches cleared successfully" 
               if success else "Failed to clear all caches")
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "success" if success else "error",
            "message": message
        }
    )


@router.get("/stats", status_code=200)
async def get_cache_stats(
    api_key: str = Depends(verify_cache_key)
) -> JSONResponse:
    """
    Get statistics about the current cache state.
    
    Security:
        Requires X-Cache-Key header with valid API key.
        
    Returns:
        JSONResponse: Cache statistics including hit rate, miss rate, etc.
    """
    from services.util.cache_utils import cache_stats
    
    stats = await cache_stats()
    
    if stats:
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": stats
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to retrieve cache statistics"
            }
        )


@router.get("/keys", status_code=200)
async def get_cache_keys(
    api_key: str = Depends(verify_cache_key)
) -> JSONResponse:
    """
    Get all cache keys currently in the cache.
    
    Useful for debugging and understanding what is cached.
    
    Security:
        Requires X-Cache-Key header with valid API key.
        
    Returns:
        JSONResponse: List of cache keys
    """
    from services.util.cache_utils import get_cache_keys
    
    keys = await get_cache_keys()
    
    if keys:
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "count": len(keys),
                "keys": keys
            }
        )
    else:
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "count": 0,
                "keys": [],
                "message": "No cache keys found"
            }
        )







---------------


# services/util/cache_utils.py
"""
Cache utility functions for managing aiocache in the API service.
"""

from aiocache import caches

from aiocache.serializers import PickleSerializer
from typing import List, Optional


async def clear_all_caches() -> bool:
    """
    Clear all cached data from the default cache.
    
    Returns:
        bool: True if cache was cleared successfully, False otherwise
    """
    try:
        await caches.get('default').clear()
        print("All caches cleared successfully")
        return True
    except Exception as e:
        print(f"Error clearing all caches: {e}")
        return False


async def clear_restricted_users_cache() -> bool:
    """
    Clear specifically the restricted users cache (both Jira and Confluence).
    
    This forces a re-query from HR data and fresh API calls, bypassing the cached results.
    We clear the SimpleMemoryCache instance used by the restricted users functions.
    
    Returns:
        bool: True if cache was cleared successfully, False otherwise
    """
    try:
        # Clear the default cache that holds the restricted users data
        await caches.get('default').clear()
        
        print("Restricted users cache cleared successfully")
        return True
    except ImportError as e:
        print(f"Import error when clearing restricted users cache: {e}")
        return False
    except Exception as e:
        print(f"Error clearing restricted users cache: {e}")
        import traceback
        traceback.print_exc()
        return False


async def get_cache_keys() -> Optional[List[str]]:
    """
    Get all keys currently in the cache (for debugging purposes).
    
    Returns:
        Optional[List[str]]: List of cache keys, or None if error occurs
    """
    try:
        cache = caches.get('default')
        keys = await cache.keys('*')
        return keys
    except Exception as e:
        print(f"Error getting cache keys: {e}")
        return None


async def cache_stats() -> Optional[dict]:
    """
    Get statistics about the current cache state.
    
    Returns:
        Optional[dict]: Cache statistics, or None if error occurs
    """
    try:
        cache = caches.get('default')
        stats = await cache.stats()
        return stats
    except Exception as e:
        print(f"Error getting cache stats: {e}")
        return None
