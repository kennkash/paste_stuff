SELECT
  g.group_name                     AS group_name,
  u.user_name                      AS username,
  u.display_name                   AS display_name,
  u.email_address                  AS email,
  u.directory_id                   AS user_directory_id
FROM cwd_group g
JOIN cwd_membership m
  ON m.parent_id = g.id
JOIN cwd_user u
  ON u.lower_user_name = m.lower_child_name
WHERE g.directory_id = 1
  AND m.membership_type = 'GROUP_USER'
ORDER BY g.group_name, u.user_name;