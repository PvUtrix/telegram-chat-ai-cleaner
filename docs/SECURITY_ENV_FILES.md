# Security Considerations for .env Files

## Clear-text Storage of API Keys

### The Issue
CodeQL (correctly) identifies that API keys are stored in plain text in `.env` files. This is a common pattern in development but requires careful handling.

### Why Plain Text is Necessary

1. **Library Compatibility**: The `python-dotenv` library requires plain text files
2. **Standard Pattern**: `.env` files are industry standard for local development
3. **Human Editable**: Developers need to easily view/edit configuration
4. **Environment Variables**: Operating systems expect plain text for env vars

### Security Mitigations Implemented

#### 1. File Permissions (chmod 600)
```python
os.chmod(env_path, stat.S_IRUSR | stat.S_IWUSR)
```
- Owner read/write only
- No access for group or others
- Automatically applied on file creation

#### 2. Git Protection
```gitignore
.env
.env.*
!.env.example
```
- `.env` files are ignored by git
- Prevents accidental commits
- Example file provided safely

#### 3. Runtime Warnings
```python
logger.warning(
    "Saving sensitive data (API keys) to file. "
    "Ensure file permissions are restricted..."
)
```
- Users informed when saving keys
- Security implications clearly stated

#### 4. Documentation
- `SECURITY_FEATURES.md`: Complete security guide
- `SECURITY.md`: Security policy
- Inline code comments: Security justifications
- README warnings: Data handling best practices

### Production Alternatives

**DO NOT use .env files in production.** Instead, use:

#### Cloud Secrets Management
- **AWS Secrets Manager**: `boto3.client('secretsmanager')`
- **Azure Key Vault**: `azure-keyvault-secrets`
- **Google Secret Manager**: `google-cloud-secret-manager`
- **HashiCorp Vault**: `hvac` Python client

#### Container/Orchestration
- **Kubernetes Secrets**: Mounted as volumes or env vars
- **Docker Secrets**: Swarm mode secret management
- **AWS ECS/Fargate**: Parameter Store or Secrets Manager
- **Azure Container Apps**: Key Vault references

#### Platform-as-a-Service
- **Heroku Config Vars**: Dashboard or CLI
- **Vercel Environment Variables**: Project settings
- **Netlify Environment Variables**: Build settings
- **Railway Variables**: Service settings

### Implementation Examples

#### AWS Secrets Manager
```python
import boto3

client = boto3.client('secretsmanager', region_name='us-east-1')
secret = client.get_secret_value(SecretId='telegram-analyzer/api-keys')
config = json.loads(secret['SecretString'])
```

#### Kubernetes Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: telegram-analyzer-secrets
type: Opaque
stringData:
  OPENAI_API_KEY: "sk-..."
  ANTHROPIC_API_KEY: "sk-ant-..."
```

#### HashiCorp Vault
```python
import hvac

client = hvac.Client(url='http://vault:8200')
client.token = os.environ['VAULT_TOKEN']
secret = client.secrets.kv.v2.read_secret_version(
    path='telegram-analyzer/api-keys'
)
```

### Development vs Production

| Aspect | Development | Production |
|--------|-------------|------------|
| Storage | `.env` file | Secrets Manager |
| Access | File system | API with auth |
| Rotation | Manual | Automated |
| Audit | None | Full logging |
| Encryption | Disk encryption | At rest + transit |
| Permissions | File (600) | IAM/RBAC |

### Risk Assessment

#### Development (.env file)
- **Risk Level**: Medium
- **Threat Model**: Local machine compromise
- **Mitigations**: File permissions, git ignore, warnings
- **Acceptable**: Yes, for local development only

#### Production (Secrets Manager)
- **Risk Level**: Low
- **Threat Model**: Network/cloud compromise
- **Mitigations**: Encryption, IAM, audit logs, rotation
- **Acceptable**: Yes, production ready

### Security Checklist

#### Local Development ✅
- [x] .env file has 600 permissions
- [x] .env is in .gitignore
- [x] Warnings shown when saving
- [x] Documentation provided
- [x] Example file available

#### Production Deployment 🔄
- [ ] Use secrets management service
- [ ] Enable secret rotation
- [ ] Implement audit logging
- [ ] Use IAM/RBAC for access control
- [ ] Monitor for unauthorized access
- [ ] Encrypt data at rest and in transit

### CodeQL Suppression Justification

The CodeQL warning for clear-text storage is suppressed because:

1. **Functional Requirement**: Plain text is required for dotenv compatibility
2. **Standard Practice**: Industry-standard pattern for development
3. **Adequate Mitigations**: Multiple security layers implemented
4. **Documented Alternatives**: Production solutions clearly documented
5. **User Awareness**: Runtime warnings and comprehensive docs
6. **Limited Scope**: Only for local development, not production

This is a conscious, informed decision with appropriate security controls.

### References

- [OWASP Secret Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [12-Factor App: Config](https://12factor.net/config)
- [NIST SP 800-57: Key Management](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)

---

**Last Updated**: 2025-01-05
**Status**: Accepted Risk for Development, Required Mitigation for Production
