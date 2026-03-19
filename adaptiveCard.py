def extract_space_key_from_webui(webui: str) -> str:
    """
    Extracts the Confluence space key from a webui path like:
    /display/ABCD/page+name
    """
    parts = webui.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "display":
        return parts[1]
    return ""
    
    for result in response_json["results"]:
    page_id = result.get("id", "")
    title = result.get("title", "")
    webui = result["_links"].get("webui", "")
    space_key = extract_space_key_from_webui(webui)

    if page_id not in existing_approval_ids:
        new_approval = {
            "id": page_id,
            "title": title,
            "webui": f"{base_view_url}{page_id}",
            "approvers": [],
            "space": space_key,
        }
        new_approvals.append(new_approval)
        ids.append({"id": page_id})
        existing_approval_ids.add(page_id)
    else:
        existing_approval = next(
            (a for a in existing_approvals if a["id"] == page_id), None
        )
        if existing_approval:
            changed = False
            if existing_approval["title"] != title:
                existing_approval["title"] = title
                changed = True

            full_url = f"{base_view_url}{page_id}"
            if existing_approval["webui"] != full_url:
                existing_approval["webui"] = full_url
                changed = True

            if existing_approval.get("space") != space_key:
                existing_approval["space"] = space_key
                changed = True

            if changed:
                save_approvals_to_s3(existing_approvals)
    
    
    

def send_initial_notification(approval, approvers):
    """Sends an initial Jarvis alert to a defined list of users when a new page goes into approval"""

    pending_approvers = [
        user['user']
        for user in approvers
        if not user['approved'] and not user['rejected']
    ]

    nt_id_to_mysingle_id = knox_id(pending_approvers)
    pending_approvers_mysingle = [
        nt_id_to_mysingle_id.get(name, None) 
        for name in pending_approvers
    ]
    recipients = [id for id in pending_approvers_mysingle if id is not None]

    print("Pending Approvers: ", recipients)

    # Dynamic space from this page's approval data
    space = approval.get("space", "")

    for user in recipients:
        try:
            data: dict = {
                "confluenceLogo": _load_logo_b64(),
                "space": space,
                "pageTitle": f"{approval['title']} Submitted for Content Review",
                "title": approval["title"],
                "pageUrl": approval["webui"],
            }

            payload = {
                "adaptiveCards": adaptive_card,
                "data": json.dumps(data),
            }

            adaptive_card_push_request = PushRequest(
                msg=json.dumps(payload),
                type=PushType.ADAPTIVE_CARD,
                recipients=[user],
            )

            stats["jarvis_messages_sent"] += 1
            jarvis.chat_push_post(adaptive_card_push_request)
            print(f"Initial notification sent successfully to {user} for {approval['title']}")
        except ApiException as e:
            print("Exception when calling ChatApi->chat_push_post: %s\n" % e)
            print(f"Error sending reminder to {user}: {e}")




"""
Module to alert users when a page in Confluence enters an approval state and needs their review.

This script retrieves all users that are assigned as approvers for a page and alerts them via Jarvis 
that the page requires their review.

The script also checks if the approvers have been updated and sends a notification to new approvers if so.

Requires:
- bigdataloader2 package (pip install bigdataloader2)
- s2cloudapi package (pip install s2cloudapi)
- sas_jarvis package (pip install sas_jarvis)
- sas_auth_wrapper package (pip install sas_auth_wrapper)
- json, os

Variables to Update:
confluence_auth_token = 'YOUR_API_TOKEN_HERE'
bucket_name = 'YOUR BUCKET NAME' (e.g., s3 bucket you have read and write access to)
cql = 'YOUR CQL QUERY' (e.g., "state = 'Approval' AND space = 'ADMIN'")
space = 'SPACE YOU ARE SEARCHING' (e.g., space = 'Smart Cloud' -- used for alert header)
"""

from bigdataloader2 import *
import s2cloudapi.s3api as s3
from sas_jarvis import (
    Configuration,
    ApiClient,
    ApiException,
    ChatApi,
    PushRequest,
    PushType,
)
from sas_auth_wrapper import get_external_api_session
import json 
import os
import pathlib
import base64
import logging
from functools import lru_cache

