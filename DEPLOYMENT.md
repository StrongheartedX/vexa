# Quick start: Local Deployment and Testing

Instructions for setting up, running, and testing the Vexa system locally using Docker Compose and Make.

[3 min video tutorial](https://www.youtube.com/watch?v=bHMIByieVek)

### Quick Start with Make


1.  **For CPU (Tiny Model, Slower Performance - Good for local tests/development):**
   this will use 'whisper tiny' model, which can run on CPU.
    ```bash
    git clone https://github.com/Vexa-ai/vexa
    cd vexa
    make all
    ```
    This command (among other things) uses `env-example.cpu` defaults for `.env` if not present.

2.  **For GPU (Medium Model, Faster Performance - Requires NVIDIA GPU & Toolkit):**
    this will use 'whisper medium' model, which is good enough to run on GPU.
    ```bash
    git clone https://github.com/Vexa-ai/vexa
    cd vexa
    make all TARGET=gpu
    ```
    This uses `env-example.gpu` defaults for `.env` if not present.


### Testing the deployment

```bash
make test
```

What to expect during testing:
1. Test user and its token are created
2. You will be asked for a meeting ID
3. Provide the `xxx-xxxx-xxx` from your running meeting (`https://meet.google.com/xxx-xxxx-xxx`)
4. Bot is sent to the meeting you provided 
5. Wait about 10 sec for the bot to join the meeting
6. Let the bot into the conference
7. Start speaking
8. Wait for the transcripts to appear. 

Did it work? Tell us! 💬 [Join Discord Community!](https://discord.gg/Ga9duGkVz9)
 



The transcription latency can is higher and quality might be lower  when running locally in CPU mode, since you don't have a device to run bigger model quickly. But this is usually enough for development and testing





### API Documentation that is running behind the hood

API docs (Swagger/OpenAPI) are available at (ports are configurable in `.env`):

```
Main API docs:  http://localhost:8056/docs
Admin API docs: http://localhost:8057/docs
```

**Managing Services:**
- `make ps`: Show container status.
- `make logs`: Tail logs (or `make logs SERVICE=<service_name>`).
- `make down`: Stop services.
- `make clean`: Stop services and remove volumes.



## Database Migration Management

### Single Command Migration (Recommended)
The easiest way to migrate your database from **any prior version** to the latest:

```bash
# Migrate database from any prior version to latest (works with any setup)
make migrate-upgrade
```

This command automatically:
- ✅ Detects current database state (including completely fresh databases)
- ✅ Handles uninitialized databases 
- ✅ Upgrades from any prior version to latest
- ✅ Synchronizes migration files between host and container
- ✅ Provides clear success/failure feedback

### Automatic Migration Management (Used by `make all`)
```bash
# Start services and automatically check/run migrations if needed
make all TARGET=gpu

# Just check if database needs migrations (automatically runs them if needed)
make migrate-check
```

The `make all` command automatically calls `migrate-check`, which will upgrade the database if needed.

### Additional Migration Commands

```bash
# Show current migration status and pending migrations
make migrate-status

# Show complete migration history
make migrate-history

# Force run migrations (bypasses checks)
make migrate-force

# Synchronize migration files between host and container
make migrate-sync
```

### Development Migration Workflow
For developers making changes to database models:

```bash
# 1. Modify models in libs/shared-models/shared_models/models.py

# 2. Rebuild containers to get latest model changes
make all TARGET=gpu

# 3. Generate a new migration
make migrate-generate MSG="Add new speaker tracking feature"

# 4. Review the generated migration file in libs/shared-models/alembic/versions/

# 5. Apply the migration (or use migrate-upgrade for safety)
make migrate-upgrade

# 6. Commit the migration files to version control
git add libs/shared-models/alembic/versions/
git commit -m "Add migration for speaker tracking feature"
```

### Emergency Migration Commands (Development Only)

```bash
# DANGEROUS: Reset database to base state and re-apply all migrations
# This will DELETE ALL DATA - only use for development
make migrate-reset
```

The migration system is designed to be robust and handle:
- Fresh database installations
- Databases at any prior version
- Corrupted migration states (with migrate-force)
- Development workflow with auto-generation

