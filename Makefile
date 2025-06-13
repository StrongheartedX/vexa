.PHONY: help all setup-env check-env phase0 phase1 phase2 phase3 \
        enable-apis create-registry build-images push-images \
        setup-cloudsql create-service-account test-connectivity test-images \
        clean-images clean-all status create-overlay-network create-worker-nodes \
        setup-secrets deploy-stack stack-status setup-iam-permissions \
        recreate-swarm init-swarm join-workers \
        create-firewall-rules create-manager-node destroy-swarm-infra

# Default target
all: phase0 phase1 phase2
	@echo "✅ All prerequisite phases (0-2) completed successfully!"
	@echo "Run 'make phase3' to provision the Swarm cluster and deploy the stack."
	@echo "Run 'make destroy-swarm-infra' to tear down all created cloud resources."

help:
	@echo "Vexa Cloud Deployment Makefile"
	@echo ""
	@echo "Quick Start:"
	@echo "  make all              # Complete phases 0-2 (setup, build, push, Cloud SQL)"
	@echo "  make phase3           # Provision Swarm, and deploy the application stack"
	@echo ""
	@echo "Individual Phases:"
	@echo "  make phase0           # Environment and tooling setup"
	@echo "  make phase1           # GCP setup, build and push images"
	@echo "  make phase2           # Cloud SQL and service account setup"
	@echo "  make phase3           # Provision Swarm, and deploy the application stack"
	@echo ""
	@echo "Utilities:"
	@echo "  make status           # Show current deployment status"
	@echo "  make test-images      # Test pulling images from registry"
	@echo "  make clean-images     # Remove local Docker images"
	@echo "  make clean-all        # Full cleanup (USE WITH CAUTION)"
	@echo "  make destroy-swarm-infra # Destroy all VMs and firewall rules."

# Configuration - can be overridden
PROJECT ?= spry-pipe-425611-c4
REGION ?= europe-west1
ZONE ?= $(REGION)-b
REG_REPO ?= vexa
REG ?= $(REGION)-docker.pkg.dev/$(PROJECT)/$(REG_REPO)
DB_INSTANCE ?= vexa-db
DB_NAME ?= vexa
SERVICE_ACCOUNT ?= sql-proxy-sa
MANAGER_NAME ?= swarm-manager-1
WORKER_PREFIX ?= cpu-worker
GCP_SA_KEY_PATH ?= $(HOME)/sql-proxy-key.json
CPU_MACHINE_TYPE ?= e2-standard-2

# Load environment variables from .env file if it exists
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

ADMIN_API_TOKEN ?= "change-me-to-a-secure-token"

# Ensure gcloud is configured
check-env:
	@echo "🔍 Checking environment..."
	@if ! which gcloud >/dev/null 2>&1; then \
		echo "❌ Error: gcloud CLI not found. Please install Google Cloud SDK."; \
		exit 1; \
	fi
	@if ! which docker >/dev/null 2>&1; then \
		echo "❌ Error: docker not found. Please install Docker."; \
		exit 1; \
	fi
	@echo "✅ Environment check passed"

setup-env: check-env
	@echo "🔧 Setting up environment variables..."
	@echo "PROJECT=$(PROJECT)"
	@echo "REGION=$(REGION)"
	@echo "ZONE=$(ZONE)"
	@echo "REG=$(REG)"
	@gcloud config set project $(PROJECT) || (echo "❌ Failed to set project. Make sure you have access to $(PROJECT)" && exit 1)
	@echo "✅ Environment configured"

# Phase 0: Tooling & Repository Bootstrap
phase0: setup-env
	@echo "🚀 Phase 0: Tooling & Repository Bootstrap"
	@echo "✅ Makefile ready"
	@echo "✅ Environment variables configured"
	@echo "✅ Phase 0 completed"

# Phase 1: Build & GCP Artifact Registry Setup
phase1: phase0 enable-apis create-registry build-images push-images test-images
	@echo "✅ Phase 1: Build & GCP Artifact Registry Setup completed"

enable-apis:
	@echo "🔧 Enabling required GCP APIs..."
	@gcloud services enable artifactregistry.googleapis.com compute.googleapis.com sqladmin.googleapis.com
	@echo "✅ GCP APIs enabled"

