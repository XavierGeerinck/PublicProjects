#!/bin/bash
cd functions-node

AZURE_FUNCTIONAPP_NAME=app-functions-2c008876

# Deploy by building locally instead of using the remote builder this prevents issues with the remote builder
func azure functionapp publish $AZURE_FUNCTIONAPP_NAME