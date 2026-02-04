from fastapi import HTTPException, Request
from fastapi.responses import ORJSONResponse
from bigdataloader2 import getData

class EmployeeService:
    @staticmethod
    async def get(request: Request) -> ORJSONResponse:
        current_user = request.headers.get("x-knox-id")
        if not current_user:
            # critical: do NOT return 200 {}
            raise HTTPException(status_code=401, detail="Missing x-knox-id")

        params = {
            "data_type": "pageradm_employee_ghr",
            "MLR": "L",
            "mysingle_id": current_user,
        }
        columns = ["ghr_id", "full_name", "cost_center_name", "title", "mysingle_id", "nt_id", "smtp"]
        data = getData(params=params, convert_type=True, custom_columns=columns)

        if data.empty:
            # user header existed but no record
            raise HTTPException(status_code=404, detail=f"User not found: {current_user}")

        data["user"] = current_user
        result = data.to_dict("records")[0]

        return ORJSONResponse(content=result, headers={"Cache-Control": "no-store"})