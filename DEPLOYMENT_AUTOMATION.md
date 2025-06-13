# Vexa Cloud Deployment Automation

This document explains how to use the fully automated deployment system for the Vexa platform on Google Cloud Platform (GCP).

## 🚀 Quick Start

### Prerequisites
- Google Cloud SDK (`gcloud`) installed and authenticated
- Docker installed and running
- Access to GCP project `spry-pipe-425611-c4` (or modify `PROJECT` in Makefile)

### Deploy Everything
```bash
# Deploy the entire Vexa platform in one command
make all
```

This single command will:
1. ✅ Set up environment and validate tools
2. ✅ Enable required GCP APIs
3. ✅ Create Artifact Registry repository  
4. ✅ Build all 6 service Docker images
5. ✅ Push images to GCP registry
6. ✅ Create Cloud SQL PostgreSQL instance
7. ✅ Set up service accounts and permissions

## 📋 Available Commands

### Main Commands
```bash
make all          # Complete deployment (Phases 0-2)
make status       # Show current deployment status
make help         # Show all available commands
```

### Individual Phases
```bash
make phase0       # Environment and tooling setup
make phase1       # Build and push Docker images
make phase2       # Cloud SQL and service account setup
```

### Utilities
```bash
make test-images     # Test pulling images from registry
make clean-images    # Remove local Docker images
make clean-all       # ⚠️  DELETE all GCP resources (destructive!)
```

## 🔧 Configuration

The deployment is configured via variables at the top of the `Makefile`:

```makefile
PROJECT ?= spry-pipe-425611-c4           # GCP Project ID
REGION ?= europe-west1                   # GCP Region
ZONE ?= $(REGION)-b                      # GCP Zone
REG_REPO ?= vexa                         # Registry Repository Name
DB_INSTANCE ?= vexa-db                   # Cloud SQL Instance Name
SERVICE_ACCOUNT ?= sql-proxy-sa          # Service Account Name
```

To use a different project:
```bash
make all PROJECT=my-vexa-project
```

## 📊 Status Reporting

Check deployment status anytime:
```bash
make status
```

Sample output:
```
📊 Current Deployment Status:

GCP Project: spry-pipe-425611-c4
Region: europe-west1
Registry: europe-west1-docker.pkg.dev/spry-pipe-425611-c4/vexa

🏗️  Infrastructure Status:
  Artifact Registry: ✅ EXISTS
  Cloud SQL Instance: ✅ EXISTS
  Service Account: ✅ EXISTS

🐳 Docker Images in Registry:
  api-gateway: ✅ PUSHED
  admin-api: ✅ PUSHED
  bot-manager: ✅ PUSHED
  vexa-bot: ✅ PUSHED
  whisperlive:cpu: ✅ PUSHED
  collector: ✅ PUSHED
```

## 🔄 Idempotent Operations

The automation is designed to be **idempotent** - you can run `make all` multiple times safely:

- ✅ Existing GCP resources are detected and skipped
- ✅ Docker images are rebuilt and re-pushed (ensuring freshness)
- ✅ Service accounts and IAM policies are updated if needed
- ✅ No duplicate resources are created

## 🏗️ What Gets Deployed

### Docker Images (Phase 1)
| Service | Image Tag | Description |
|---------|-----------|-------------|
| API Gateway | `api-gateway:latest` | Main entry point and request router |
| Admin API | `admin-api:latest` | Administrative interface |
| Bot Manager | `bot-manager:latest` | Manages vexa-bot lifecycle |
| Vexa Bot | `vexa-bot:latest` | Meeting bot implementation |
| WhisperLive | `whisperlive:cpu-latest` | Speech-to-text service (CPU) |
| Collector | `collector:latest` | Transcription data collector |

### GCP Infrastructure (Phase 2)
| Resource | Configuration | Purpose |
|----------|--------------|---------|
| **Artifact Registry** | `vexa` repository in `europe-west1` | Private Docker image storage |
| **Cloud SQL** | PostgreSQL 15, 1 CPU, 4GB RAM | Managed database |
| **Service Account** | `sql-proxy-sa` with Cloud SQL Client role | Database access |

## 🚧 What's Next

After running `make all`, you're ready for **Phase 3: Docker Swarm Deployment**:

1. **Set up Docker Swarm cluster** on GCP Compute Engine
2. **Deploy services** using the pushed images
3. **Configure networking** with overlay networks
4. **Add GPU workers** for WhisperLive GPU inference
5. **Implement autoscaling** for dynamic resource management

See `planstate.md` for detailed Phase 3+ planning.

## 🔒 Security Notes

- **Service Account Keys**: Stored in `~/sql-proxy-key.json` - keep secure
- **Database Password**: Currently set to `VexaDB123!` - change for production
- **Registry Access**: Images are private and require GCP authentication
- **IAM Permissions**: Service accounts have minimal required permissions

## 🛠️ Troubleshooting

### "Permission denied" errors
```bash
# Ensure you're authenticated
gcloud auth login
gcloud config set project spry-pipe-425611-c4
```

### "Repository already exists" warnings
This is normal - the system detects existing resources and continues.

### Docker build failures
```bash
# Clean up and retry
make clean-images
make phase1
```

### Network connectivity issues
```bash
# Test registry access
make test-images
```

## 🎯 Benefits

✅ **One-Command Deployment**: From zero to deployed in minutes  
✅ **Reproducible**: Same result every time, anywhere  
✅ **Idempotent**: Safe to re-run, handles existing resources  
✅ **Modular**: Can run individual phases as needed  
✅ **Self-Documenting**: Clear status and progress indicators  
✅ **Production-Ready**: Uses managed GCP services  

---

For detailed phase planning and current status, see [`planstate.md`](./planstate.md). 