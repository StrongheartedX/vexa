
Okay, let's summarize the current paradigm for scaling WhisperLive and the detailed plan we're implementing in Phase 2 (Local Docker Compose Setup).

**Current Paradigm & Strategy:**

1.  **Scaling Model:** We are implementing **horizontal scaling** by running multiple, independent instances of the WhisperLive server.
2.  **Load Balancing:** An external load balancer (Nginx within Docker Compose for now, transitioning to a Kubernetes Service/Ingress in production) sits in front of these instances. Its role is to distribute incoming client WebSocket connections across the available WhisperLive server replicas.
3.  **State Handling:**
    *   We acknowledge that each WhisperLive server instance might hold some temporary state related to an active connection (e.g., VAD state, last segments for context).
    *   However, we've determined that the *critical, long-term state* (meeting identity, user context, full collected transcript) resides *outside* the individual WhisperLive instance (handled by the connecting bot and the central Vexa `transcription-collector` service/API).
    *   Therefore, the standard requirement for "sticky sessions" (pinning a client to one specific backend instance for its entire lifetime) is relaxed.
    *   If a WhisperLive instance fails or restarts, the load balancer will direct a reconnecting client (assuming the client/bot handles reconnection) to a *different*, healthy instance. This is acceptable because the essential context travels with the bot's requests or is retrieved from the central collector. A brief interruption or potential loss of a few seconds of in-flight audio during reconnection is deemed an acceptable trade-off for simplified scaling.
4.  **Technology Stack:**
    *   **Local Development/Testing (Phase 2):** Docker Compose orchestrates all services, including multiple WhisperLive replicas, the Nginx load balancer, and a dedicated load testing client.
    *   **Production (Phase 3 Target):** Kubernetes will manage the deployment, scaling, and load balancing of the containerized WhisperLive service. The Docker image built now serves as the deployable unit.

**Detailed Plan Implementation (Phase 2 - Docker Compose):**

1.  **`docker-compose.yml` Configuration:**
    *   **`whisperlive` Service:**
        *   Uses your existing build configuration (`context: .`, `dockerfile: services/WhisperLive/Dockerfile.project`).
        *   Maintains existing `volumes` for model caching (`./hub`, `./services/WhisperLive/models`).
        *   Kept the original `command` to start the server (listening internally on port 9090).
        *   **Scaled:** Added a `deploy` section with `replicas: 3` to run three instances.
        *   **GPU Resources:** Configured under `deploy.resources` to allocate GPU access (`count: all`).
        *   **Networking:** Added to the new `whispernet` (for load balancer access) while keeping it on `vexa_default` (for potential internal communication like with `transcription-collector`, although the direct WebSocket URL in the environment suggests the *client* might be sending data there, not this service directly).
        *   **Ports:** Removed direct host port mapping (`ports: ["9090:9090"]`) as Nginx now handles external access.
    *   **`load-balancer` Service:**
        *   Runs the official `nginx:latest` image.
        *   Maps host port `9090` to its internal port `80`.
        *   Mounts the custom `./nginx.conf` file.
        *   Connects only to the `whispernet` network.
        *   Depends on the `whisperlive` service being started.
    *   **`load-tester` Service:**
        *   **Custom Image:** Built using `context: .` and `dockerfile: load-tester/Dockerfile`. This image includes Python 3.10, `ffmpeg`, `libsndfile1`, and Python dependencies (`websockets`, `numpy`, `soundfile`).
        *   **Volumes:** Mounts the host `./load_test_client.py` and `./test_audio` directory into `/app/` inside the container.
        *   **Command:** Runs `sleep infinity` as dependencies are installed in the image.
        *   **Networking:** Connects only to the `whispernet` network.
        *   Depends on the `load-balancer` service.
    *   **Existing Services:** Your other Vexa services (`api-gateway`, `admin-api`, `bot-manager`, `transcription-collector`, `redis`, `postgres`) remain defined as they were, using the `vexa_default` network.
    *   **Networks:** Defines both `vexa_default` (for original services) and `whispernet` (for the WhisperLive cluster + LB + tester).

2.  **`nginx.conf`:**
    *   Configures Nginx with an `upstream` block named `whisperlive_backend`.
    *   Uses Docker Compose's service discovery by referencing `server whisperlive:9090;` within the upstream block. Nginx will resolve `whisperlive` to the IPs of the running replicas.
    *   Listens on port 80 (internally).
    *   Proxies requests (`proxy_pass http://whisperlive_backend;`) and includes necessary headers (`Upgrade`, `Connection`) to correctly handle WebSocket traffic.

3.  **`load-tester/Dockerfile`:**
    *   Starts from `python:3.10-slim`.
    *   Installs `ffmpeg` and `libsndfile1` via `apt-get`.
    *   Copies `load-tester/requirements.txt` (relative to build context `.`) and installs Python packages via `pip`.
    *   Copies `load_test_client.py` and the `test_audio` directory (relative to build context `.`) into the image (though the volume mount will override the directory contents at runtime).
    *   Sets the default command to `sleep infinity`.

4.  **`load-tester/requirements.txt`:**
    *   Lists `websockets`, `numpy`, `soundfile`.

5.  **`load_test_client.py`:**
    *   An asyncio-based Python script.
    *   Takes arguments (`--num-clients`, `--host`, `--port`, `--audio-dir`).
    *   Connects (`args.num_clients`) concurrent WebSocket clients to the specified host/port (`load-balancer:80` by default).
    *   Randomly selects `.wav` files from the audio directory.
    *   Streams audio data in chunks, simulating real-time pacing.
    *   Includes basic error handling and summary reporting.
    *   Listens for incoming messages but primarily focuses on the sending/connection aspect for load generation.

6.  **`test_audio` Directory:**
    *   A directory (`/home/dima/vexa/test_audio`) intended to hold sample `.wav` files.
    *   **Crucially:** Currently contains invalid or unreadable audio files based on `ffmpeg` errors.

**Current Status & Immediate Next Steps:**

*   All necessary configuration files (`docker-compose.yml`, `nginx.conf`, `load-tester/Dockerfile`, `load-tester/requirements.txt`) and the client script (`load_test_client.py`) are in place.
*   The Docker services (including 3 `whisperlive` replicas) are running via `docker-compose up`.
*   The immediate **blocker** is the lack of valid `.wav` audio files in the `/home/dima/vexa/test_audio` directory that both `ffmpeg` (for potential conversion) and the `soundfile` library (within the client script) can read.
*   **Next actions required:**
    1.  Place at least one known-good, standard `.wav` file into `/home/dima/vexa/test_audio`.
    2.  (Optional but recommended) Use the `ffmpeg` command inside the `load-tester` container to convert this file to 16kHz mono 16-bit PCM (`*.converted.wav`) to ensure maximum compatibility.
    3.  Run the load test script using `docker-compose exec load-tester python load_test_client.py --num-clients <N>`.