create-registry:
	@echo "🏗️  Creating Artifact Registry repository..."
	@gcloud artifacts repositories create $(REG_REPO) \
		--location=$(REGION) \
		--repository-format=docker || echo "ℹ️  Repository already exists"
	@gcloud auth configure-docker $(REGION)-docker.pkg.dev --quiet
	@echo "✅ Artifact Registry configured"

build-images:
	@echo "🔨 Building all Vexa service images..."
	@docker build -t $(REG)/api-gateway:latest           -f services/api-gateway/Dockerfile .
	@docker build -t $(REG)/admin-api:latest             -f services/admin-api/Dockerfile .
	@docker build -t $(REG)/bot-manager:latest           -f services/bot-manager/Dockerfile .
	@docker build -t $(REG)/vexa-bot:latest              -f services/vexa-bot/core/Dockerfile ./services/vexa-bot/core
	@docker build -t $(REG)/whisperlive:cpu-latest       -f services/WhisperLive/Dockerfile.cpu .
	@docker build -t $(REG)/collector:latest             -f services/transcription-collector/Dockerfile .
	@echo "✅ All images built successfully"

push-images:
	@echo "📤 Pushing images to GCP Artifact Registry..."
	@docker push $(REG)/api-gateway:latest
	@docker push $(REG)/admin-api:latest
	@docker push $(REG)/bot-manager:latest
	@docker push $(REG)/vexa-bot:latest
	@docker push $(REG)/whisperlive:cpu-latest
	@docker push $(REG)/collector:latest
	@echo "✅ All images pushed successfully"

test-images:
	@echo "🧪 Testing image availability..."
	@docker pull $(REG)/whisperlive:cpu-latest >/dev/null
	@echo "✅ Images accessible from registry"

# Phase 2: Cloud SQL Provisioning & Connectivity
phase2: phase1 setup-cloudsql create-service-account
	@echo "✅ Phase 2: Cloud SQL Provisioning & Connectivity completed"

setup-cloudsql:
	@echo "🗄️  Setting up Cloud SQL..."
	@gcloud sql instances create $(DB_INSTANCE) \
		--database-version=POSTGRES_15 \
		--cpu=1 \
		--memory=4GiB \
		--region=$(REGION) \
		--root-password="VexaDB123!" 2>/dev/null || echo "ℹ️  Cloud SQL instance already exists"
	@gcloud sql databases create $(DB_NAME) --instance=$(DB_INSTANCE) 2>/dev/null || echo "ℹ️  Database already exists"
	@echo "✅ Cloud SQL configured"

create-service-account:
	@echo "🔑 Creating service account for Cloud SQL access..."
	@gcloud iam service-accounts create $(SERVICE_ACCOUNT) \
		--display-name="Cloud SQL Proxy Service Account" 2>/dev/null || echo "ℹ️  Service account already exists"
	@gcloud projects add-iam-policy-binding $(PROJECT) \
		--member="serviceAccount:$(SERVICE_ACCOUNT)@$(PROJECT).iam.gserviceaccount.com" \
		--role="roles/cloudsql.client" >/dev/null
	@gcloud iam service-accounts keys create $(GCP_SA_KEY_PATH) \
		--iam-account=$(SERVICE_ACCOUNT)@$(PROJECT).iam.gserviceaccount.com 2>/dev/null || echo "ℹ️  Service account key already exists"
	@echo "✅ Service account configured"

# Phase 3: Docker Swarm Deployment
phase3: setup-iam-permissions init-swarm create-worker-nodes join-workers deploy-stack
	@echo "✅ Phase 3: Docker Swarm Deployment completed."
	@echo "Your Vexa application is running on a new Swarm Cluster."
	@make status

deploy-stack: setup-secrets
	@echo "🚀 Deploying the Vexa stack to the Swarm..."
	@echo "Substituting environment variables in docker-compose file..."
	@export REG=$(REG) PROJECT=$(PROJECT) && envsubst < vexa-cpu.yml > vexa-cpu-substituted.yml
	@gcloud compute scp --zone=$(ZONE) vexa-cpu-substituted.yml $(MANAGER_NAME):~/vexa-cpu.yml
	@gcloud compute ssh $(MANAGER_NAME) --zone=$(ZONE) --command="sudo docker stack deploy -c vexa-cpu.yml --with-registry-auth vexa-cpu"
	@rm vexa-cpu-substituted.yml
	@echo "✅ Stack deployment initiated."

