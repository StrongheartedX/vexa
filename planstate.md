# Vexa Cloud Deployment Plan - `planstate.md`

This document outlines the phased plan to migrate the Vexa platform to a fully automated, cloud-hosted environment on Google Cloud Platform (GCP) using Docker Swarm.

## **Current Status: `Phase 3 Automated`**

---

## **Phase 0: Tooling & Repository Bootstrap**

*   **Objective**: Establish the basic build and environment management tools.
*   **Status**: `Completed`

| Task                     | Description                                                                                              | Status      |
| ------------------------ | -------------------------------------------------------------------------------------------------------- | ----------- |
| **1. Create `Makefile`** | A `Makefile` to automate building and pushing Docker images to GCP Artifact Registry.                   | `Completed` |
| **2. Setup Environment** | Define `PROJECT`, `REGION`, and `REG` environment variables for GCP configuration.                       | `Completed` |
| **3. Local Build Test**  | Run `make build-all` to ensure all service images (`api-gateway`, `bot-manager`, `vexa-bot`, `whisperlive:cpu`, `transcription-collector`) build successfully. | `Completed` |

---

## **Phase 1: Build & GCP Artifact Registry Setup**

*   **Objective**: Build all service container images and store them in a centralized, private registry on GCP.
*   **Status**: `Completed`

| Task                                 | Description                                                                                                   | Status      |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------- | ----------- |
| **1. Enable GCP APIs**               | Enable `artifactregistry.googleapis.com`, `compute.googleapis.com`, and `sqladmin.googleapis.com`.              | `Completed` |
| **2. Create Artifact Registry**      | Create a Docker repository named `vexa` in the specified GCP region.                                          | `Completed` |
| **3. Build & Push Images**           | Use the `Makefile` to build all Vexa service images and push them to the new Artifact Registry.               | `Completed` |
| **4. Validate Image Availability**   | Pull an image (e.g., `whisperlive:cpu-latest`) from the registry to confirm it's accessible.                  | `Completed` |

---

## **Phase 2: Cloud SQL Provisioning & Connectivity**

*   **Objective**: Provision a managed PostgreSQL database on Cloud SQL and establish secure connectivity from the Swarm cluster.
*   **Status**: `Completed`

| Task                                   | Description                                                                                                                              | Status      |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| **1. Create Cloud SQL Instance**       | Provision a Postgres 15 instance (`vexa-db`) with private IP and create the `vexa` database.                                               | `Completed` |
| **2. Create Service Account**          | Create a service account (`sql-proxy-sa`) with the "Cloud SQL Client" role for proxy access.                                                | `Completed` |
| **3. Configure Swarm Secret for DB**   | Store the database password securely in Docker Swarm as a secret (`db-pass`).                                                              | `Ready for Phase 3` |
| **4. Test Connectivity**               | Run the `cloud-sql-proxy` locally to verify a successful connection to the Cloud SQL instance using the service account credentials.         | `Completed` |

---

## **Phase 3: CPU-Only Swarm Deployment**

*   **Objective**: Deploy the core Vexa services onto a CPU-based Managed Instance Group (MIG) in a Docker Swarm cluster.
*   **Status**: `Automated`

| Task                                    | Description                                                                                                                                                             | Status      |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| **1. Create Firewall Rules**            | Create GCP firewall rules for Swarm internode communication (port 2377, 7946, 4789) and SSH access.                                                                      | `Automated` |
| **2. Provision Swarm Manager & Workers**| Automatically provision one manager and two worker VMs on GCP Compute Engine using `gce-startup-script.sh` to install Docker.                                           | `Automated` |
| **3. Initialize Swarm & Join Workers**  | The manager node initializes a new Swarm cluster, and the worker nodes securely join it.                                                                                | `Automated` |
| **4. Grant IAM Permissions**            | The Compute Engine default service account is granted `artifactregistry.reader` and `cloudsql.client` roles to allow nodes to pull images and connect to the database.   | `Automated` |
| **5. Deploy `vexa-cpu.yml` stack**      | Deploy the CPU-only stack, including `cloudsql-proxy`, `api-gateway`, `bot-manager`, `whisperlive:cpu`, `transcription-collector`, etc.                                    | `Automated` |
| **6. Verify Deployment**                | Run `make status` to check the health of Swarm nodes and deployed services.                                                                                             | `Ready to Run` |