# ============================================================== #
#                       Variable Definitions                     #
# ============================================================== #

stats = {
    "pages_with_approval": 0,      # pages that entered an approval state
    "pages_without_approvers": 0, # pages in approval state but no approvers set
    "jarvis_messages_sent": 0,    # total number of adaptive‑card pushes
}

# Get a requests.Session that will automatically add the extra authentication to each request
external_api_session = get_external_api_session()
# Defining Base URL for API call
base_url = "http://confluence.externalapi.smartcloud.samsungaustin.com"
# Defining Base URL for link to pages
baseUrl = "https://confluence.samsungaustin.com"
base_view_url = "https://confluence.samsungaustin.com/pages/viewpage.action?pageId="


# An auth token can be generated at http://confluence/plugins/personalaccesstokens/usertokens.action
# I'm saving my token as a variable in a creds.py file
# Put the below line in that file with the string as your auth token created above:
# confluence_auth_token = ""

#from creds import confluence_auth_token

# WARNING: The users token that is used in the script MUST have edit access for the space/pages being pulled or workflow visibility
header = {'Authorization': f'Bearer shhhh'}

# ================================================================ #
# WARNING: You will need to create an s3 bucket prior to execution #
# Once created you can delete the line below                       #
# s3.create_bucket('your-bucket-name')                             #
# ================================================================ #

# Defining the bucket_name as the one created 
bucket_name = 'pendingconfluenceapprovals'
# Defining the object_key for the json that will be uploaded to the bucket
object_key = 'approvals.json'

# Defining Jarvis config
configuration = Configuration(
    username=os.environ["AccessKey"],
    password=os.environ["IAMKEY"],
)
# Creating Jarvis configuration with credentials
jarvis = ChatApi(ApiClient(configuration))
 
# This assumes you have a local ComalaTemplate.json file
# The one referenced here is included in the repo
file_path: str = "ComalaTemplate.json"  # Reading local ComalaTemplate.json file for adaptive card styling
with open(file_path) as json_file:
    adaptive_card: str = json_file.read()


@lru_cache(maxsize=1)
def _load_logo_b64() -> str:
    """
    Read the PNG logo **once** and return a base‑64 string.
    The result is cached (lru_cache) so every later call is O(1).
    """
    logo_path = pathlib.Path("DMC_Icon.png")
    try:
        raw = logo_path.read_bytes()
        b64 = base64.b64encode(raw).decode()
        return f"data:image/png;base64,{b64}"
    except Exception as exc:                # pragma: no‑cover
        logging.error(f"Logo load failed ({logo_path}): {exc}")
        return ""                           # fallback – empty string means “no logo”
# ============================================================== #
#                        Retrieve KnoxID                         #
# ============================================================== #

def knox_id(users):
    """Fetching Knox ID for approvers - Jarvis uses Knox ID but Confluence returns NTID"""
    params = {'data_type': 'pageradm_employee_ghr',
            'MLR': 'L',
            'nt_id': users}
    custom_columns = ['mysingle_id', 'nt_id']
    df = getData(params=params, custom_columns=custom_columns)

    # Set 'nt_id' as the index for efficient lookups
    df.set_index('nt_id', inplace=True)
    nt_id_to_mysingle_id = df['mysingle_id'].to_dict()

    return nt_id_to_mysingle_id

# ============================================================== #
#                     Main Function Definitions                  #
# ============================================================== #

# --------------------------------------------------------------
# Helper: fetch a single “page” of Confluence search results
# --------------------------------------------------------------
def _search_confluence(cql: str, start: int = 0, limit: int = 25):
    """
    Calls the Confluence CQL search endpoint with pagination params.

    Parameters
    ----------
    cql   : str
        Your CQL query (e.g. "state = 'Approval' AND space = 'ADMIN'")
    start : int
        Zero‑based offset of the first result to return.
    limit : int
        Maximum number of results to return (Confluence caps this at 200,
        but we deliberately use 25 as requested).

    Returns
    -------
    dict
        The decoded JSON payload from Confluence.
    """
    api_path = (
        f"{base_url}/rest/api/content/search"
        f"?cql={cql}"
        f"&start={start}"
        f"&limit={limit}"
    )
    response = external_api_session.get(api_path, headers=header)
    response.raise_for_status()                # <-- raise if HTTP error
    return response.json()


