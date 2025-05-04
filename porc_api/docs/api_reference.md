# PORC API Reference

## 1. Blueprint Submission
`POST /blueprint`  
Submit a signed blueprint for validation and Terraform rendering.

## 2. Run Plan
`POST /run/{id}/plan`  
Trigger a Terraform plan for the given external or internal run ID.

## 3. Run Apply
`POST /run/{id}/apply`  
Apply the infrastructure only if a valid plan exists and (if required) approval is recorded.

## 4. Submit Approval
`POST /run/{id}/approve`  
Submit a ServiceNow change record or manual approval.

## 5. Metadata Lookup
`GET /run/{id}/metadata`  
Retrieve full state and metadata for the run.

## 6. Resolve ID
`GET /resolve?id=github:1234`  
Map a GitHub/Port ID to internal porc_run_id and metadata.

## 7. Logs & Events
`GET /run/{id}/logs`  
`GET /run/{id}/events`  
Retrieve debug and activity trail for the run.

## 8. Cleanup
`POST /cleanup?before=YYYY-MM-DD`  
Delete logs and stale state for expired runs.

## 9. Reporting & Metrics
`GET /metrics`  
`GET /report?team=team-name&range=30d`  
Deliver audit reports or usage metrics.