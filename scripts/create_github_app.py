#!/usr/bin/env python3
"""
Script to create and configure a GitHub App for PORC.
This script will:
1. Create a new GitHub App
2. Generate a private key
3. Install it on the specified repository
4. Output the necessary credentials
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


def generate_private_key() -> tuple[str, str]:
    """Generate a new RSA private key and return both PEM and base64 encoded versions."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Get PEM format
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    # Get base64 encoded version
    b64 = base64.b64encode(pem.encode('utf-8')).decode('utf-8')
    
    return pem, b64


def create_github_app(
    name: str,
    description: str,
    homepage_url: str,
    webhook_url: Optional[str],
    webhook_secret: Optional[str],
    private_key: str,
    github_token: str
) -> Dict:
    """Create a new GitHub App using the GitHub API."""
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    data = {
        'name': name,
        'description': description,
        'url': homepage_url,
        'default_permissions': {
            'checks': 'write',
            'contents': 'read',
            'pull_requests': 'read'
        },
        'default_events': [
            'check_run',
            'check_suite',
            'pull_request'
        ],
        'public': False
    }
    
    if webhook_url:
        data['webhook_url'] = webhook_url
    if webhook_secret:
        data['webhook_secret'] = webhook_secret
    
    # First create the app manifest
    response = requests.post(
        'https://api.github.com/user/apps',
        headers=headers,
        json=data
    )
    
    if response.status_code != 201:
        raise Exception(f"Failed to create GitHub App: {response.text}")
    
    app_data = response.json()
    
    # Then create the app installation
    install_response = requests.post(
        f'https://api.github.com/app/installations',
        headers=headers,
        json={
            'repository_selection': 'selected',
            'repositories': [f'{owner}/{repo}']
        }
    )
    
    if install_response.status_code != 201:
        raise Exception(f"Failed to create app installation: {install_response.text}")
    
    app_data['installation_id'] = install_response.json()['id']
    
    return app_data


def install_app_on_repo(
    app_id: int,
    owner: str,
    repo: str,
    github_token: str
) -> None:
    """Install the GitHub App on the specified repository."""
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.post(
        f'https://api.github.com/app/installations/{app_id}/repositories/{owner}/{repo}',
        headers=headers
    )
    
    if response.status_code != 201:
        raise Exception(f"Failed to install app on repository: {response.text}")


def main():
    parser = argparse.ArgumentParser(description='Create and configure a GitHub App for PORC')
    parser.add_argument('--name', default='porc-checks-bot', help='Name of the GitHub App')
    parser.add_argument('--description', default='PORC GitHub App for managing check runs', help='Description of the GitHub App')
    parser.add_argument('--homepage', required=True, help='Homepage URL for the GitHub App')
    parser.add_argument('--webhook-url', help='Webhook URL for the GitHub App')
    parser.add_argument('--webhook-secret', help='Webhook secret for the GitHub App')
    parser.add_argument('--owner', required=True, help='GitHub organization or user name')
    parser.add_argument('--repo', required=True, help='Repository name')
    parser.add_argument('--github-token', required=True, help='GitHub personal access token with admin:org scope')
    parser.add_argument('--output-dir', default='.', help='Directory to save the credentials')
    
    args = parser.parse_args()
    
    # Generate private key
    print("Generating private key...")
    private_key_pem, private_key_b64 = generate_private_key()
    
    # Create GitHub App
    print("Creating GitHub App...")
    app_data = create_github_app(
        name=args.name,
        description=args.description,
        homepage_url=args.homepage,
        webhook_url=args.webhook_url,
        webhook_secret=args.webhook_secret,
        private_key=private_key_pem,
        github_token=args.github_token
    )
    
    # Install app on repository
    print(f"Installing app on {args.owner}/{args.repo}...")
    install_app_on_repo(
        app_id=app_data['id'],
        owner=args.owner,
        repo=args.repo,
        github_token=args.github_token
    )
    
    # Save credentials
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save private key
    with open(output_dir / 'private-key.pem', 'w') as f:
        f.write(private_key_pem)
    
    # Save app configuration
    config = {
        'app_id': app_data['id'],
        'client_id': app_data['client_id'],
        'client_secret': app_data['client_secret'],
        'private_key': private_key_b64,
        'webhook_secret': args.webhook_secret,
        'installation_id': app_data['installation_id']
    }
    
    with open(output_dir / 'github-app-config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\nGitHub App created and installed successfully!")
    print(f"App ID: {app_data['id']}")
    print(f"Client ID: {app_data['client_id']}")
    print(f"Private key saved to: {output_dir / 'private-key.pem'}")
    print(f"Configuration saved to: {output_dir / 'github-app-config.json'}")
    print("\nNext steps:")
    print("1. Add the private key and app ID to your Kubernetes secrets")
    print("2. Update your PORC API configuration to use the GitHub App")
    print("3. Test the integration by creating a new PR")


if __name__ == '__main__':
    main() 