destroy-stack:
	@echo "🔥 Removing the Vexa stack..."
	@gcloud compute ssh $(MANAGER_NAME) --zone=$(ZONE) --command="sudo docker stack rm vexa-cpu" >/dev/null 2>&1 || echo "ℹ️  Stack 'vexa-cpu' not found."
	@echo "🗑️  Removing secrets..."
	@gcloud compute ssh $(MANAGER_NAME) --zone=$(ZONE) --command="sudo docker secret rm gcp_sa_key db_pass admin_api_token" >/dev/null 2>&1 || echo "ℹ️  Secrets not found."
	@echo "🌐 Removing overlay network..."
	@gcloud compute ssh $(MANAGER_NAME) --zone=$(ZONE) --command="sudo docker network rm vexa-net" >/dev/null 2>&1 || echo "ℹ️  Network 'vexa-net' not found."

# Swarm Cluster Management
recreate-swarm: destroy-swarm-infra init-swarm create-worker-nodes join-workers
	@echo "✅ Swarm cluster has been recreated with the latest configuration."

init-swarm: create-manager-node create-firewall-rules
	@echo "🚀 Initializing Docker Swarm on the manager..."
	@echo "Waiting for manager VM startup script to finish... (Streaming logs)"
	@for j in 1 2 3; do \
		gcloud compute instances tail-serial-port-output $(MANAGER_NAME) --zone=$(ZONE) --port 1 | \
			while read line; do \
				echo "$$line"; \
				if echo "$$line" | grep -q "Finished running startup script"; then break; fi; \
			done && break || echo "Retry $$j: Waiting for startup script to finish..."; \
		sleep 5; \
	done
	@echo "✅ Manager startup script finished. Verifying Docker installation..."
	@gcloud compute ssh $(MANAGER_NAME) --zone=$(ZONE) --command="while ! sudo docker info > /dev/null 2>&1; do echo 'Waiting for Docker to start...'; sleep 3; done"
	@echo "✅ Docker is running on the manager."
	@if ! gcloud compute ssh $(MANAGER_NAME) --zone=$(ZONE) --command="sudo docker node ls" >/dev/null 2>&1; then \
		echo "--- Swarm not initialized. Clearing any lingering state and initializing now..."; \
		gcloud compute ssh $(MANAGER_NAME) --zone=$(ZONE) --command="sudo docker swarm leave --force" >/dev/null 2>&1; \
		MANAGER_IP=$$(gcloud compute instances describe $(MANAGER_NAME) --zone=$(ZONE) --format='get(networkInterfaces[0].networkIP)'); \
		gcloud compute ssh $(MANAGER_NAME) --zone=$(ZONE) --command="sudo docker swarm init --advertise-addr $$MANAGER_IP"; \
	else \
		echo "--- Swarm is already active on the manager."; \
	fi

create-firewall-rules:
	@echo "🔥 Creating firewall rules for Swarm..."
	@gcloud compute firewall-rules create swarm-internal --allow tcp:2377,tcp:7946,udp:7946,udp:4789 --source-tags=swarm-node --target-tags=swarm-node >/dev/null 2>&1 || echo "ℹ️  Firewall rule 'swarm-internal' already exists."
	@gcloud compute firewall-rules create swarm-ssh --allow tcp:22 --source-ranges=0.0.0.0/0 --target-tags=swarm-node >/dev/null 2>&1 || echo "ℹ️  Firewall rule 'swarm-ssh' already exists."
	@echo "✅ Firewall rules are in place."

create-manager-node:
	@echo "👑 Provisioning Swarm manager node..."
	@gcloud compute instances create $(MANAGER_NAME) \
		--zone=$(ZONE) \
		--machine-type=$(CPU_MACHINE_TYPE) \
		--tags=swarm-node,swarm-manager \
		--metadata-from-file=startup-script=gce-startup-script.sh >/dev/null 2>&1 || echo "ℹ️  VM '$(MANAGER_NAME)' already exists."
	@echo "✅ Swarm manager node provisioned."

