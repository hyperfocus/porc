# Plan-Then-Apply Enforcement in PORC

PORC enforces that a valid `plan` must run before any `apply` operation. This includes:

- Checking Mongo for a plan run matching the external ID
- Validating that the plan has not expired (time-based TTL)
- Verifying the plan matches the current blueprint hash
- Enforcing approval (if required) before `apply`

## Metadata Keys Used

- `external_id`: Provided by GitHub or Port
- `plan_status`: Recorded as 'success', 'failure', 'skipped'
- `approval_required`: Boolean flag
- `approval_record`: Optional change record ID (e.g., ServiceNow)

## Enforcement Logic

- If `plan_status` != 'success' → reject apply
- If `approval_required` = true → block until `approval_record` is present and validated