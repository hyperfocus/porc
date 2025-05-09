# GitHub App Setup for PORC

This guide walks through setting up a GitHub App for PORC to enable Check Runs API access.

## Prerequisites

- Python 3.11 or later
- `pip` package manager
- `kubectl` configured with access to your cluster
- GitHub account with admin access to the repository

## Important Security Note

The following files contain sensitive information and should **never** be committed to version control:
- `k8s/secrets/` directory and all its contents
- `*.pem` files (private keys)
- `github-app-config.json`

These files are automatically added to `.gitignore` to prevent accidental commits.

## Step 1: Create GitHub App

1. Go to [GitHub App settings](https://github.com/settings/apps/new)
2. Fill in the following details:
   - GitHub App name: `porc-checks-bot` (or your preferred name)
   - Homepage URL: Your PORC API URL (e.g., `https://github.com/hyperfocus/porc`)
   - Webhook URL: Leave empty for now
   - Webhook secret: Leave empty for now

3. Set the following permissions:
   - Checks: Read & write
   - Contents: Read-only
   - Pull requests: Read-only

4. Subscribe to these events:
   - Check run
   - Check suite
   - Pull request

5. Where can this GitHub App be installed?
   - Select "Only on this account"

6. Click "Create GitHub App"

## Step 2: Generate Private Key

1. In your GitHub App settings, scroll to "Private keys"
2. Click "Generate a private key"
3. Save the downloaded `.pem` file securely

## Step 3: Install GitHub App

1. Go to your GitHub App's page (e.g., `https://github.com/apps/porc-checks-bot`)
2. Click "Install App"
3. Select your repository
4. Click "Install"

## Step 4: Generate Configuration

1. Install required Python packages:
   ```bash
   pip install PyJWT
   ```

2. Run the configuration script:
   ```bash
   python scripts/create_github_app.py \
     --name "porc-checks-bot" \
     --homepage "https://github.com/hyperfocus/porc" \
     --owner "hyperfocus" \
     --repo "porc"
   ```

3. When prompted:
   - Enter the path to your downloaded `.pem` file
   - Enter the App ID (found in your app's settings page)

4. The script will generate:
   - `github-app-config.json`: Contains app ID, private key, and installation ID

## Step 5: Create Kubernetes Secrets

1. Run the secrets generation script:
   ```bash
   python scripts/create_k8s_secrets.py --config github-app-config.json
   ```

2. This will create three secret files in `k8s/secrets/`:
   - `github-app-id.yaml`: App ID secret
   - `github-app-key.yaml`: Private key secret
   - `github-app-installation-id.yaml`: Installation ID secret

3. Apply the secrets to your cluster:
   ```bash
   kubectl apply -f k8s/secrets
   ```

## Step 6: Update PORC Configuration

1. Apply the GitHub App ConfigMap:
   ```bash
   kubectl apply -f k8s/config/github-app.yaml
   ```

2. Update the deployment:
   ```bash
   kubectl apply -f k8s/deployment.yaml
   ```

3. Restart the deployment to pick up new configuration:
   ```bash
   kubectl rollout restart deployment/porc-api
   ```

## Step 7: Verify Setup

1. Create a new PR in your repository
2. The PORC API should now:
   - Create check runs using the GitHub App
   - Update check run status
   - Post check run results

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Verify the private key is correctly saved in Kubernetes secrets
   - Check that the App ID and Installation ID are correct
   - Ensure the GitHub App has the correct permissions

2. **404 Not Found**
   - Verify the GitHub App is installed on the repository
   - Check that the Installation ID is correct

3. **403 Forbidden**
   - Verify the GitHub App has the required permissions
   - Check that the repository is in the allowed list

### Checking Logs

```bash
kubectl logs -f deployment/porc-api
```

## Security Notes

- Keep the private key secure and never commit it to version control
- Regularly rotate the private key through the GitHub App settings
- Use the minimum required permissions for the GitHub App
- Consider using a dedicated namespace for the PORC deployment

## Maintenance

### Updating App Permissions

1. Go to your GitHub App settings
2. Update permissions as needed
3. Click "Save changes"
4. Reinstall the app on your repository

### Rotating Private Key

1. Generate a new private key in GitHub App settings
2. Update the Kubernetes secret:
   ```bash
   kubectl create secret generic github-app-key \
     --from-file=private_key=path/to/new-key.pem \
     --dry-run=client -o yaml | kubectl apply -f -
   ```
3. Restart the deployment:
   ```bash
   kubectl rollout restart deployment/porc-api
   ``` 