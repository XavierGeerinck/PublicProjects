# README

## Prerequisites

```bash
# Install UV
# why UV? Because it's fast (see: https://codemaker2016.medium.com/introducing-uv-next-gen-python-package-manager-b78ad39c95d7)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Configure Python 3.12 with it
uv python install 3.12
```

## Troubleshooting

### Invalid peer certificate: UnknownIssuer

This is because the SSL Certificate File is not being found. Set it manually through the below:

```bash
# This file is created automatically through `sudo update-ca-certificates`
# if you are missing your CA, add it in `/usr/local/share/ca-certificates/`
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
```