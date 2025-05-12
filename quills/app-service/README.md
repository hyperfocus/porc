# App Service Quill Templates

This directory contains Jinja2 templates for provisioning App Services.

## Templates and Required Variables

### 1.0.0/main.tf.j2
- `resource_group_name`
- `location`
- `vnet_name`
- `vnet_address_space`
- `app_subnet_prefix`
- `app_service_plan_name`
- `os_type`
- `app_service_plan_sku`
- `app_service_name`
- `runtime_version`
- `java_server`
- `custom_domain_name`
- `custom_domain_prefix`

### 1.0.0/terraform.tfvars.json.j2
- `resource_group_name`
- `location`
- `environment`
- `app_name`
- `vnet_name`
- `app_service_plan_name`
- `app_service_plan_sku`
- `app_service_name`
- `os_type`
- `runtime_stack`
- `runtime_version` 