#!/bin/bash
# Setup environment variables for Vexa GCP deployment

export PROJECT="spry-pipe-425611-c4"
export REGION="europe-west1"
export ZONE="${REGION}-b" # Default zone
export REG_REPO="vexa"
export REG="${REGION}-docker.pkg.dev/${PROJECT}/${REG_REPO}"

echo "Environment variables set for Vexa GCP deployment:"
echo "PROJECT: ${PROJECT}"
echo "REGION:  ${REGION}"
echo "ZONE:    ${ZONE}"
echo "REG:     ${REG}"
echo ""
echo "Run 'source cloud_env_setup.sh' to apply these settings to your current shell." 