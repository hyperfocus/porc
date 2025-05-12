# Postgres DB Quill Templates

This directory contains Jinja2 templates for provisioning Postgres databases.

## Templates and Required Variables

### main.tf.j2
- `db_name`
- `db_user`
- `plan`
- `environment`

### terraform.tfvars.json.j2
- `db_name`
- `db_user`
- `plan`
- `environment`

## 1.0.0/main.tf.j2
- `resource_group_name`
- `location`
- `environment`
- `app_name`
- `vnet_name`
- `vnet_address_space`
- `db_subnet_prefix`
- `postgres_server_name`
- `postgres_version`
- `postgres_admin_user`
- `postgres_admin_password`
- `postgres_zone`
- `postgres_storage_mb`
- `postgres_sku_name`
- `postgres_backup_retention_days`
- `postgres_private_dns_zone`
- `db_name`

## 1.0.0/terraform.tfvars.json.j2
- `resource_group_name`
- `location`
- `environment`
- `app_name`
- `vnet_name`
- `postgres_server_name`
- `postgres_admin_user`
- `postgres_admin_password`
- `db_name` 