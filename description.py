# api/v0/endpoints/ticket.py
from fastapi import APIRouter, HTTPException
from bigdataloader2 import getData
from pydantic import BaseModel
from s2cloudapi import cloudSmtp as smtp
from services.v0.external_api.jiraRequests import JiraAPIClient
from typing import List, Optional, Union
import tempfile
import os



jira_client = JiraAPIClient()
router = APIRouter()


def user_cost_centers(user):
    params = {
        "data_type": "pageradm_employee_ghr", 
        "MLR": "L", 
        "gad_id": user,
        'employee_type_name': '%Dispatcher%',
        'status_name': 'Active',}
    custom_columns = [
        "full_name",
        "smtp",
        "status_name",
        "nt_id",
        "gad_id",
        "cost_center_name",
        "dept_name",
        "title",
    ]
    return getData(params=params, custom_columns=custom_columns)

def dispatcher(user):
    params = {
        "data_type": "pageradm_employee_ghr", 
        "MLR": "L", 
        "gad_id": user,
        'employee_type_name': '%Dispatcher%',
        'status_name': 'Active',}
    custom_columns = [
        "employee_type_name",
    ]
    return getData(params=params, custom_columns=custom_columns)

def format_user_information(raw_requested_users: list[str]) -> str:
    sections = []

    for user in raw_requested_users:
        try:
            df = user_cost_centers(user)

            if df is None or df.empty:
                sections.append(
                    f"""*{user}*
- Status: Not found in HR data
"""
                )
                continue

            row = df.iloc[0]

            full_name = row.get("full_name") or "N/A"
            email = row.get("smtp") or "N/A"
            status = row.get("status_name") or "N/A"
            nt_id = row.get("nt_id") or "N/A"
            gad_id = row.get("gad_id") or user
            cost_center = row.get("cost_center_name") or "N/A"
            department = row.get("dept_name") or "N/A"
            title = row.get("title") or "N/A"

            sections.append(
                f"""*{full_name}* ({gad_id})
- Username: {user}
- NT ID: {nt_id}
- Email: {email}
- Status: {status}
- Cost Center: *{cost_center}*
- Department: {department}
- Title: {title}
"""
            )

        except Exception as e:
            sections.append(
                f"""*{user}*
- Status: Error loading HR data: {str(e)}
"""
            )

    return "\n".join(sections)


# Define the ResponseItem model
class ResponseItem(BaseModel):
    question: str
    answer: Optional[Union[str, List[str]]]

# Define the main request model
class SpotfireRequest(BaseModel):
    form_title: str
    submit_date: str
    submitter: str
    responses: List[ResponseItem]

async def verify_user(username: str) -> Optional[str]:
    """
    Verify if a user exists in Jira by username.
    If not found, checks in bigdataloader2 and attempts verification with the found nt_id.
    Returns the verified username or None if not found.
    """
    
    # First check if the user exists in Jira
    try:
        jira_response = await jira_client.get(f"api/2/user/search?username={username}")
        if jira_response and len(jira_response) > 0:
            return jira_response[0]['name']
    except Exception as e:
        print(f"Error checking user {username} in Jira: {str(e)}")

    # If not found in Jira, search in bigdataloader2
    try:
        params = {
            "data_type": "pageradm_employee_ghr",
            "MLR": "L",
            "mysingle_id": username,
        }
        columns = ["nt_id"]
        data = getData(params=params, convert_type=True, custom_columns=columns)

        if data and len(data) > 0:
            nt_id = data[0]['nt_id']
            # Verify if the nt_id exists in Jira
            try:
                jira_response = await jira_client.get(f"api/2/user/search?username={nt_id}")
                if jira_response and len(jira_response) > 0:
                    return nt_id
            except Exception as e:
                print(f"Error checking nt_id {nt_id} in Jira: {str(e)}")
    except Exception as e:
        print(f"Error checking user {username} in bigdataloader2: {str(e)}")

    print(f"Could not find user: {username}")
    return None

