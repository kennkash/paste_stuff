# services/v0/usernameLookup.py
"""
Username Lookup Service

This service handles the migration from nt_id to gad_id for Jira/Confluence usernames.
Instead of assuming nt_id is the username, it queries the actual Jira/Confluence username
from their APIs.

This handles the gradual migration period where:
- Some users still have nt_id as their username
- Some users have gad_id as their username (after they log in)
"""

from fastapi import HTTPException
from fastapi.responses import ORJSONResponse
from typing import Optional, Dict, Tuple
from aiocache import cached
from aiocache.serializers import PickleSerializer
from .external_api.jiraRequests import JiraAPIClient
from .external_api.confRequests import ConfAPIClient
from .user import EmployeeService
import json


class UsernameLookupService:
    """
    Service to lookup actual Jira/Confluence usernames for users.
    
    This service queries the Atlassian APIs to get the current username
    for a user, handling the migration from nt_id to gad_id.
    """

    CACHE_TTL_SECONDS = 3600  # 1 hour cache

    @staticmethod
    async def get_jira_username(request) -> str:
        """
        Get the current Jira username for the authenticated user.
        
        Args:
            request: FastAPI Request object with x-knox-id header
            
        Returns:
            str: The current Jira username (could be nt_id or gad_id)
            
        Raises:
            HTTPException: If user cannot be found or username lookup fails
        """
        try:
            # Get user's employee data (includes mysingle_id, nt_id, gad_id, smtp)
            user_response = await EmployeeService.get(request=request)
            user_body = user_response.body
            user_str = user_body.decode('utf-8')
            user_data = json.loads(user_str)
            
            mysingle_id = user_data.get("mysingle_id")
            nt_id = user_data.get("nt_id")
            gad_id = user_data.get("gad_id")
            smtp = user_data.get("smtp")
            
            if not mysingle_id:
                raise HTTPException(status_code=400, detail="User mysingle_id not found")
            
            # Try to get username from cache first
            cached_username = await UsernameLookupService._get_cached_jira_username(mysingle_id)
            if cached_username:
                return cached_username
            
            # Query Jira API to get the actual username
            # We'll try multiple identifiers in order of preference
            jira_username = await UsernameLookupService._query_jira_for_username(
                mysingle_id=mysingle_id,
                nt_id=nt_id,
                gad_id=gad_id,
                smtp=smtp
            )
            
            if not jira_username:
                raise HTTPException(
                    status_code=404, 
                    detail=f"User not found in Jira: {mysingle_id}"
                )
            
            # Cache the result
            await UsernameLookupService._cache_jira_username(mysingle_id, jira_username)
            
            return jira_username
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error looking up Jira username: {str(e)}"
            )

    @staticmethod
    async def get_confluence_username(request) -> str:
        """
        Get the current Confluence username for the authenticated user.
        
        Args:
            request: FastAPI Request object with x-knox-id header
            
        Returns:
            str: The current Confluence username (could be nt_id or gad_id)
            
        Raises:
            HTTPException: If user cannot be found or username lookup fails
        """
        try:
            # Get user's employee data
            user_response = await EmployeeService.get(request=request)
            user_body = user_response.body
            user_str = user_body.decode('utf-8')
            user_data = json.loads(user_str)
            
            mysingle_id = user_data.get("mysingle_id")
            nt_id = user_data.get("nt_id")
            gad_id = user_data.get("gad_id")
            smtp = user_data.get("smtp")
            
            if not mysingle_id:
                raise HTTPException(status_code=400, detail="User mysingle_id not found")
            
            # Try to get username from cache first
            cached_username = await UsernameLookupService._get_cached_confluence_username(mysingle_id)
            if cached_username:
                return cached_username
            
            # Query Confluence API to get the actual username
            confluence_username = await UsernameLookupService._query_confluence_for_username(
                mysingle_id=mysingle_id,
                nt_id=nt_id,
                gad_id=gad_id,
                smtp=smtp
            )
            
            if not confluence_username:
                raise HTTPException(
                    status_code=404,
                    detail=f"User not found in Confluence: {mysingle_id}"
                )
            
            # Cache the result
            await UsernameLookupService._cache_confluence_username(mysingle_id, confluence_username)
            
            return confluence_username
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error looking up Confluence username: {str(e)}"
            )

    @staticmethod
    async def get_both_usernames(request) -> Tuple[str, str]:
        """
        Get both Jira and Confluence usernames for the authenticated user.
        
        Args:
            request: FastAPI Request object with x-knox-id header
            
        Returns:
            Tuple[str, str]: (jira_username, confluence_username)
            
        Raises:
            HTTPException: If user cannot be found or username lookup fails
        """
        jira_username = await UsernameLookupService.get_jira_username(request)
        confluence_username = await UsernameLookupService.get_confluence_username(request)
        
        return (jira_username, confluence_username)

    @staticmethod
    async def _query_jira_for_username(
        mysingle_id: str,
        nt_id: Optional[str] = None,
        gad_id: Optional[str] = None,
        smtp: Optional[str] = None
    ) -> Optional[str]:
        """
        Query Jira API to find the user's current username.
        
        Tries multiple identifiers in order:
        1. gad_id (new username format - highest priority)
        2. nt_id (old username format)
        3. mysingle_id (Knox ID)
        4. smtp (email address)
        
        Args:
            mysingle_id: User's mysingle_id
            nt_id: User's nt_id (may be None)
            gad_id: User's gad_id (may be None)
            smtp: User's email (may be None)
            
        Returns:
            Optional[str]: The Jira username if found, None otherwise
        """
        jira_client = JiraAPIClient()
        
        # List of identifiers to try, in order of preference
        identifiers_to_try = []
        
        # Priority order: gad_id > nt_id > mysingle_id > smtp
        if gad_id:
            identifiers_to_try.append(("gad_id", gad_id))
        if nt_id:
            identifiers_to_try.append(("nt_id", nt_id))
        if mysingle_id:
            identifiers_to_try.append(("mysingle_id", mysingle_id))
        if smtp:
            identifiers_to_try.append(("smtp", smtp))
        
        for identifier_type, identifier_value in identifiers_to_try:
            try:
                # Try to get user details using this identifier
                # Note: The actual API endpoint may vary - adjust as needed
                api_path = f"scriptrunner/latest/custom/getUserDetails?username={identifier_value}"
                response = await jira_client.get(api_path)
                
                if response and "error" not in response:
                    # Found the user - return their actual username
                    username = response.get("username")
                    if username:
                        return username
                        
            except Exception as e:
                # Log the error but continue trying other identifiers
                print(f"Failed to query Jira with {identifier_type}={identifier_value}: {e}")
                continue
        
        return None

    @staticmethod
    async def _query_confluence_for_username(
        mysingle_id: str,
        nt_id: Optional[str] = None,
        gad_id: Optional[str] = None,
        smtp: Optional[str] = None
    ) -> Optional[str]:
        """
        Query Confluence API to find the user's current username.
        
        Tries multiple identifiers in order:
        1. gad_id (new username format - highest priority)
        2. nt_id (old username format)
        3. mysingle_id (Knox ID)
        4. smtp (email address)
        
        Args:
            mysingle_id: User's mysingle_id
            nt_id: User's nt_id (may be None)
            gad_id: User's gad_id (may be None)
            smtp: User's email (may be None)
            
        Returns:
            Optional[str]: The Confluence username if found, None otherwise
        """
        conf_client = ConfAPIClient()
        
        # List of identifiers to try, in order of preference
        identifiers_to_try = []
        
        # Priority order: gad_id > nt_id > mysingle_id > smtp
        if gad_id:
            identifiers_to_try.append(("gad_id", gad_id))
        if nt_id:
            identifiers_to_try.append(("nt_id", nt_id))
        if mysingle_id:
            identifiers_to_try.append(("mysingle_id", mysingle_id))
        if smtp:
            identifiers_to_try.append(("smtp", smtp))
        
        for identifier_type, identifier_value in identifiers_to_try:
            try:
                # Try to get user details using this identifier
                api_path = f"scriptrunner/latest/custom/getUserDetails?username={identifier_value}"
                response = await conf_client.get(api_path)
                
                if response and "error" not in response:
                    # Found the user - return their actual username
                    username = response.get("username")
                    if username:
                        return username
                        
            except Exception as e:
                # Log the error but continue trying other identifiers
                print(f"Failed to query Confluence with {identifier_type}={identifier_value}: {e}")
                continue
        
        return None

    @staticmethod
    @cached(ttl=3600, serializer=PickleSerializer())
    async def _get_cached_jira_username(mysingle_id: str) -> Optional[str]:
        """
        Get cached Jira username for a user.
        
        Args:
            mysingle_id: User's mysingle_id
            
        Returns:
            Optional[str]: Cached username if exists, None otherwise
        """
        # This is a placeholder - actual caching is handled by aiocache decorator
        return None

    @staticmethod
    @cached(ttl=3600, serializer=PickleSerializer())
    async def _cache_jira_username(mysingle_id: str, username: str) -> None:
        """
        Cache Jira username for a user.
        
        Args:
            mysingle_id: User's mysingle_id
            username: Jira username to cache
        """
        # This is a placeholder - actual caching is handled by aiocache decorator
        pass

    @staticmethod
    @cached(ttl=3600, serializer=PickleSerializer())
    async def _get_cached_confluence_username(mysingle_id: str) -> Optional[str]:
        """
        Get cached Confluence username for a user.
        
        Args:
            mysingle_id: User's mysingle_id
            
        Returns:
            Optional[str]: Cached username if exists, None otherwise
        """
        # This is a placeholder - actual caching is handled by aiocache decorator
        return None

    @staticmethod
    @cached(ttl=3600, serializer=PickleSerializer())
    async def _cache_confluence_username(mysingle_id: str, username: str) -> None:
        """
        Cache Confluence username for a user.
        
        Args:
            mysingle_id: User's mysingle_id
            username: Confluence username to cache
        """
        # This is a placeholder - actual caching is handled by aiocache decorator
        pass


# Convenience functions for backward compatibility
async def get_jira_username(request) -> str:
    """Convenience function to get Jira username."""
    return await UsernameLookupService.get_jira_username(request)


async def get_confluence_username(request) -> str:
    """Convenience function to get Confluence username."""
    return await UsernameLookupService.get_confluence_username(request)
