# Vexa Self-Deployment Guide

For security-minded companies, Vexa offers complete self-deployment options. This document provides detailed setup instructions.

## Prerequisites

- Git
- Docker and Docker Compose
- NVIDIA GPU with CUDA
- Minimum 4GB RAM
- Stable internet connection

## Step 1: Clone Repository

```bash
git clone https://github.com/Vexa-ai/vexa
cd vexa
git submodule update --init --recursive --remote
```

## Step 2: Set Up Whisper Service

```bash
cd whisper_service
cp .env.example .env
chmod +x start.sh
docker compose up -d
```

Check logs:

```bash
docker compose logs -f
```

## Step 3: Set Up Transcription Service

```bash
cd ../vexa-transcription-service
cp .env.example .env
# Set WHISPER_SERVICE_URL and WHISPER_API_TOKEN
docker compose up -d
```

## Step 4: Set Up Engine Service

```bash
cd ../vexa-engine
cp .env.example .env
docker compose up -d
# Optional clear existing transcripts
docker compose exec vexa-engine python clear_transcripts.py
```

## Step 5: Start Test Meeting API Calls Replay

```bash
cd ../vexa-testing-app
python register_test_user.py
python main.py
```

This will start sending API calls that simulate a meeting. Keep this terminal running for the duration of your test.

## Step 6: View Results (In a Separate Terminal)

While keeping the previous terminal with API calls running, open a new terminal and run:

```bash
cd ../vexa-engine
docker compose exec vexa-engine python demo.py
```

## Step 7: Access Documentation and Dashboards

After all services are running, you can access:

- Transcription Service Swagger: [http://localhost:8008/docs](http://localhost:8008/docs)
- Engine Service Swagger: [http://localhost:8010/docs](http://localhost:8010/docs)
- Ray Model Deployment Dashboard: [http://localhost:8265/#/overview](http://localhost:8265/#/overview)

## Troubleshooting

- Logs: `docker compose logs -f`
- Verify `.env` configurations
- Ensure GPU passthrough is correctly configured

## Security Considerations

Vexa is designed for secure on-premises deployment, making it ideal for organizations with strict data privacy requirements. All data remains within your infrastructure, and no data is sent to external services unless explicitly configured.

## Performance Optimization

For optimal performance:
- Use a dedicated GPU for transcription processing
- Ensure adequate network bandwidth for audio streaming
- Configure appropriate resource limits in Docker Compose files

## Support

For deployment assistance, please reach out on our [Discord Community](https://discord.gg/Ga9duGkVz9) or file an issue on GitHub. 