create-worker-nodes: create-manager-node
	@echo "🌎 Creating Swarm worker nodes..."
	@for i in 1 2; do \
		if ! gcloud compute instances describe $(WORKER_PREFIX)-$$i --zone=$(ZONE) >/dev/null 2>&1; then \
			echo "--- Creating worker $(WORKER_PREFIX)-$$i..."; \
			gcloud compute instances create $(WORKER_PREFIX)-$$i \
				--zone=$(ZONE) \
				--machine-type=$(CPU_MACHINE_TYPE) \
				--image-project=debian-cloud \
				--image-family=debian-12 \
				--boot-disk-size=20GB \
				--scopes=cloud-platform \
				--metadata-from-file=startup-script=gce-startup-script.sh; \
		else \
			echo "--- Worker $(WORKER_PREFIX)-$$i already exists."; \
		fi; \
		echo "--- Waiting for worker $(WORKER_PREFIX)-$$i to finish startup script..."; \
		for j in 1 2 3; do \
			gcloud compute instances tail-serial-port-output $(WORKER_PREFIX)-$$i --zone=$(ZONE) --port 1 | \
				while read line; do \
					echo "$$line"; \
					if echo "$$line" | grep -q "Finished running startup script"; then break; fi; \
				done && break || echo "Retry $$j: Waiting for startup script to finish..."; \
			sleep 5; \
		done; \
		echo "✅ Worker $(WORKER_PREFIX)-$$i startup script finished. Verifying Docker installation..."; \
		gcloud compute ssh $(WORKER_PREFIX)-$$i --zone=$(ZONE) --command="while ! sudo docker info > /dev/null 2>&1; do echo 'Waiting for Docker to start on $(WORKER_PREFIX)-$$i...'; sleep 3; done"; \
		echo "✅ Docker is running on worker $(WORKER_PREFIX)-$$i."; \
	done
	@echo "✅ All worker nodes are running and Docker is ready."

join-workers: init-swarm create-worker-nodes
	@echo "🤝 Joining worker nodes to the Swarm..."
	@JOIN_TOKEN=$$(gcloud compute ssh $(MANAGER_NAME) --zone=$(ZONE) --command="sudo docker swarm join-token worker -q"); \
	MANAGER_IP=$$(gcloud compute instances describe $(MANAGER_NAME) --zone=$(ZONE) --format='get(networkInterfaces[0].networkIP)'); \
	for i in 1 2; do \
		echo "--- Joining worker $(WORKER_PREFIX)-$$i..."; \
		gcloud compute ssh $(WORKER_PREFIX)-$$i --zone=$(ZONE) --command="sudo docker swarm join --token $$JOIN_TOKEN $$MANAGER_IP:2377" || echo "Node is already part of the swarm."; \
	done
	@echo "✅ Worker nodes joined."

status:
	@echo "📊 Checking deployment status..."
	@echo "--- GCP Project Info ---"
	@gcloud config list
	@echo "--- Swarm Status (from manager) ---"
	@-gcloud compute ssh $(MANAGER_NAME) --zone=$(ZONE) --command="sudo docker node ls"
	@echo "--- Stack Services (from manager) ---"
	@-gcloud compute ssh $(MANAGER_NAME) --zone=$(ZONE) --command="sudo docker stack services vexa-cpu"

setup-iam-permissions:
	@echo "🔐 Granting IAM permissions to Compute Engine default service account..."
	@GCE_SA_EMAIL=$$(gcloud iam service-accounts list --filter="displayName:'Compute Engine default service account'" --format='value(email)'); \
	gcloud projects add-iam-policy-binding $(PROJECT) \
		--member="serviceAccount:$$GCE_SA_EMAIL" \
		--role="roles/artifactregistry.reader" >/dev/null 2>&1 || echo "ℹ️  Artifact Registry Reader role already exists for GCE SA."; \
	gcloud projects add-iam-policy-binding $(PROJECT) \
		--member="serviceAccount:$$GCE_SA_EMAIL" \
		--role="roles/cloudsql.client" >/dev/null 2>&1 || echo "ℹ️  Cloud SQL Client role already exists for GCE SA."; \
	gcloud projects add-iam-policy-binding $(PROJECT) \
		--member="serviceAccount:$$GCE_SA_EMAIL" \
		--role="roles/logging.logWriter" >/dev/null 2>&1 || echo "ℹ️  Logs Writer role already exists for GCE SA."
	@echo "✅ IAM permissions granted."