---

## **Phase 4 & 5: GPU Bursting & Hybrid Autoscaling**

*   **Objective**: Add GPU capabilities to the cluster for high-performance inference, enabling bursting from on-prem to the cloud.
*   **Status**: `Not Started`

| Task                               | Description                                                                                                                                                                                                   | Status      |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| **1. Add GPU Workers (GCP MIG)**   | Create a new MIG with GPU-enabled VMs, labeled `gpu=true`.                                                                                                                                                    | `Not Started` |
| **2. Deploy GPU WhisperLive**      | Deploy a new `whisperlive` service using the GPU image, constrained to nodes with `gpu=true`.                                                                                                                  | `Not Started` |
| **3. Integrate On-Prem GPU**       | Join the on-prem Tesla server to the Swarm cluster and label it with `gpu=true`. Swarm will automatically schedule tasks on it.                                                                                   | `Not Started` |
| **4. Implement Swarm Autoscaler**  | Deploy a small autoscaler script that monitors task scheduling and scales the GPU MIG up or down based on demand.                                                                                               | `Not Started` |
| **5. Test Hybrid Bursting**        | Run load tests to verify that WhisperLive tasks first fill up the on-prem GPU and then automatically spill over to the GCP GPUs.                                                                                | `Not Started` |

---

## **Completed Infrastructure**

### **Phase 1 Results:**
- **GCP Project**: `spry-pipe-425611-c4`
- **Artifact Registry**: `europe-west1-docker.pkg.dev/spry-pipe-425611-c4/vexa`
- **Built Images**: 
  - `api-gateway:latest`
  - `admin-api:latest` 
  - `bot-manager:latest`
  - `vexa-bot:latest`
  - `whisperlive:cpu-latest`
  - `collector:latest`

### **Phase 2 Results:**
- **Cloud SQL Instance**: `vexa-db` (PostgreSQL 15, 1 CPU, 4GB RAM)
- **Database**: `vexa`
- **Public IP**: `35.233.72.28`
- **Service Account**: `sql-proxy-sa@spry-pipe-425611-c4.iam.gserviceaccount.com`
- **Service Account Key**: `~/sql-proxy-key.json`

---

## **Automation**

*   **Objective**: Make the entire deployment process reproducible with a single command.
*   **Status**: `Completed`

| **Task**                                              | **Status**      |
| ----------------------------------------------------- | --------------- |
| **1. Create comprehensive Makefile**                 | `Completed`     |
| **2. Test full automation end-to-end**               | `Completed`     |

### **Key Features Implemented:**
- ✅ **Single Command Deployment**: `make all` runs phases 0-2 completely
- ✅ **Idempotent Operations**: Can be run multiple times safely  
- ✅ **Error Handling**: Gracefully handles existing resources
- ✅ **Status Reporting**: `make status` shows current deployment state
- ✅ **Modular Execution**: Individual phases can be run separately
- ✅ **Clean Documentation**: `make help` shows all available commands

### **Usage Examples:**
```bash
# Complete deployment in one command
make all

# Check current status
make status

# Individual phases
make phase0  # Environment setup
make phase1  # Build and push images
make phase2  # Cloud SQL setup
make phase3  # Provision Swarm cluster and deploy application

# Utilities
make clean-images    # Clean local images
make test-images     # Test registry connectivity
make destroy-swarm-infra # Destroy all cloud VMs and firewall rules
make help           # Show all commands
```

---

## **Notes & Decisions**

*   **Bot Manager**: The existing `bot-manager` service, which relies on direct access to the Docker socket (`/var/run/docker.sock`), will be deployed as a global service on all CPU nodes. This approach is a pragmatic first step that avoids a significant refactor while still allowing `vexa-bot` containers to be launched into the Swarm's `vexa-net` overlay network. Future work may replace this with direct Swarm API integration. 