#!/usr/bin/env python3
"""
Script to help set up a GitHub App for PORC.
This script will:
1. Guide you through creating the GitHub App manually
2. Help install it on the specified repository
3. Output the necessary credentials
"""

import argparse
import base64
import json
import os
import sys
import time
import jwt
from pathlib import Path
from typing import Dict, Optional

import requests


def get_installation_id(app_id: int, private_key_path: str, owner: str, repo: str) -> int:
    """Get the installation ID for the GitHub App using JWT authentication."""
    # Read private key
    with open(private_key_path, 'r') as f:
        private_key = f.read()
    
    # Generate JWT
    now = int(time.time())
    payload = {
        'iat': now,
        'exp': now + 300,  # 5 minutes (GitHub's max is 10 minutes)
        'iss': app_id
    }
    
    jwt_token = jwt.encode(payload, private_key, algorithm='RS256')
    
    # Get installation ID
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.get(
        f'https://api.github.com/repos/{owner}/{repo}/installation',
        headers=headers
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get installation ID: {response.text}")
    
    return response.json()['id']


def main():
    parser = argparse.ArgumentParser(description='Set up a GitHub App for PORC')
    parser.add_argument('--name', default='porc-checks-bot', help='Name of the GitHub App')
    parser.add_argument('--description', default='PORC GitHub App for managing check runs', help='Description of the GitHub App')
    parser.add_argument('--homepage', required=True, help='Homepage URL for the GitHub App')
    parser.add_argument('--webhook-url', help='Webhook URL for the GitHub App')
    parser.add_argument('--webhook-secret', help='Webhook secret for the GitHub App')
    parser.add_argument('--owner', required=True, help='GitHub organization or user name')
    parser.add_argument('--repo', required=True, help='Repository name')
    parser.add_argument('--output-dir', default='.', help='Directory to save the credentials')
    
    args = parser.parse_args()
    
    print("\n=== GitHub App Setup Instructions ===")
    print("1. Go to https://github.com/settings/apps/new")
    print("2. Fill in the following details:")
    print(f"   - GitHub App name: {args.name}")
    print(f"   - Homepage URL: {args.homepage}")
    print(f"   - Webhook URL: {args.webhook_url or '(leave empty)'}")
    print(f"   - Webhook secret: {args.webhook_secret or '(leave empty)'}")
    print("\n3. Set the following permissions:")
    print("   - Checks: Read & write")
    print("   - Contents: Read-only")
    print("   - Pull requests: Read-only")
    print("\n4. Subscribe to these events:")
    print("   - Check run")
    print("   - Check suite")
    print("   - Pull request")
    print("\n5. Where can this GitHub App be installed?")
    print("   - Select 'Only on this account'")
    print("\n6. For the private key:")
    print("   a. Go to your GitHub App settings (https://github.com/settings/apps/porc-checks-bot)")
    print("   b. Scroll down to the 'Private keys' section")
    print("   c. Click 'Generate a private key' button")
    print("   d. Save the downloaded .pem file")
    
    private_key_path = input("\nEnter the path to the downloaded .pem file: ")
    
    # Get app ID
    app_id = input("\nEnter the App ID (found in the app's settings page): ")
    
    # Get installation ID
    print("\nGetting installation ID...")
    try:
        installation_id = get_installation_id(int(app_id), private_key_path, args.owner, args.repo)
    except Exception as e:
        print(f"\nError getting installation ID: {e}")
        print("\nPlease install the app on your repository first:")
        print(f"1. Go to https://github.com/apps/{args.name}")
        print("2. Click 'Install'")
        print("3. Select your repository")
        print("4. Click 'Install'")
        input("\nPress Enter after installing the app...")
        installation_id = get_installation_id(int(app_id), private_key_path, args.owner, args.repo)
    
    # Read private key for config
    with open(private_key_path, 'r') as f:
        private_key = f.read()
    private_key_b64 = base64.b64encode(private_key.encode('utf-8')).decode('utf-8')
    
    # Save app configuration
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    config = {
        'app_id': int(app_id),
        'private_key': private_key_b64,
        'webhook_secret': args.webhook_secret,
        'installation_id': installation_id
    }
    
    config_path = output_dir / 'github-app-config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\nGitHub App setup completed successfully!")
    print(f"Configuration saved to: {config_path}")
    print("\nNext steps:")
    print("1. Add the private key and app ID to your Kubernetes secrets")
    print("2. Update your PORC API configuration to use the GitHub App")
    print("3. Test the integration by creating a new PR")


if __name__ == '__main__':
    main() 