# Clean up
clean-images:
	@echo "🗑️  Removing local Docker images..."
	@docker rmi -f $(shell docker images -q "$(REG)/*") >/dev/null 2>&1 || echo "No images to remove."

destroy-swarm-infra:
	@echo "🔥 Destroying Swarm VMs and firewall rules. THIS IS DESTRUCTIVE."
	@echo -n "Are you sure you want to delete all Swarm VMs and firewall rules in project $(PROJECT)? [y/N] "; \
	old_stty_cfg=$$(stty -g); \
	stty raw -echo; \
	REPLY=$$(head -c 1); \
	stty $$old_stty_cfg; \
	echo; \
	case $$REPLY in \
		[Yy]) \
			echo "Proceeding with deletion..."; \
			gcloud compute instances delete $(MANAGER_NAME) $(WORKER_PREFIX)-1 $(WORKER_PREFIX)-2 --zone=$(ZONE) --quiet || echo "VMs not found."; \
			gcloud compute firewall-rules delete swarm-internal swarm-ssh --quiet || echo "Firewall rules not found."; \
			echo "✅ Infrastructure destroyed.";; \
		*) \
			echo "Aborted.";; \
	esac

clean-all: destroy-stack destroy-swarm-infra
	@echo "✅ Full cleanup complete."

setup-secrets: init-swarm
	@echo "🤫 Setting up secrets..."
	@echo "🔑 Setting up Docker Swarm secrets..."
	@if [ ! -f "$(GCP_SA_KEY_PATH)" ]; then echo "❌ SA Key not found at $(GCP_SA_KEY_PATH)!"; exit 1; fi
	@cat $(GCP_SA_KEY_PATH) | gcloud compute ssh $(MANAGER_NAME) --zone=$(ZONE) --command="sudo docker secret create gcp_sa_key -" >/dev/null 2>&1 || echo "ℹ️  Secret 'gcp_sa_key' already exists."
	@echo "VexaDB123!" | gcloud compute ssh $(MANAGER_NAME) --zone=$(ZONE) --command="sudo docker secret create db_pass -" >/dev/null 2>&1 || echo "ℹ️  Secret 'db_pass' already exists."
	@printf "%s" "$(ADMIN_API_TOKEN)" | gcloud compute ssh $(MANAGER_NAME) --zone=$(ZONE) --command="sudo docker secret create admin_api_token -" >/dev/null 2>&1 || echo "ℹ️  Secret 'admin_api_token' already exists."
	@echo "✅ Secrets configured."

stack-status:
	@echo "📋 Checking Vexa stack status..."
	@gcloud compute ssh $(MANAGER_NAME) --zone=$(ZONE) --command="sudo docker stack ps vexa"

clean-swarm:
	@echo "🔥 Tearing down the Swarm cluster..."
	@gcloud compute instances delete $(MANAGER_NAME) $(WORKER_PREFIX)-1 $(WORKER_PREFIX)-2 --zone=$(ZONE) --quiet || echo "ℹ️  Swarm VMs already deleted."
	@echo "✅ Swarm cluster deleted."

test-connectivity:
	@echo "🔗 Testing Cloud SQL connectivity..."
	@echo "This requires setting up the Cloud SQL Proxy locally"
	@echo "Command to run manually:"
	@echo "docker run --rm --name cloudsql-proxy -v ~/sql-proxy-key.json:/config/key.json -p 5432:5432 gcr.io/cloudsql-docker/gce-proxy:latest /cloud_sql_proxy -instances=$(PROJECT):$(REGION):$(DB_INSTANCE)=tcp:0.0.0.0:5432 -credential_file=/config/key.json" 