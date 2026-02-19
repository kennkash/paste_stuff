# ------------------------------------------------------------
# 4. MERGE HR DATA (EMAIL FIRST, THEN NT_ID FALLBACK, DROP NON-MATCHES)
# ------------------------------------------------------------
params_hr = {"data_type": "pageradm_employee_ghr", "MLR": "L"}
user_data = getData(
params=params_hr,
custom_columns=["cost_center_name", "dept_name", "smtp", "title", "nt_id", "mysingle_id"],
custom_operators={"smtp": "notnull"},
)

# Make nt_id safe and unique
user_data["smtp"] = user_data["smtp"].astype(str).str.strip().str.lower()
user_data["nt_id"] = user_data["nt_id"].astype(str).str.strip().str.lower()

# Ensure unique nt_id to avoid multi-match explosions
user_data = (
    user_data.sort_values("nt_id")
    .drop_duplicates(subset=["nt_id"], keep="last")
)

# Normalize users keys
users["email_norm"] = users["email"].astype(str).str.strip().str.lower()
users["user_name_norm"] = users["user_name"].apply(normalize_username)

# 4a. Merge on email
merge_email = users.merge(
user_data,
left_on="email_norm",
right_on="smtp",
how="left",
indicator=True,
)

matched_email = merge_email[merge_email["_merge"] == "both"].copy()
unmatched_email = merge_email[merge_email["_merge"] == "left_only"].copy()

# Clean up unmatched (remove partially merged HR columns)
cols_to_remove = ["cost_center_name", "dept_name", "title", "smtp", "nt_id", "_merge"]
unmatched_email.drop(columns=[c for c in cols_to_remove if c in unmatched_email.columns], inplace=True)

# ---- 4b. Merge remaining rows on nt_id
merge_ntid = unmatched_email.merge(
user_data,
left_on="user_name_norm",
right_on="nt_id",
how="left",
indicator=True,
)

matched_ntid = merge_ntid[merge_ntid["_merge"] == "both"].copy()
unmatched_final = merge_ntid[merge_ntid["_merge"] == "left_only"].copy()

# ---- 4c. Keep ONLY rows that matched on email OR nt_id
users = pd.concat(
    [matched_email.drop(columns=["_merge"]), matched_ntid.drop(columns=["_merge"])],
    ignore_index=True
)

# ---- 4d. Drop users that fail BOTH merges
users.drop(columns=["email_norm", "user_name_norm"], inplace=True, errors="ignore")

print("Matched on email:", len(matched_email))
print("Matched on nt_id:", len(matched_ntid))
print("Dropped (no HR match):", len(unmatched_final))
