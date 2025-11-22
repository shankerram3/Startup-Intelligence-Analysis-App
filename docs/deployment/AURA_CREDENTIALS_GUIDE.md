# Neo4j Aura DB Credentials & Security Guide

This guide explains how to securely handle your Neo4j Aura DB credentials and configure environment variables.

---

## 🔑 Table of Contents

1. [Getting Your Aura DB Credentials](#getting-your-aura-db-credentials)
2. [Understanding the Credentials](#understanding-the-credentials)
3. [Storing Credentials Securely](#storing-credentials-securely)
4. [Environment Variable Configuration](#environment-variable-configuration)
5. [Security Best Practices](#security-best-practices)
6. [Rotating Credentials](#rotating-credentials)
7. [Troubleshooting](#troubleshooting)

---

## Getting Your Aura DB Credentials

### ⚠️ CRITICAL: Save Credentials Immediately!

When you create a Neo4j Aura DB instance, **you only see the password ONCE**. If you lose it, you'll need to reset it.

### Step-by-Step Process

#### 1. Create Aura DB Instance

Go to https://console.neo4j.io/ and create a database.

#### 2. Credentials Screen

After creation, you'll see a screen like this:

```
╔═══════════════════════════════════════════════════════╗
║          Database Created Successfully!               ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  Connection URI:                                      ║
║  neo4j+s://abc12345.databases.neo4j.io               ║
║                                                       ║
║  Username:                                            ║
║  neo4j                                                ║
║                                                       ║
║  Password:                                            ║
║  X8h9K2mP5nQ7rT3wY6zA                               ║
║                                                       ║
║  ⚠️  SAVE THIS PASSWORD - YOU WON'T SEE IT AGAIN!   ║
║                                                       ║
║  [Download credentials.txt]  [Continue]              ║
╚═══════════════════════════════════════════════════════╝
```

#### 3. Save Credentials (Do ALL of these!)

**Option A: Download credentials file**
- Click **"Download credentials.txt"** button
- Save to a secure location on your local machine
- **Do NOT upload this file to GitHub or any public location!**

**Option B: Copy to password manager**
- Copy URI, username, and password
- Save in your password manager (1Password, LastPass, etc.)

**Option C: Write them down**
- Write on paper and store securely
- Yes, physically write them down!

**Example credentials.txt:**
```
Neo4j Aura DB Credentials
========================

Database Name: graphrag-kb
Instance ID: abc12345

Connection URI: neo4j+s://abc12345.databases.neo4j.io
Username: neo4j
Password: X8h9K2mP5nQ7rT3wY6zA

Created: 2025-11-04 10:30:00 UTC
Region: AWS us-east-1
```

---

## Understanding the Credentials

### Connection URI Format

**Aura DB uses different URI format than self-hosted Neo4j!**

```bash
# ❌ WRONG - Self-hosted Neo4j format
NEO4J_URI=bolt://localhost:7687

# ✅ CORRECT - Aura DB format
NEO4J_URI=neo4j+s://abc12345.databases.neo4j.io
```

**Key differences:**
- Protocol: `neo4j+s://` (not `bolt://`)
- No port number (it's built-in)
- SSL/TLS is automatically enabled (`+s` means secure)
- Hostname is your unique Aura DB instance

### Username

**Default username:** `neo4j`

This is the same as self-hosted Neo4j, but you **cannot** change it in Aura DB free tier.

### Password

**Format:** Usually 20-24 characters, alphanumeric
**Example:** `X8h9K2mP5nQ7rT3wY6zA`

**Important:**
- Case-sensitive
- No spaces
- Generated randomly by Neo4j
- Cannot be customized during creation
- Can be reset later (but requires database restart)

---

## Storing Credentials Securely

### Option 1: .env File (Recommended for Development)

#### Create .env File on Your Server

```bash
# SSH into your server
ssh user@<your-server-ip>

# Navigate to project directory
cd ~/Startup-Intelligence-Analysis-App

# Create .env file
cat > .env << 'EOF'
# OpenAI API
OPENAI_API_KEY=sk-your-openai-api-key-here

# Neo4j Aura DB Connection
NEO4J_URI=neo4j+s://abc12345.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=X8h9K2mP5nQ7rT3wY6zA

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Embedding Backend
RAG_EMBEDDING_BACKEND=sentence-transformers
SENTENCE_TRANSFORMERS_MODEL=BAAI/bge-small-en-v1.5

# Verbose Logging
RAG_VERBOSE=1
EOF

# Secure the file (readable only by you)
chmod 600 .env

# Verify permissions
ls -la .env
# Should show: -rw------- (only owner can read/write)
```

#### Use vim/nano to Edit

```bash
# Using vim
vim .env

# Or using nano
nano .env

# Replace the placeholder values with your actual credentials
```

**Replace these values:**
```bash
# Change this:
NEO4J_URI=neo4j+s://abc12345.databases.neo4j.io
NEO4J_PASSWORD=X8h9K2mP5nQ7rT3wY6zA

# To your actual values:
NEO4J_URI=neo4j+s://your-actual-instance.databases.neo4j.io
NEO4J_PASSWORD=YourActualPassword123
```

#### Verify .env File

```bash
# Check contents (be careful - contains secrets!)
cat .env

# Or check without displaying secrets
grep "NEO4J_URI" .env
# Should show: NEO4J_URI=neo4j+s://...
```

<!-- Removed reference to azure_setup_aura.sh script -->

<!-- Removed Azure Key Vault instructions -->

---

## Environment Variable Configuration

### Complete .env File Template

```bash
# ============================================================================
# OpenAI API Configuration
# ============================================================================
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ============================================================================
# Neo4j Aura DB Configuration
# ============================================================================
# Connection URI format: neo4j+s://[instance-id].databases.neo4j.io
# Example: neo4j+s://abc12345.databases.neo4j.io
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io

# Username (always 'neo4j' for Aura DB)
NEO4J_USER=neo4j

# Password (generated when you created the Aura DB instance)
# Example: X8h9K2mP5nQ7rT3wY6zA
NEO4J_PASSWORD=YourAuraDBPasswordHere

# ============================================================================
# API Server Configuration
# ============================================================================
# Host (0.0.0.0 allows external connections)
API_HOST=0.0.0.0

# Port (default: 8000)
API_PORT=8000

# ============================================================================
# Embedding Configuration
# ============================================================================
# Backend: 'openai' or 'sentence-transformers'
# Use sentence-transformers to save API costs
RAG_EMBEDDING_BACKEND=sentence-transformers

# Sentence Transformers model (if using sentence-transformers backend)
# Recommended: BAAI/bge-small-en-v1.5 (best balance of speed/quality)
SENTENCE_TRANSFORMERS_MODEL=BAAI/bge-small-en-v1.5

# Alternative models:
# - BAAI/bge-base-en-v1.5 (better quality, slower)
# - all-MiniLM-L6-v2 (faster, lower quality)

# ============================================================================
# Logging Configuration
# ============================================================================
# Enable verbose logging (1=enabled, 0=disabled)
RAG_VERBOSE=1

# ============================================================================
# Optional: Azure-specific Settings
# ============================================================================
# Your Azure VM public IP (for reference)
AZURE_VM_PUBLIC_IP=20.1.2.3

# Environment name
ENVIRONMENT=production
```

### Validating Your Configuration

#### Test Connection

```bash
# Quick connection test
python -c "
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv('NEO4J_URI')
user = os.getenv('NEO4J_USER')
password = os.getenv('NEO4J_PASSWORD')

print(f'Testing connection...')
print(f'URI: {uri}')
print(f'User: {user}')
print(f'Password: {\"*\" * len(password)}')
print()

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    print('✅ Successfully connected to Aura DB!')

    # Get database info
    with driver.session() as session:
        result = session.run('CALL dbms.components() YIELD name, versions, edition')
        for record in result:
            print(f'   Database: {record[\"name\"]} {record[\"versions\"][0]}')
            print(f'   Edition: {record[\"edition\"]}')

    driver.close()
except Exception as e:
    print(f'❌ Connection failed!')
    print(f'Error: {e}')
    print()
    print('Common issues:')
    print('  1. Wrong URI format (should start with neo4j+s://)')
    print('  2. Incorrect password')
    print('  3. Database is paused (Free tier)')
    print('  4. Network connectivity issues')
"
```

#### Check Environment Variables

```bash
# Check if .env file is loaded
python -c "
import os
from dotenv import load_dotenv

load_dotenv()

print('Environment Variables:')
print(f'NEO4J_URI: {os.getenv(\"NEO4J_URI\", \"NOT SET\")}')
print(f'NEO4J_USER: {os.getenv(\"NEO4J_USER\", \"NOT SET\")}')
print(f'NEO4J_PASSWORD: {\"***\" + os.getenv(\"NEO4J_PASSWORD\", \"NOT SET\")[-4:]}')
print(f'OPENAI_API_KEY: {os.getenv(\"OPENAI_API_KEY\", \"NOT SET\")[:20]}...')
"
```

---

## Security Best Practices

### 1. File Permissions

```bash
# .env file should be readable only by owner
chmod 600 .env

# Verify
ls -la .env
# Output: -rw------- 1 azureuser azureuser 500 Nov 4 10:30 .env
```

### 2. Git Ignore

Ensure .env is in .gitignore:

```bash
# Check if .env is ignored
cat .gitignore | grep .env

# If not, add it
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore
echo "!.env.template" >> .gitignore

# Verify .env is not tracked
git status
# Should NOT show .env file
```

### 3. Never Commit Secrets

```bash
# Before committing, check for secrets
git diff

# If you accidentally committed secrets:
# 1. Rotate all credentials immediately
# 2. Remove from git history:
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all
```

### 4. Use Different Credentials for Different Environments

```bash
# Development
.env.development

# Staging
.env.staging

# Production
.env.production

# Load specific environment
# export ENV=production
# python -c "from dotenv import load_dotenv; load_dotenv('.env.production')"
```

### 5. Limit Database Access

In Aura DB Console:
1. Go to your database
2. Click **"Connection"** tab
3. Under **"Allowed IP Addresses"**, add your VM's public IP
4. This restricts access to only your VM

```bash
# Get your VM's public IP
curl ifconfig.me

# Add this IP to Aura DB allowed list
```

### 6. Use Read-Only Credentials (Future)

For production, create separate read-only users:

```cypher
// In Neo4j Browser (Aura Console)
CREATE USER reader SET PASSWORD 'ReadOnlyPassword123';
GRANT ROLE reader TO reader;
```

Then use different credentials for different purposes:
- Admin: Full access (for pipeline)
- Reader: Read-only (for API queries)

---

## Rotating Credentials

### When to Rotate

- Every 90 days (best practice)
- If credentials are compromised
- When team member leaves
- After any security incident

### How to Reset Aura DB Password

#### Option 1: Via Aura Console (Recommended)

1. Go to https://console.neo4j.io/
2. Select your database
3. Click **"Actions"** → **"Reset password"**
4. **Important**: Database will restart (1-2 minutes downtime)
5. New password will be displayed (save it!)
6. Update .env file on your VM

```bash
# SSH into VM
ssh azureuser@<your-vm-ip>

# Update .env file
vim ~/Startup-Intelligence-Analysis-App/.env

# Update NEO4J_PASSWORD line with new password

# Restart API
sudo systemctl restart graphrag-api

# Test connection
curl http://localhost:8000/health
```

#### Option 2: Via Neo4j Cypher (Self-Service)

Unfortunately, Aura DB free tier doesn't support user password changes via Cypher. You must use the Console.

### Rotation Checklist

- [ ] Generate new password in Aura Console
- [ ] Save new password securely
- [ ] Update .env file on all servers/VMs
- [ ] Restart API service
- [ ] Test connection
- [ ] Update password manager
- [ ] Revoke old password access (automatic in Aura)
- [ ] Document rotation in change log

---

## Troubleshooting

### Issue: "Authentication failed"

```
neo4j.exceptions.AuthError: The client is unauthorized due to authentication failure.
```

**Solutions:**

1. **Check password is correct**:
   ```bash
   # View (masked) password from .env
   grep NEO4J_PASSWORD .env
   ```

2. **Verify URI format**:
   ```bash
   # Should start with neo4j+s://
   grep NEO4J_URI .env
   ```

3. **Check for extra spaces or characters**:
   ```bash
   # Password should be clean (no quotes, spaces)
   # Wrong:
   NEO4J_PASSWORD="X8h9K2mP5nQ7rT3wY6zA"  # Has quotes!
   NEO4J_PASSWORD=X8h9K2mP5nQ7rT3wY6zA   # Extra space!

   # Correct:
   NEO4J_PASSWORD=X8h9K2mP5nQ7rT3wY6zA
   ```

4. **Reset password in Aura Console**

### Issue: "Connection refused" or "Unable to connect"

```
neo4j.exceptions.ServiceUnavailable: Unable to retrieve routing information
```

**Solutions:**

1. **Check database is running** (not paused):
   - Go to Aura Console
   - Check database status
   - If paused, click "Resume"

2. **Check URI is correct**:
   ```bash
   # Should look like: neo4j+s://abc12345.databases.neo4j.io
   # NOT: bolt://localhost:7687
   ```

3. **Check network connectivity**:
   ```bash
   # Test connectivity to Aura
   ping abc12345.databases.neo4j.io

   # Test port
   nc -zv abc12345.databases.neo4j.io 7687
   ```

4. **Check VM firewall allows outbound HTTPS**:
   ```bash
   sudo ufw status
   # Should allow outbound traffic
   ```

### Issue: ".env file not loaded"

```python
# NEO4J_URI is None or 'None'
```

**Solutions:**

1. **Check .env file exists**:
   ```bash
   ls -la ~/Startup-Intelligence-Analysis-App/.env
   ```

2. **Check working directory**:
   ```bash
   # Must run from project directory
   cd ~/Startup-Intelligence-Analysis-App
   python your_script.py
   ```

3. **Check python-dotenv is installed**:
   ```bash
   pip show python-dotenv
   ```

4. **Explicitly specify .env path**:
   ```python
   from dotenv import load_dotenv
   load_dotenv('/full/path/to/.env')
   ```

### Issue: "Password contains special characters"

If your Aura DB password has special characters (`!@#$%^&*`), you might need to escape them:

```bash
# If password is: P@ssw0rd!123
# In .env file, use as-is (no quotes needed):
NEO4J_PASSWORD=P@ssw0rd!123

# If still having issues, use quotes:
NEO4J_PASSWORD='P@ssw0rd!123'
```

---

## Quick Reference

### .env File Format

```bash
# Aura DB Configuration
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=YourPasswordHere

# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here
```

### Test Connection

```bash
python -c "from neo4j import GraphDatabase; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))); driver.verify_connectivity(); print('✅ Connected!'); driver.close()"
```

### Update Credentials

```bash
# Edit .env file
vim ~/Startup-Intelligence-Analysis-App/.env

# Restart API
sudo systemctl restart graphrag-api

# Verify
curl http://localhost:8000/health
```

---

## Summary

### ✅ Do's

- ✅ Save credentials immediately when creating Aura DB
- ✅ Download credentials.txt file
- ✅ Store in password manager
- ✅ Use .env file with chmod 600
- ✅ Add .env to .gitignore
- ✅ Test connection after setup
- ✅ Rotate credentials every 90 days
- ✅ Use Azure Key Vault for production

### ❌ Don'ts

- ❌ Never commit .env to git
- ❌ Never share passwords in plain text
- ❌ Never use same password across environments
- ❌ Don't use weak passwords (if you can set custom)
- ❌ Don't store passwords in code
- ❌ Don't email/Slack passwords

---

**Need Help?**

- Aura DB Console: https://console.neo4j.io/
- Neo4j Docs: https://neo4j.com/docs/aura/
- See also: [AURA_DB_SETUP.md](AURA_DB_SETUP.md)

---

**Your credentials are safe as long as you follow these practices! 🔐**
