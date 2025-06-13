#!/bin/bash
apt-get update
apt-get install -y docker.io google-cloud-sdk
gcloud auth configure-docker europe-west1-docker.pkg.dev --quiet
systemctl enable docker
systemctl start docker

echo "Finished running startup script" 