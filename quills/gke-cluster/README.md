# GKE Cluster Quill Templates

This directory contains Jinja2 templates for provisioning GKE clusters.

## Templates and Required Variables

### main.tf.j2
- `cluster_name`
- `region`
- `node_count`

### terraform.tfvars.json.j2
- `cluster_name`
- `region`
- `node_count`

## 1.0.0/main.tf.j2
- `project_id`
- `region`
- `vpc_name`
- `subnet_name`
- `subnet_cidr`
- `pods_cidr`
- `services_cidr`
- `cluster_name`
- `master_cidr`
- `authorized_cidr`
- `node_pool_name`
- `node_count`
- `machine_type`
- `disk_size_gb`
- `disk_type`
- `environment`

## 1.0.0/terraform.tfvars.json.j2
- `project_id`
- `region`
- `vpc_name`
- `subnet_name`
- `cluster_name`
- `authorized_cidr`
- `node_pool_name`
- `environment` 