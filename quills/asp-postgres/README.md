# ASP-Postgres Quill Templates

This directory contains Jinja2 templates for provisioning ASP.NET and Postgres resources.

## Templates and Required Variables

### 1.0.0/main.tf.j2
- `resource_group_name`
- `location`
- `vnet_name`
- `vnet_address_space`
- `app_subnet_prefix`
- `db_subnet_prefix`
- `app_service_plan_name`
- `app_service_plan_sku`
- `app_service_name`
- `dotnet_version`
- `db_name`
- `environment`
- `postgres_server_name`
- `postgres_version`
- `postgres_admin_user`
- `postgres_admin_password`
- `postgres_zone`
- `postgres_storage_mb`
- `postgres_sku_name`
- `postgres_backup_retention_days`
- `postgres_private_dns_zone`

### 1.0.0/terraform.tfvars.json.j2
- `resource_group_name`
- `location`
- `environment`
- `app_name`
- `vnet_name`
- `app_service_plan_name`
- `app_service_name`
- `postgres_server_name`
- `postgres_admin_user`
- `postgres_admin_password`
- `db_name` 