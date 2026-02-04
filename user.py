# api/v0/endpoints/user.py
from fastapi import APIRouter, Request
from fastapi.responses import ORJSONResponse
from services.util.errorResponse import error_response_noarg
from services.v0.user import EmployeeService

router = APIRouter()


@router.get("", status_code=200, summary="Get current user information", responses=error_response_noarg(), tags=["secure"])
async def fetch_user(*, request: Request) -> ORJSONResponse:
    """
    fetch_user get the user information for the individual that made the request

    Args:
        request (Request): fastapi request payload

    Returns ORJSONResponse:
        
        {
            "ghr_id": "12345678",

            "full_name": "John Doe",

            "cost_center_name": "Manufacturing System",

            "title": "Engineer I",

            "mysingle_id": "j.doe",
            
            "nt_id": "jdoe123",

            "user": "j.doe"
        }
    """
    result = await EmployeeService.get(request=request)
    return result

# services/v0/user.py
import pandas as pd
from fastapi import HTTPException, Request
from fastapi.responses import ORJSONResponse
from bigdataloader2 import getData


class EmployeeService:
    """
     Basic emplyee service function to get employee data

    Returns:
        dict: requestor employee data
    """

    @staticmethod
    async def get(request: Request) -> ORJSONResponse:
        """
        get employee information from bdl pageradm_employee_ghr

        Args:
            request (Request): api request with x-knox-id check

        Returns:
            ORJSONResponse: response containing employee information
        """
        data = pd.DataFrame()
        try:
            current_user = request.headers.get("x-knox-id", None)
            print("Current knox id:", current_user)
        except HTTPException:
            print("No user found!")
            # no user was provided, return empty
            return ORJSONResponse(content={"No user found"})

        # query the employee data
        params = {
            "data_type": "pageradm_employee_ghr",
            "MLR": "L",
            "mysingle_id": current_user
        }
        columns = ["ghr_id", "full_name", "cost_center_name", "title", "mysingle_id", "nt_id", "smtp"]
        data = getData(params=params, convert_type=True, custom_columns=columns)

        # set default
        result = {}

        # tack on the user id
        if not data.empty:
            data["user"] = current_user
            result = data.to_dict("records")[0]  # only want the first row

        return ORJSONResponse(content=result)