# --------------------------------------------------------------
# Revised `getApprovals()` – now paginates in chunks of 25
# --------------------------------------------------------------
def getApprovals():
    """
    Pulls all pages matching the CQL query, 25 at a time.
    Updates the S3‑stored JSON file and fires Jarvis notifications
    for new or changed approvals.
    """
    # -----------------------------------------------------------------
    # 1️⃣  Your CQL – keep it exactly as you would normally use it.
    # -----------------------------------------------------------------
    cql = "state = 'In Progress' AND space = 'CMPDMC'"          # <-- replace with your real query

    # -----------------------------------------------------------------
    # 2️⃣  Pagination loop – keep requesting until `size < limit`
    # -----------------------------------------------------------------
    all_results = []                # will contain every result across pages
    start = 0
    limit = 25                      # <- the **hard‑coded** page size you asked for

    while True:
        page_json = _search_confluence(cql, start=start, limit=limit)

        # Confluence returns a dict with a `results` list and a total `size`
        results = page_json.get("results", [])
        all_results.extend(results)

        # If we received fewer than `limit` items we are on the last page
        if len(results) < limit:
            break

        # Otherwise move the offset forward and fetch the next chunk
        start += limit

    # -----------------------------------------------------------------
    # 3️⃣  From this point on the logic is exactly the same as the
    #     original implementation – only the source of `response_json`
    #     has changed.
    # -----------------------------------------------------------------
    if not all_results:
        # No pending approvals – clean up S3 just like the original script.
        print("No pending approvals -- cleaning up S3")
        if s3.chk_file_exist(bucket=bucket_name, key=object_key):
            s3.delete_file(bucket=bucket_name, key=object_key)
            empty_approvals = []
            s3.upload_object(
                object_data=json.dumps(empty_approvals, indent=4),
                bucket=bucket_name,
                key=object_key,
            )
        return []

    # -------------------------------------------------
    # The rest of the function is unchanged, but we
    # replace the old `response_json` variable with the
    # combined list we just built.
    # -------------------------------------------------
    response_json = {"results": all_results}

    # -----------------------------------------------------------------
    # Existing approval handling (unchanged from your original code)
    # -----------------------------------------------------------------
    # Track pages that need approval
    ids = []
    new_approvals = []

    try:
        # Get existing approvals from S3
        existing_approvals = s3.get_object(bucket=bucket_name, key=object_key)
        existing_approvals = (
            json.loads(existing_approvals["Body"].read())
            if existing_approvals
            else []
        )
        print("Existing Approvals: ", existing_approvals)
    except Exception as e:
        print(f"Could not load existing approvals from S3: {e}")
        existing_approvals = []

    current_page_ids = {result["id"] for result in response_json["results"]}
    print(f"Pages pending review: {current_page_ids}")

    # Identify approvals to delete if they no longer exist in Confluence
    approvals_to_delete = [
        approval
        for approval in existing_approvals
        if approval["id"] not in current_page_ids
    ]

    if approvals_to_delete:
        # Remove deleted approvals from list
        existing_approvals = [
            approval
            for approval in existing_approvals
            if approval not in approvals_to_delete
        ]
        save_approvals_to_s3(existing_approvals)

    existing_approval_ids = {approval["id"] for approval in existing_approvals}

    # -----------------------------------------------------------------
    # Process each page returned by the paginated query
    # -----------------------------------------------------------------
    for result in response_json["results"]:
        page_id = result.get("id", "")
        title = result.get("title", "")
        webui = result["_links"].get("webui", "")

        if page_id not in existing_approval_ids:
            # New approval – add placeholder, will be enriched later
            new_approval = {
                "id": page_id,
                "title": title,
                "webui": f"{base_view_url}{page_id}",
                "approvers": [],
            }
            new_approvals.append(new_approval)
            ids.append({"id": page_id})
            existing_approval_ids.add(page_id)
        else:
            # Existing – check for title / URL changes
            existing_approval = next(
                (a for a in existing_approvals if a["id"] == page_id), None
            )
            if existing_approval:
                changed = False
                if existing_approval["title"] != title:
                    existing_approval["title"] = title
                    changed = True
                # store fully‑qualified URL for consistency
                
                full_url = f"{base_view_url}{page_id}"
                if existing_approval["webui"] != full_url:
                    existing_approval["webui"] = full_url
                    changed = True
                if changed:
                    save_approvals_to_s3(existing_approvals)

    # -------------------------------------------------
    # Append new approvals and persist the JSON file
    # -------------------------------------------------
    existing_approvals += new_approvals
    print("Updating Approval JSON")
    save_approvals_to_s3(existing_approvals)

    # -------------------------------------------------
    # Send notifications (same flow as before)
    # -------------------------------------------------
    if new_approvals:
        for new_approval in new_approvals:
            process_approval(new_approval["id"], is_new=True)

    # Existing approvals (including the ones we may have just updated)
    for approval in existing_approvals:
        if approval not in new_approvals:
            process_approval(approval["id"], is_new=False)

    return existing_approvals


