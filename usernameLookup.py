"""
Username Lookup Service

Handles Jira/Confluence username lookup during nt_id -> gad_id migration.

Source of truth:
- gad_id is preferred
- nt_id is fallback

The ScriptRunner endpoints accept usernames only, so smtp/email is intentionally
not checked.
"""

from typing import Optional, Tuple
from urllib.parse import quote_plus
import json

from fastapi import HTTPException
from aiocache import Cache
from aiocache.serializers import PickleSerializer

from .external_api.jiraRequests import JiraAPIClient
from .external_api.confRequests import ConfAPIClient
from .user import EmployeeService


class UsernameLookupService:
    """
    Service to lookup actual Jira/Confluence usernames for users.

    During migration:
    - Some Atlassian usernames may still be nt_id
    - Some Atlassian usernames may now be gad_id
    """

    CACHE_TTL_SECONDS = 3600

    _cache = Cache(
        Cache.MEMORY,
        serializer=PickleSerializer(),
        namespace="username_lookup",
    )

    @staticmethod
    async def get_jira_username(request) -> str:
        try:
            user_data = await UsernameLookupService._get_employee_data(request)

            gad_id = user_data.get("gad_id")
            nt_id = user_data.get("nt_id")

            if not gad_id:
                raise HTTPException(status_code=400, detail="User gad_id not found")

            cached_username = await UsernameLookupService._get_cached_username(
                system="jira",
                gad_id=gad_id,
            )
            if cached_username:
                return cached_username

            jira_username = await UsernameLookupService._query_jira_for_username(
                gad_id=gad_id,
                nt_id=nt_id,
            )

            if not jira_username:
                raise HTTPException(
                    status_code=404,
                    detail=f"User not found in Jira using gad_id={gad_id} or nt_id={nt_id}",
                )

            await UsernameLookupService._cache_username(
                system="jira",
                gad_id=gad_id,
                username=jira_username,
            )

            return jira_username

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error looking up Jira username: {str(e)}",
            )

    @staticmethod
    async def get_confluence_username(request) -> str:
        try:
            user_data = await UsernameLookupService._get_employee_data(request)

            gad_id = user_data.get("gad_id")
            nt_id = user_data.get("nt_id")

            if not gad_id:
                raise HTTPException(status_code=400, detail="User gad_id not found")

            cached_username = await UsernameLookupService._get_cached_username(
                system="confluence",
                gad_id=gad_id,
            )
            if cached_username:
                return cached_username

            confluence_username = await UsernameLookupService._query_confluence_for_username(
                gad_id=gad_id,
                nt_id=nt_id,
            )

            if not confluence_username:
                raise HTTPException(
                    status_code=404,
                    detail=f"User not found in Confluence using gad_id={gad_id} or nt_id={nt_id}",
                )

            await UsernameLookupService._cache_username(
                system="confluence",
                gad_id=gad_id,
                username=confluence_username,
            )

            return confluence_username

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error looking up Confluence username: {str(e)}",
            )

    @staticmethod
    async def get_both_usernames(request) -> Tuple[str, str]:
        jira_username = await UsernameLookupService.get_jira_username(request)
        confluence_username = await UsernameLookupService.get_confluence_username(request)

        return jira_username, confluence_username

    @staticmethod
    async def _get_employee_data(request) -> dict:
        user_response = await EmployeeService.get(request=request)
        user_body = user_response.body
        user_str = user_body.decode("utf-8")
        return json.loads(user_str)

    @staticmethod
    async def _query_jira_for_username(
        gad_id: str,
        nt_id: Optional[str] = None,
    ) -> Optional[str]:
        jira_client = JiraAPIClient()

        identifiers_to_try = UsernameLookupService._build_identifiers(
            gad_id=gad_id,
            nt_id=nt_id,
        )

        for identifier_type, identifier_value in identifiers_to_try:
            try:
                encoded_username = quote_plus(identifier_value)
                api_path = (
                    "scriptrunner/latest/custom/getUserDetails"
                    f"?username={encoded_username}"
                )

                response = await jira_client.get(api_path)

                username = UsernameLookupService._extract_username(response)
                if username:
                    return username

            except Exception as e:
                print(
                    f"Failed to query Jira with "
                    f"{identifier_type}={identifier_value}: {e}"
                )
                continue

        return None

    @staticmethod
    async def _query_confluence_for_username(
        gad_id: str,
        nt_id: Optional[str] = None,
    ) -> Optional[str]:
        conf_client = ConfAPIClient()

        identifiers_to_try = UsernameLookupService._build_identifiers(
            gad_id=gad_id,
            nt_id=nt_id,
        )

        for identifier_type, identifier_value in identifiers_to_try:
            try:
                encoded_username = quote_plus(identifier_value)
                api_path = (
                    "scriptrunner/latest/custom/getUserDetails"
                    f"?username={encoded_username}"
                )

                response = await conf_client.get(api_path)

                username = UsernameLookupService._extract_username(response)
                if username:
                    return username

            except Exception as e:
                print(
                    f"Failed to query Confluence with "
                    f"{identifier_type}={identifier_value}: {e}"
                )
                continue

        return None

    @staticmethod
    def _build_identifiers(
        gad_id: str,
        nt_id: Optional[str] = None,
    ) -> list[tuple[str, str]]:
        identifiers_to_try: list[tuple[str, str]] = []

        if gad_id:
            identifiers_to_try.append(("gad_id", gad_id))

        if nt_id and nt_id != gad_id:
            identifiers_to_try.append(("nt_id", nt_id))

        return identifiers_to_try

    @staticmethod
    def _extract_username(response) -> Optional[str]:
        if not response or not isinstance(response, dict):
            return None

        if response.get("error"):
            return None

        return (
            response.get("username")
            or response.get("name")
            or response.get("userName")
            or response.get("key")
        )

    @staticmethod
    def _cache_key(system: str, gad_id: str) -> str:
        return f"{system}:{gad_id.lower().strip()}"

    @staticmethod
    async def _get_cached_username(system: str, gad_id: str) -> Optional[str]:
        key = UsernameLookupService._cache_key(system, gad_id)
        return await UsernameLookupService._cache.get(key)

    @staticmethod
    async def _cache_username(system: str, gad_id: str, username: str) -> None:
        key = UsernameLookupService._cache_key(system, gad_id)
        await UsernameLookupService._cache.set(
            key,
            username,
            ttl=UsernameLookupService.CACHE_TTL_SECONDS,
        )


async def get_jira_username(request) -> str:
    return await UsernameLookupService.get_jira_username(request)


async def get_confluence_username(request) -> str:
    return await UsernameLookupService.get_confluence_username(request)
