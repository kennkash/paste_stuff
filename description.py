description = f"""
h2. Spotfire License Request

*Submitter:* {request.submitter}
*Submitted On:* {request.submit_date}

h3. Requested Users
{chr(10).join(f"- {u}" for u in raw_requested_users)}

h3. License Type
{license_type or "N/A"}

h3. Exception Categories
{", ".join(exception_categories) if exception_categories else "None"}

h3. Exception Details
{exception_details or "None"}
"""
