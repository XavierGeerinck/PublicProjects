# Pulumi Deploy

## Getting Started

### Install Pulumi

Install Pulumi through the code below:

```bash
# Mac
brew install pulumi

# Windows
choco install pulumi

# Linux
curl -fsSL https://get.pulumi.com | sh
```

### Access Microsoft

```bash
az login
az account set --subscription YOUR_SUB_ID

# Get the locations we can deploy in
az account list-locations --output table
```

### Configure Pulumi

#### State File

Pulumi utilizes a state file. This file can be stored in the cloud or locally.

```bash
# Use Current Directory
pulumi login file://$(pwd)

# Use Home Directory
pulumi login --local

# Use Azure Blob
AZURE_STORAGE_ACCOUNT="NAME_OF_STORAGE_ACCOUNT"
AZURE_STORAGE_KEY="ACCESS_KEY_OF_STORAGE_ACCOUNT"
pulumi login azblob://AZURE_STORAGE_ACCOUNT_CONTAINER_PATH

# Logout
pulumi logout

# Migrating between backends
# https://www.pulumi.com/docs/intro/concepts/state/#migrating-between-backends
```

## Running Pulumi

```bash
# Set Pulumi Location
pulumi config set azure-native:location northeurope

# Set Pulumi Password
export PULUMI_CONFIG_PASSPHRASE="YOUR_PASSWORD"

# [Node,.js] Install Dependencies
npm i

# Run Pulumi
pulumi up --stack demo-container-apps-pulumi
```