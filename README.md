<p align="left">
  <img src="assets/logodark.svg" alt="Vexa Logo" width="40"/>
</p>

# Vexa
# API for **Real-Time Meeting Transcription** and **Knowledge Extraction**

Vexa is an API for **real-time meeting transcription** using **meeting bots** and direct **streaming from web/mobile apps**. It extracts knowledge from various platforms including:

- **Google Meet**
- **Zoom**
- **Microsoft Teams**

Built as a **scalable multiuser service**, Vexa efficiently supports **thousands of simultaneous users** and **concurrent transcription sessions**. It's an **enterprise-grade** alternative to [recall.ai](https://recall.ai) with numerous extra features, designed specifically for **secure corporate environments** where **data security** and **compliance** are non-negotiable.

## API Capabilities

### Inputs:
- **Meeting Bots**: Automated bots that join your meetings on:
  - Google Meet
  - Zoom
  - Microsoft Teams
  - And more platforms

- **Direct Streaming**: Capture audio directly from:
  - Web applications
  - Mobile apps

### Features:
- **Real-time multilingual transcription** supporting **99 languages** with **Whisper**
- **Real-time processing with LLM** to improve readability and add extra features
- **Real-time translation** between supported languages
- **Meeting knowledge extraction** with **RAG** (Retrieval Augmented Generation) for finished meetings
- **MCP server** for Agent access to transcription data

## 📚 API Reference

<div align="center">
  <a href="https://api.dev.vexa.ai/docs">
    <img src="https://img.shields.io/badge/API-Documentation-2ea44f?style=for-the-badge" alt="API Documentation">
  </a>
</div>

Explore our comprehensive API documentation to quickly integrate Vexa's powerful transcription capabilities into your applications. Our interactive documentation provides:

- **Detailed Endpoints**: Complete reference for all API endpoints
- **Request Examples**: Code samples in multiple languages  
- **Response Schemas**: Clear specifications of all data structures
- **Authentication Guide**: Simple steps to secure your integration

## Scalability Architecture

Vexa is designed from the ground up as a **high-performance, scalable multiuser service**:

- **Microservice-based architecture** allowing independent scaling of components
- **Distributed processing** of transcription workloads
- **Horizontal scaling** to handle thousands of concurrent users
- **Multi-tenant design** with secure data isolation between organizations
- **Queue-based audio processing** for handling peak loads
- **Low-latency performance** (**5-10 seconds**) even at scale

## Current Status

- **Fully Functional**: Complete low-level transcription API that:
  - Receives **audio** and **speaker activations**
  - Returns **high-quality transcripts** in real-time

## Coming Next (April 2025)

### Bots Service for Automated Meeting Attendance
- Google Meet (Early April 2025)
- Microsoft Teams (April 2025)
- Zoom (April 2025)

### Web Component for Audio Streaming
- Web and Mobile Apps (Early April 2025)

### Documentation
- Comprehensive API Documentation (Early April 2025)

## Self-Deployment

For **security-minded companies**, Vexa offers complete **self-deployment** options.

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed setup instructions.

## Contributing

Contributors are welcome! Join our community and help shape Vexa's future:

- **Research & Discuss**: 
  - Review our **roadmap** in the [Project Tasks Board](https://github.com/Vexa-ai/vexa/projects)
  - Join discussions in our [Discord Community](https://discord.gg/Ga9duGkVz9)
  - Share your ideas and feedback

- **Get Involved**:
  - Browse available **tasks** in our task manager
  - Request task assignment through Discord
  - Submit **pull requests** for review

- **Critical Tasks**:
  - Selected **high-priority tasks** will be marked with **bounties**
  - Bounties are sponsored by the **Vexa core team**
  - Check task descriptions for bounty details and requirements

To contribute:
1. Join our Discord community
2. Review the roadmap and available tasks
3. Request task assignment
4. Submit a pull request

## Project Links

- 🌐 [Vexa Website](https://vexa.ai)
- 💼 [LinkedIn](https://www.linkedin.com/company/vexa-ai/)
- 🐦 [X (@grankin_d)](https://x.com/grankin_d)
- 💬 [Discord Community](https://discord.gg/Ga9duGkVz9)

## License

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Vexa is licensed under the **Apache License, Version 2.0**. See [LICENSE](LICENSE) for the full license text.

The Vexa name and logo are trademarks of **Vexa.ai Inc**. See [TRADEMARK.md](TRADEMARK.md) for more information.