@router.post('/spotfire', status_code=201, summary="Submit a Spotfire License Request Jira ticket to WMPR via Cloud")
async def putSpotfireTicket(request: SpotfireRequest):
    # Process responses to map to Jira fields
    verified_users = []
    raw_requested_users = []
    license_type = None
    exception_categories = []
    exception_details = None

    # Process all responses
    for response in request.responses:
        # Skip the info box question
        if response.question == "Spotfire License Request":
            continue

        # Convert answer to list if it's a single string
        answer = response.answer
        if isinstance(answer, str):
            answer = [answer]

        if response.question == "User(s) to Request License For":
            # Process the users
            for user in answer:
                # Split if multiple users are comma-separated
                for u in user.split(','):
                    # Remove whitespace and verify the user
                    clean_user = u.strip()
                    if clean_user:
                        raw_requested_users.append(clean_user)
                        verified_username = await verify_user(clean_user)
                        if verified_username:
                            verified_users.append({
                                "name": verified_username
                            })

        elif response.question == "License Type":
            # Get the first answer if it exists
            license_type = answer[0] if answer else None

        elif response.question == "Exception Category":
            # Split comma-separated values into individual categories
            for category in answer:
                for cat in category.split(','):
                    exception_categories.append(cat.strip())

        elif response.question == "Exception Details":
            # Get the first answer if it exists
            exception_details = answer[0] if answer else None

    # Validate required fields
    if not verified_users:
        raise HTTPException(status_code=400, detail="Could not verify any users in the request")

    # Verify the submitter
    verified_reporter = await verify_user(request.submitter)
    if not verified_reporter:
        raise HTTPException(status_code=400, detail="Could not verify the submitter (reporter)")

    user_information = format_user_information(raw_requested_users)
    
    if request.form_title == 'Spotfire License Exception Request':
        description = f"""
                        h2. Admin Checks
                        
                        h3. Criteria for Approval

                        Requested user(s) must be in the following cost centers:
                        - Defect Reduction
                        - Device
                        - Product Operations
                        - Defect Quality & Systems
                        - PE

                        h3. Requested Users
                        {chr(10).join(f"- {u}" for u in raw_requested_users)}

                        h3. User(s) Information
                        {user_information}
                        
                        h3. Submitter
                        {request.submitter}

                    """
    elif request.form_title == 'Temporary Spotfire License Request':
        description = f"""
                        h2. Admin Checks
                        
                        h3. Criteria for Approval
                        
                        Requested user(s) must be an Expat or the exception must be for HQ work

                        h3. Requested Users
                        {chr(10).join(f"- {u}" for u in raw_requested_users)}
                        
                        h3. User(s) Information
                        {user_information}

                        h3. Expat?
                        

                        h3. Exception Categories
                        {", ".join(exception_categories) if exception_categories else "None"}

                        h3. Exception Details
                        {exception_details or "None"}
                    """

    # Build the Jira payload
    payload = {
        "fields": {
            "project": {
                "key": "WMPR"
            },
            "summary": request.form_title,
            "description": description,
            "customfield_10503": "wmpr/11b311d0-d759-4613-af2a-3cc82e0c4e2d",
            "issuetype": {
                "name": "Service Request with Approvals"
            },
            "customfield_14809": ", ".join(raw_requested_users), # Raw user names
            "customfield_11811": verified_users,  # Users field
            "reporter": {
                "name": verified_reporter
            }
        }
    }

    # Add License Type if it exists (single select field)
    if license_type:
        # For single select fields, we need to pass the value in a specific format
        # We'll try both the value directly and with a value wrapper based on what works
        payload["fields"]["customfield_11215"] = {"value": license_type}

    # Add Exception Categories if they exist (multi-select checkboxes)
    if exception_categories:
        # For multi-select checkbox fields, we need to pass each value individually
        payload["fields"]["customfield_13916"] = [{"value": cat} for cat in exception_categories]

    # Add Exception Details if they exist (multi-line text field)
    if exception_details:
        payload["fields"]["customfield_15207"] = exception_details

    # Make the Jira API call
    try:
        r = await jira_client.post("api/latest/issue", payload)

        # Handle the ResponseData object correctly
        if not r or not r.json:
            raise ValueError("Jira returned an empty response")

        if r.status_code != 201:
            error_info = r.text
            if r.json and r.json.get('errorMessages'):
                error_info = "\n".join(r.json['errorMessages'])
            raise ValueError(f"Jira API error (status {r.status_code}): {error_info}")

        if "key" not in r.json:
            raise ValueError("Invalid response from Jira - no key field found")

        key = r.json["key"]
        url = f"https://jira.samsungaustin.com/plugins/servlet/desk/portal/14/{key}"
        hyperlink = f'<a href="{url}" target="_blank">{key}</a>'

        # Prepare email content
        html_string = f'<style></style><body>Hi {request.submitter}!<br><br>Thank you for submitting a spotfire license request for: <strong>{", ".join(u["name"] for u in verified_users)}</strong><br><br>Your ticket has been received and will be addressed as it moves through our queue. You can monitor the status of your ticket here: {hyperlink}</body>'
        signage = f'<style></style><body><br><br>Additionally, you\'ll receive emails from Jira when updates are made to your ticket.<br><br><br><br>Best Regards,<br>Spotfire Administrators</body>'

        test_html = html_string + '<br>' + signage

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_file:
            temp_file.write(test_html)
            temp_file_path = temp_file.name

        try:
            smtp.sendEmail(
                toUsers=f'{request.submitter}@samsung.com',
                subject=f'Spotfire License Request Received',
                bodyHtmlFile=temp_file_path,
                appendUserRecipient="FALSE"
            )
        finally:
            os.unlink(temp_file_path)  
        return r.json  # Return the parsed JSON response

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"Error creating Jira ticket: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Error creating Jira ticket: {error_msg}")