def process_approval(page_id, is_new=False):
    """Helper function to process each approval based on whether it's new or existing"""

    # Pulling the approval status for the page id
    api_path = f"{base_url}/rest/cw/1/content/{page_id}/status?expand=approvals"
    response = external_api_session.get(api_path, headers=header)
    response_json = response.json()

    # Check if page is in approval state
    approval_state = response_json.get('approvals', [])
    if not approval_state:
        print(f"Not in an approval state for page ID: {page_id}")
        # Retrieve existing approvals from S3
        existing_approvals = s3.get_object(bucket=bucket_name, key=object_key)
        existing_approvals = json.loads(existing_approvals['Body'].read()) if existing_approvals else []
        # Remove the page ID from existing_approvals
        updated_approvals = [approval for approval in existing_approvals if approval['id'] != page_id]
        # Save the updated list back to S3
        save_approvals_to_s3(updated_approvals)
        return
    
    stats["pages_with_approval"] += 1

    # Check if page has approvers assigned
    pop_approval = response_json['approvals'][0]
    pop_approvers = pop_approval.get('approvers', [])
    if not pop_approvers:
        print(f"No approvers set for page ID: {page_id}")
        stats["pages_without_approvers"] += 1
        # If no approvers, set the approvers field to an empty list in existing_approvals
        existing_approvals = s3.get_object(bucket=bucket_name, key=object_key)
        existing_approvals = json.loads(existing_approvals['Body'].read()) if existing_approvals else []
        # Find and modify the entry with the matching page_id
        updated_approvals = []
        for approval in existing_approvals:
            if approval['id'] == page_id:
                approval['approvers'] = []
            updated_approvals.append(approval)
        # Save the updated list back to S3
        save_approvals_to_s3(updated_approvals)
        
        return
        
    approvers = []
    for approver in pop_approvers:
        approvers.append({
            'user': approver['user']['name'],
            'approved': approver['approved'],
            'rejected': approver['rejected']
        })
        
    # Update approval data
    update_approval_data(page_id, approvers, is_new)
    
