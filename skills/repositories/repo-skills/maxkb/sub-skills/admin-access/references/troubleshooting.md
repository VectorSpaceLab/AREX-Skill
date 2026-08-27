# Troubleshooting

## Common admin issues
- Login/profile/password-reset failures: check the auth route family and the UI login flow.
- Language switch not persisting: verify the user profile flow and stored locale.
- Missing data in folders or resource pages: confirm the workspace id and resource mapping.
- Homepage metrics are empty: check permissions, date range, and the correct workspace scope.
- OSS file retrieval/upload fails: confirm the file route, application id, and path prefix.
- Tool/trigger pages 403 or 404: confirm the permission group and the workspace-aware route.
- Email settings or system profile errors: verify the management endpoint and validation requirements.

## Safe response pattern
- Name the admin surface first.
- Then name the workspace, resource, or permission boundary.
- Then state whether the problem is routing, auth, or missing data.

## Do not do
- Do not merge tool/trigger runtime behavior into admin CRUD advice.
- Do not expose private file URLs or credentials.
