#!/usr/bin/env python3
"""
Script to create Kubernetes secrets for the GitHub App.
This script will:
1. Read the GitHub App config
2. Create Kubernetes secrets for the app ID and private key
"""

import argparse
import base64
import json
import subprocess
from pathlib import Path


def create_k8s_secrets(config_path: str, namespace: str = "default"):
    """Create Kubernetes secrets from the GitHub App config."""
    # Read config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Create secret for app ID
    app_id_secret = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {
            "name": "github-app-id",
            "namespace": namespace
        },
        "type": "Opaque",
        "data": {
            "app_id": base64.b64encode(str(config['app_id']).encode()).decode()
        }
    }
    
    # Create secret for private key
    private_key_secret = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {
            "name": "github-app-key",
            "namespace": namespace
        },
        "type": "Opaque",
        "data": {
            "private_key": config['private_key']
        }
    }
    
    # Create secret for installation ID
    installation_id_secret = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {
            "name": "github-app-installation-id",
            "namespace": namespace
        },
        "type": "Opaque",
        "data": {
            "installation_id": base64.b64encode(str(config['installation_id']).encode()).decode()
        }
    }
    
    # Save secrets to files
    secrets_dir = Path("k8s/secrets")
    secrets_dir.mkdir(parents=True, exist_ok=True)
    
    with open(secrets_dir / "github-app-id.yaml", "w") as f:
        json.dump(app_id_secret, f, indent=2)
    
    with open(secrets_dir / "github-app-key.yaml", "w") as f:
        json.dump(private_key_secret, f, indent=2)
    
    with open(secrets_dir / "github-app-installation-id.yaml", "w") as f:
        json.dump(installation_id_secret, f, indent=2)
    
    print(f"Created secret files in {secrets_dir}")
    print("\nTo apply these secrets to your cluster, run:")
    print(f"kubectl apply -f {secrets_dir}")


def main():
    parser = argparse.ArgumentParser(description='Create Kubernetes secrets for GitHub App')
    parser.add_argument('--config', required=True, help='Path to github-app-config.json')
    parser.add_argument('--namespace', default='default', help='Kubernetes namespace')
    
    args = parser.parse_args()
    create_k8s_secrets(args.config, args.namespace)


if __name__ == '__main__':
    main() 