#!/bin/bash
# Note: On mac, install sshpass with `curl -L https://raw.githubusercontent.com/kadwanev/bigboybrew/master/Library/Formula/sshpass.rb > sshpass.rb && brew install sshpass.rb`
SUBSCRIPTION_ID=YOUR_SUBSCRIPTION_ID
LOCATION=westeurope

ADMIN_USERNAME=demo
ADMIN_PASSWORD=YOUR_PASSWORD

SA_NAME=YOUR_EXISTING_SA_NAME
SA_CONTAINER_NAME=YOUR_EXISTING_SA_CONTAINER_NAME

# Variabels - Computed
SUFFIX=$(openssl rand -base64 5 | tr -d '/+' | tr '[:upper:]' '[:lower:]' | tr -cd '[:alnum:]' | head -c 5)
RG_NAME="demo-$SUFFIX"
VM_NAME="demo-$SUFFIX"
VM_SA_NAME="sademo$SUFFIX"
VM_DISK_NAME="disk-$SUFFIX"

# Check prerequisites
if [[ $(uname -s) == "Darwin" && $(which sshpass) ]]; then
  echo "Install all prerequisites first"
  echo "curl -L https://raw.githubusercontent.com/kadwanev/bigboybrew/master/Library/Formula/sshpass.rb > sshpass.rb && brew install sshpass.rb"
  exit
fi

# =============================================
# Create Resource group
# =============================================
az group create --name $RG_NAME --location $LOCATION

# =============================================
# Create a VM with azcopy installed
# =============================================
az vm create \
  --resource-group $RG_NAME \
  --name $VM_NAME \
  --image "UbuntuLTS" \
  --os-disk-size-gb 1024 \
  --admin-username $ADMIN_USERNAME \
  --admin-password $ADMIN_PASSWORD \
  --generate-ssh-keys \
  --output table

VM_IP=$(
  az vm show \
  --resource-group $RG_NAME \
  --name $VM_NAME \
  --show-details \
  --query publicIps \
  --output tsv
)

# Install azcopy on it
sshpass -p $ADMIN_PASSWORD ssh -t $ADMIN_USERNAME@$VM_IP \
  "apt install -y wget && wget -O azcopy_v10.tar.gz https://aka.ms/downloadazcopy-v10-linux && tar -xf azcopy_v10.tar.gz --strip-components=1"

# =============================================
# Download the model
# =============================================
sshpass -p $ADMIN_PASSWORD ssh -t $ADMIN_USERNAME@$VM_IP \
  "wget -O llama_download.sh https://raw.githubusercontent.com/shawwn/llama-dl/main/llama.sh; sudo chmod +x llama_download.sh; ./llama_download.sh"

# =============================================
# Upload the model to Azure Storage
# =============================================
# Create a SAS URL for the container so we can upload/download files
# expiry time = 4 hours from now
AZ_SAS_TOKEN_EXPIRY=$(date -v+4H -u +%Y-%m-%dT%H:%MZ)
AZ_SAS_TOKEN=$(az storage container generate-sas --account-name $SA_NAME --name $SA_CONTAINER_NAME --permissions rw --expiry $AZ_SAS_TOKEN_EXPIRY --output tsv)

# Upload the files in the directories 7B, 13B to azure storage under the folder LLaMA 
sshpass -p $ADMIN_PASSWORD ssh -t $ADMIN_USERNAME@$VM_IP \
  "sudo ./azcopy copy '/home/$ADMIN_USERNAME/llama_download.sh' 'https://$SA_NAME.blob.core.windows.net/$SA_CONTAINER_NAME/LLaMA/download.sh?${AZ_SAS_TOKEN}'"
sshpass -p $ADMIN_PASSWORD ssh -t $ADMIN_USERNAME@$VM_IP \
  "sudo ./azcopy copy '/home/$ADMIN_USERNAME/tokenizer.model' 'https://$SA_NAME.blob.core.windows.net/$SA_CONTAINER_NAME/LLaMA/download.sh?${AZ_SAS_TOKEN}'"
sshpass -p $ADMIN_PASSWORD ssh -t $ADMIN_USERNAME@$VM_IP \
  "sudo ./azcopy copy '/home/$ADMIN_USERNAME/tokenizer_checklist.chk' 'https://$SA_NAME.blob.core.windows.net/$SA_CONTAINER_NAME/LLaMA/download.sh?${AZ_SAS_TOKEN}'"
sshpass -p $ADMIN_PASSWORD ssh -t $ADMIN_USERNAME@$VM_IP \
  "sudo ./azcopy copy '/home/$ADMIN_USERNAME/7B' 'https://$SA_NAME.blob.core.windows.net/$SA_CONTAINER_NAME/LLaMA/7B?${AZ_SAS_TOKEN}' --recursive=true"
sshpass -p $ADMIN_PASSWORD ssh -t $ADMIN_USERNAME@$VM_IP \
  "sudo ./azcopy copy '/home/$ADMIN_USERNAME/13B' 'https://$SA_NAME.blob.core.windows.net/$SA_CONTAINER_NAME/LLaMA/13B?${AZ_SAS_TOKEN}' --recursive=true"
sshpass -p $ADMIN_PASSWORD ssh -t $ADMIN_USERNAME@$VM_IP \
  "sudo ./azcopy copy '/home/$ADMIN_USERNAME/30B' 'https://$SA_NAME.blob.core.windows.net/$SA_CONTAINER_NAME/LLaMA/30B?${AZ_SAS_TOKEN}' --recursive=true"
sshpass -p $ADMIN_PASSWORD ssh -t $ADMIN_USERNAME@$VM_IP \
  "sudo ./azcopy copy '/home/$ADMIN_USERNAME/65B' 'https://$SA_NAME.blob.core.windows.net/$SA_CONTAINER_NAME/LLaMA/65B?${AZ_SAS_TOKEN}' --recursive=true"

# =============================================
# Clean up
# =============================================
az group delete --name $RG_NAME --yes --no-wait