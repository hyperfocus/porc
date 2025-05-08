#!/usr/bin/env python3
"""
Test script to verify GitHub App authentication.
This script will:
1. Generate a JWT token using the GitHub App private key
2. Get an installation access token
3. Make a test API call to verify authentication
"""
import os
import jwt
import time
import aiohttp
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GitHub App configuration from environment
APP_ID = os.getenv("GITHUB_APP_ID", "1252405")  # From values.yaml
INSTALLATION_ID = os.getenv("GITHUB_APP_INSTALLATION_ID", "66216708")  # From values.yaml
PRIVATE_KEY = os.getenv("GITHUB_APP_PRIVATE_KEY")

async def generate_jwt():
    """Generate a JWT token for GitHub App authentication."""
    if not PRIVATE_KEY:
        raise ValueError("GITHUB_APP_PRIVATE_KEY environment variable is not set")
    
    now = int(time.time())
    payload = {
        'iat': now,
        'exp': now + 300,  # 5 minutes
        'iss': APP_ID
    }
    
    try:
        jwt_token = jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')
        logger.info("Successfully generated JWT token")
        return jwt_token
    except Exception as e:
        logger.error(f"Failed to generate JWT token: {e}")
        raise

async def get_installation_token(jwt_token):
    """Get an installation access token using the JWT token."""
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    async with aiohttp.ClientSession() as session:
        url = f'https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens'
        async with session.post(url, headers=headers) as response:
            if response.status != 201:
                error_text = await response.text()
                logger.error(f"Failed to get installation token: {error_text}")
                raise Exception(f"Failed to get installation token: {error_text}")
            
            data = await response.json()
            logger.info("Successfully obtained installation token")
            return data['token']

async def test_api_call(token):
    """Make a test API call using the installation token."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    async with aiohttp.ClientSession() as session:
        # Test getting repository information
        url = 'https://api.github.com/repos/hyperfocus/porc'
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Failed to get repository info: {error_text}")
                raise Exception(f"Failed to get repository info: {error_text}")
            
            data = await response.json()
            logger.info(f"Successfully accessed repository: {data['name']}")
            return data

async def main():
    try:
        # Step 1: Generate JWT
        jwt_token = await generate_jwt()
        
        # Step 2: Get installation token
        installation_token = await get_installation_token(jwt_token)
        
        # Step 3: Test API call
        repo_info = await test_api_call(installation_token)
        
        logger.info("GitHub App authentication test completed successfully!")
        logger.info(f"Repository name: {repo_info['name']}")
        logger.info(f"Repository URL: {repo_info['html_url']}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 