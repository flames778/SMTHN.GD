# Token Encryption & KMS Custody

## Overview

Integration tokens (OAuth access and refresh tokens) are encrypted at rest in the database using Fernet symmetric encryption. This provides a security boundary preventing token leakage if the database is compromised.

## Encryption Strategy

### Algorithm
- **Cipher:** Fernet (AES-128-CBC with HMAC-SHA256)
- **Key Size:** 256-bit (SHA-256 hash of APP_ENCRYPTION_KEY)
- **Authentication:** HMAC-SHA256 (tamper detection)
- **Implementation:** Python `cryptography.fernet.Fernet`

### Key Derivation

The plaintext `APP_ENCRYPTION_KEY` (≥32 characters) is hashed with SHA-256 to produce a Fernet-compatible 256-bit key:

```python
key_hash = hashlib.sha256(encryption_key.encode("utf-8")).digest()
fernet_key = base64.urlsafe_b64encode(key_hash)
```

This ensures the key is cryptographically sound regardless of input entropy.

## Token Lifecycle

### 1. Token Issuance
When a user authorizes Google OAuth:
- Raw token arrives from Google OAuth server (in transit: TLS encrypted)
- Token is immediately encrypted before database insertion
- Plaintext token never stored; only ciphertext persists

### 2. Token Retrieval
When tokens are needed (e.g., syncing calendar):
- Ciphertext is fetched from database
- Decrypted in-memory using `APP_ENCRYPTION_KEY`
- Plaintext token used only for the Google API call
- Plaintext immediately discarded after use

### 3. Token Refresh
When Google refresh token is used:
- Ciphertext refresh token is fetched
- Decrypted in-memory
- Sent to Google OAuth server (TLS encrypted)
- New tokens returned, re-encrypted, and stored

### 4. Token Revocation
When user revokes integration:
- Row status set to "revoked"
- Tokens replaced with encrypted empty strings
- Tokens no longer usable even if database is compromised

## Production KMS Custody

### Local Development
- `APP_ENCRYPTION_KEY` stored in `.env` (unencrypted, development-only)
- Database runs in-memory or local PostgreSQL (no encryption at rest)
- Sufficient for development; not for production

### Production Recommendation: Azure Key Vault

For production deployments on Azure:

1. **Store Master Key in Azure Key Vault**
   - `APP_ENCRYPTION_KEY` (≥32 random characters) as a Key Vault secret
   - Automatic rotation policy (90 days recommended)
   - Access control via Azure AD identity (service principal)

2. **Token Encryption Remains Client-Side**
   - Application retrieves key from Key Vault at startup
   - Encrypts/decrypts tokens in application memory
   - Tokens never exposed to Azure infrastructure in plaintext

3. **Database Protection**
   - PostgreSQL Transparent Data Encryption (TDE) in Azure Database for PostgreSQL
   - Encrypted tokens provide additional security layer
   - Double encryption: TDE (storage) + Fernet (application)

4. **Deployment Flow**
   ```
   Startup:
     1. Get APP_ENCRYPTION_KEY from Azure Key Vault
     2. Validate key (≥32 chars)
     3. Initialize TokenEncryption service
     4. Start API server
   
   Token Storage:
     API receives OAuth token → TokenEncryption.encrypt() → PostgreSQL (encrypted at rest)
   
   Token Use:
     Fetch from PostgreSQL → TokenEncryption.decrypt() → Use → Discard plaintext
   ```

5. **Configuration (environment)**
   ```bash
   # In production deployment config:
   APP_ENCRYPTION_KEY=$(az keyvault secret show --vault-name my-vault --name app-encryption-key --query value -o tsv)
   export APP_ENCRYPTION_KEY
   ```

### Alternative: Google Cloud KMS / AWS KMS
If deployed on GCP or AWS, use equivalent key management services:
- **GCP Cloud KMS:** Store and rotate master key, retrieve during startup
- **AWS KMS:** Similarly retrieve at startup, application handles encryption

## Threat Model & Boundaries

### Protected Against
✓ **Database Breach:** Attacker gets encrypted tokens, needs `APP_ENCRYPTION_KEY` to decrypt  
✓ **Log Leakage:** Application logs never contain plaintext tokens  
✓ **Backup Exposure:** Database backups contain only ciphertext  
✓ **Casual Inspection:** Database admin cannot read tokens without key  

### Not Protected Against
✗ **Key Compromise:** If `APP_ENCRYPTION_KEY` is exposed, all tokens are exposed
✗ **In-Flight Plaintext:** Tokens sent to Google are in plaintext (mitigated by TLS)
✗ **Memory Dumps:** If application process is dumped, plaintext tokens in memory are readable
✗ **Filesystem Access:** If attacker has OS-level filesystem access (requires other security layers)

## Key Rotation

### Local Development (No Rotation Required)
- Same key throughout development
- Tests use hardcoded fixture keys

### Production Key Rotation Strategy

**Scenario:** APP_ENCRYPTION_KEY needs rotation (leaked, rotated policy, etc.)

**Approach:** Dual-key decryption (grace period for old-key tokens)

1. **Start Rotation Window**
   - Deploy new code with both old and new keys registered
   - All new tokens encrypted with new key
   - Decrypt logic tries new key first, falls back to old key

2. **Migration Job (optional)**
   - Background job re-encrypts all existing tokens with new key
   - Reduces old-key dependency
   - Can run during low-traffic window

3. **Retire Old Key**
   - After grace period (e.g., 24 hours), deprecate fallback to old key
   - New key becomes sole encryption/decryption key

Example (pseudocode):
```python
class TokenEncryption:
    def __init__(self, new_key, old_key=None):
        self._new = Fernet(make_key(new_key))
        self._old = Fernet(make_key(old_key)) if old_key else None
    
    def encrypt(self, plaintext):
        return self._new.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext):
        try:
            return self._new.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            if self._old:
                return self._old.decrypt(ciphertext.encode()).decode()
            raise
```

## Implementation Files

- **Encryption Service:** `app/security/token_encryption.py`
- **Integration Repository:** `app/repositories/integrations.py` (calls `get_decrypted_tokens()`)
- **Tests:** `lockdin_mvp/tests/test_token_encryption.py`, `test_encrypted_integrations.py`
- **Configuration:** `app/core/config.py` (validates APP_ENCRYPTION_KEY)

## Environment Variables

- **APP_ENCRYPTION_KEY** (Required)
  - Minimum 32 characters
  - Should be cryptographically random (≥128 bits entropy)
  - Stored in `.env` locally; in Azure Key Vault in production
  - Example: `openssl rand -base64 32` (produces 44-char base64-encoded 256-bit value)

## Testing Encryption

All token operations are transparent—tests don't need to know about encryption:

```python
# Repository layer handles encryption automatically
repo.upsert_google(..., access_token="plaintext_token", ...)
row = repo.get_by_provider(...)
# row.access_token contains ciphertext
decrypted = repo.get_decrypted_tokens(row)
assert decrypted["access_token"] == "plaintext_token"
```

## Compliance & Audit

### Data Minimization
- Tokens encrypted immediately upon storage
- Plaintext exists only transiently during issuance and use

### Auditability
- All encryption/decryption happens in `app/security/token_encryption.py`
- Single point for adding encryption logs if needed
- Access to encrypted tokens recorded in standard application logs (ciphertext only)

### Regulatory
- Fulfills "encryption at rest" requirement for GDPR/HIPAA compliance
- Supports audit trail via database audit logs (show encrypted columns changing)