def update_approval_data(page_id, approvers, is_new=False):
    """Updates approval data in S3 with new approvers"""

    # Get existing approvals
    response = s3.get_object(bucket=bucket_name, key=object_key)
    approvals_data = json.loads(response['Body'].read())
    
     # Iterate through each approval entry to find the matching page ID
    for i in range(len(approvals_data)):
        if approvals_data[i]['id'] == page_id:
            # Extract the existing approvers' usernames
            existing_appr = [appr["user"] for appr in approvals_data[i].get('approvers', [])]
            # Extract the new approvers' usernames
            new_appr = [appr["user"] for appr in approvers if appr.get("user")]
            # Determine which users are new approvers
            new_users = [user for user in new_appr if user not in existing_appr]
            
            # If there are new approvers, send them notifications
            if new_users:
                for new_user in new_users:
                    # Find the corresponding approver's details
                    for appr in approvers:
                        if appr['user'] == new_user:
                            # Check if this is a new approval or if the user hasn't been alerted before
                            if is_new or (new_user not in existing_appr):
                                print(f"Alerting for approval: {approvals_data[i]['title']} - {approvals_data[i]['webui']}")
                                send_initial_notification(approvals_data[i], [appr])
                                break  # Move to the next new user after sending notification
            
            # Update the approvers list for the current page
            approvals_data[i]['approvers'] = approvers
            break  # Exit the loop after updating the current page's data
            
    # Save the updated approval data back to S3
    print(f'Updating Approvers for Page ID: {page_id}')
    save_approvals_to_s3(approvals_data)
    
    # Return the updated approval data
    return approvals_data


# ============================================================== #
#                     Jarvis Notification Function               #
# ============================================================== #

def send_initial_notification(approval, approvers):
    """Sends an initial Jarvis alert to a defined list of users when a new page goes into approval"""

    # Getting a list of approvers who have not rejected or approved the content yet
    pending_approvers = [
        user['user']
        for user in approvers
        if not user['approved'] and not user['rejected']
    ]
    # Retrieving the Knox IDs of the users who have not acted on the pending approval
    nt_id_to_mysingle_id = knox_id(pending_approvers)
    pending_approvers_mysingle = [
        nt_id_to_mysingle_id.get(name, None) 
        for name in pending_approvers
    ]
    recipients = [id for id in pending_approvers_mysingle if id is not None]
    
    print("Pending Approvers: ", recipients)

    # Setting the header for alert
    space = "Document Management Center"

    for user in recipients:
        try:
            # Populate the adaptive card template with data
            data: dict = {
                "confluenceLogo": _load_logo_b64(),
                "space": space,
                "pageTitle": f"{approval['title']} Submitted for Content Review",
                "title": approval["title"],
                "pageUrl": approval["webui"],
            }
            # Configure the payload - adaptive_card represents the template
            payload = {
                "adaptiveCards": adaptive_card,
                "data": json.dumps(data),
            }
            # Define msg, type, and recipients of the alert
            adaptive_card_push_request = PushRequest(
                msg=json.dumps(payload),
                type=PushType.ADAPTIVE_CARD,
                recipients=[user], # By using a for loop, messages are sent to individuals seperately rather than in a group IM
            )
            # Send the initial alert
            stats["jarvis_messages_sent"] += 1
            jarvis.chat_push_post(adaptive_card_push_request)
            print(f"Initial notification sent successfully to {user} for {approval['title']}")
        except ApiException as e:
            print("Exception when calling ChatApi->chat_push_post: %s\n" % e)
            print(f"Error sending reminder to {user}: {e}")

# ============================================================== #
#                     Save to S3 Bucket Function                 #
# ============================================================== #

def save_approvals_to_s3(approvals):
    """Saves the approval data to S3 bucket"""
    
    try:
        # Delete existing object
        s3.delete_file(bucket=bucket_name, key=object_key)
        # Upload the approval data as a JSON file to S3
        s3.upload_object(
            object_data=json.dumps(approvals, indent=4),
            bucket=bucket_name,
            key=object_key
        )
    except Exception as e:
        print(f"Error saving approvals to S3: {e}")


# Get all approvals, send initial notifications for new pages & send notifications for approvers added later on
approvals = getApprovals()
print("\n=== Confluence‑Approval Summary ===")
print(f"Pages that entered an approval state            : {stats['pages_with_approval']}")
print(f"Pages in approval state **without** approvers  : {stats['pages_without_approvers']}")
print(f"Jarvis adaptive‑card messages sent            : {stats['jarvis_messages_sent']}")
print("====================================")
