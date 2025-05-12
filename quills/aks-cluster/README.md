# AKS Cluster Quill Templates

This directory contains Jinja2 templates for provisioning AKS clusters.

## Templates and Required Variables

### 1.0.0/main.tf.j2
- `resource_group_name`
- `location`
- `environment`
- `app_name`
- `vnet_name`
- `vnet_address_space`
- `subnet_prefix`
- `cluster_name`
- `kubernetes_version`
- `node_count`
- `node_vm_size`
- `enable_auto_scaling`
- `min_count`
- `max_count`
- `network_plugin`
- `network_policy`
- `dns_service_ip`
- `service_cidr`
- `pod_cidr`

### 1.0.0/terraform.tfvars.json.j2
- `resource_group_name`
- `location`
- `vnet_name`
- `cluster_name`
- `kubernetes_version`
- `node_count`
- `node_vm_size`
- `enable_auto_scaling`
- `min_count`
- `max_count`
- `network_plugin`
- `network_policy`
- `dns_service_ip`
- `service_cidr`
- `pod_cidr`
- `environment`
- `app_name` 