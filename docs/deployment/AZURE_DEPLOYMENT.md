# Azure Deployment Guide

Complete guide for deploying the Startup Intelligence Analysis App to Azure.

---

## Quick Start

```bash
# Option 1: Automated deployment script
bash azure_setup.sh

# Option 2: With Neo4j Aura
bash azure_setup_aura.sh
```

---

## Prerequisites

- Azure account with active subscription
- Azure CLI installed and configured
- OpenAI API key
- Neo4j Aura account (for managed Neo4j) OR Docker for self-hosted

---

## Deployment Options

### Option 1: Azure VM + Docker Neo4j (Self-Hosted)

See `AZURE_README.md` for detailed instructions on:
- Setting up Azure VM
- Installing Docker and Neo4j
- Configuring networking and security
- Running the application

### Option 2: Azure VM + Neo4j Aura (Managed)

See `AURA_SETUP.md` for:
- Creating Neo4j Aura instance
- Getting connection credentials
- Configuring the application
- Best practices for production

### Option 3: Azure Container Instances

Deploy as containers for better scalability.

---

## Deployment Steps

### 1. Create Azure Resources

```bash
# Create resource group
az group create --name startup-intel-rg --location eastus

# Create VM
az vm create \
  --resource-group startup-intel-rg \
  --name startup-intel-vm \
  --image Ubuntu2204 \
  --size Standard_B2s \
  --admin-username azureuser \
  --generate-ssh-keys

# Open ports
az vm open-port --port 7474 --resource-group startup-intel-rg --name startup-intel-vm
az vm open-port --port 7687 --resource-group startup-intel-rg --name startup-intel-vm
az vm open-port --port 8000 --resource-group startup-intel-rg --name startup-intel-vm
```

### 2. Connect and Setup

```bash
# SSH to VM
ssh azureuser@<VM_PUBLIC_IP>

# Clone repository
git clone <your-repo-url>
cd Startup-Intelligence-Analysis-App

# Run setup script
bash azure_setup.sh
```

### 3. Configure Application

```bash
# Create .env file
cat > .env << 'EOF'
OPENAI_API_KEY=sk-your-key
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-secure-password
API_HOST=0.0.0.0
API_PORT=8000
EOF
```

### 4. Start Services

```bash
# Start Neo4j (Docker)
docker-compose up -d

# Or use Neo4j Aura (no Docker needed)
# Update NEO4J_URI in .env to Aura connection string

# Start API
python api.py
```

---

## Security Considerations

### Network Security

```bash
# Restrict Neo4j ports to local access only
az vm open-port --port 7474 --priority 1000 --resource-group startup-intel-rg --name startup-intel-vm --source-address-prefixes <YOUR_IP>/32

# Only expose API port publicly
az vm open-port --port 8000 --priority 1001 --resource-group startup-intel-rg --name startup-intel-vm
```

### SSL/TLS Setup

See [SSL Setup Guide](SSL_SETUP.md) for configuring HTTPS.

### Firewall Rules

```bash
# Configure Azure NSG
az network nsg rule create \
  --resource-group startup-intel-rg \
  --nsg-name startup-intel-nsg \
  --name AllowHTTPS \
  --priority 1000 \
  --destination-port-ranges 443 \
  --protocol Tcp \
  --access Allow
```

---

## Monitoring & Maintenance

### Azure Monitor

```bash
# Enable VM insights
az vm monitor metrics list \
  --resource-group startup-intel-rg \
  --name startup-intel-vm \
  --metric-names "Percentage CPU"
```

### Logging

```bash
# Application logs
tail -f /var/log/startup-intel/app.log

# Neo4j logs (if self-hosted)
docker logs neo4j -f
```

### Backups

```bash
# Neo4j backups (self-hosted)
docker exec neo4j neo4j-admin dump --to=/backups/neo4j-backup-$(date +%Y%m%d).dump

# For Neo4j Aura, backups are automatic
```

---

## Scaling

### Vertical Scaling

```bash
# Resize VM
az vm resize \
  --resource-group startup-intel-rg \
  --name startup-intel-vm \
  --size Standard_D4s_v3
```

### Horizontal Scaling

- Use Azure Load Balancer for multiple API instances
- Use Neo4j cluster for high availability
- Consider Azure Kubernetes Service (AKS) for container orchestration

---

## Cost Optimization

- Use Azure Reserved Instances for 40-60% savings
- Shut down development VMs when not in use
- Use Neo4j Aura Free tier for testing
- Monitor usage with Azure Cost Management

---

## Troubleshooting

### Common Issues

**Issue: Cannot connect to Neo4j**
```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Check firewall
sudo ufw status

# Test connection
curl http://localhost:7474
```

**Issue: API not accessible**
```bash
# Check if API is running
ps aux | grep "python api.py"

# Check port binding
netstat -tulpn | grep 8000

# Check Azure NSG rules
az network nsg rule list --resource-group startup-intel-rg --nsg-name startup-intel-nsg
```

---

## Additional Resources

- [Azure VM Documentation](https://docs.microsoft.com/azure/virtual-machines/)
- [Neo4j Aura Setup](AURA_SETUP.md)
- [SSL Setup Guide](SSL_SETUP.md)
- [Azure Quickstart](../QUICKSTART_AZURE.md)

---

For detailed Azure-specific instructions, see the original files:
- `AZURE_README.md` - Comprehensive Azure setup
- `AZURE_DEPLOYMENT_GUIDE.md` - Step-by-step deployment
- `QUICKSTART_AZURE.md` - Quick Azure deployment

