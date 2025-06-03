# Database Migration System

This document describes the Alembic-based database migration system for the Vexa project.

## Overview

Vexa uses **Alembic** for database schema management, providing:
- ✅ **Automated migration checks** during startup
- ✅ **Version-controlled schema changes**
- ✅ **Safe rollback capabilities**
- ✅ **Container-integrated workflow**
- ✅ **Development-friendly Make commands**

## Quick Reference

### Essential Commands

```bash
# Check if migrations are needed (automatic)
make migrate-check

# Show current migration status
make migrate-status

# View migration history
make migrate-history

# Run pending migrations
make migrate-run

# Generate new migration (development)
make migrate-generate MSG="Your description"
```

### Development Workflow

```bash
# 1. Modify models in libs/shared-models/shared_models/models.py
# 2. Rebuild containers
make all TARGET=gpu

# 3. Generate migration
make migrate-generate MSG="Add new feature"

# 4. Review generated migration file
cat libs/shared-models/alembic/versions/XXXXX_*.py

# 5. Apply migration
make migrate-run

# 6. Commit to version control
git add libs/shared-models/alembic/versions/
git commit -m "Add database migration for new feature"
```

## Migration Commands Reference

### `make migrate-check`
**Purpose**: Automatically checks if database needs migrations and runs them
**When to use**: Part of `make all`, but can be run manually
**Output**: 
- ✅ "Database is up to date" (no action needed)
- 🔄 "Database needs migrations" (automatically runs `migrate-run`)

### `make migrate-status`
**Purpose**: Shows current migration state and available migrations
**Output**:
```
---> Current migration:
7fa95b5a0eb7 (head)
---> Available migrations:
Rev: 7fa95b5a0eb7 (head)
Parent: <base>
Path: /app/alembic/versions/7fa95b5a0eb7_add_speaker_events_table_for_phase_2.py
```

### `make migrate-history`
**Purpose**: Shows complete migration history
**Output**:
```
<base> -> 7fa95b5a0eb7 (head), Add speaker_events table for Phase 2
```

### `make migrate-run`
**Purpose**: Applies pending migrations to database
**When to use**: When you have new migration files to apply
**Process**:
1. Copies alembic files to container
2. Runs `alembic upgrade head`
3. Copies updated files back to host

### `make migrate-force`
**Purpose**: Force runs migrations (development/debugging)
**When to use**: When `migrate-run` fails and you need to force apply
**Caution**: Use carefully in production

### `make migrate-generate MSG="Description"`
**Purpose**: Creates new migration based on model changes
**Requirements**: Must provide MSG parameter
**Example**: `make migrate-generate MSG="Add user preferences table"`
**Process**:
1. Copies current alembic files to container
2. Runs `alembic revision --autogenerate`
3. Copies new migration file back to host

### `make migrate-copy`
**Purpose**: Synchronizes migration files between container and host
**When to use**: After manual alembic operations in container
**Automatic**: Called by other migration commands

## File Structure

```
libs/shared-models/
├── alembic.ini                 # Alembic configuration
├── alembic/
│   ├── env.py                  # Migration environment setup
│   ├── script.py.mako          # Migration template
│   └── versions/               # Migration files
│       └── 7fa95b5a0eb7_add_speaker_events_table_for_phase_2.py
├── shared_models/
│   ├── models.py              # SQLAlchemy models
│   ├── schemas.py             # Pydantic schemas
│   └── database.py            # Database configuration
└── README.md                  # Package documentation
```

## Current Schema State

**Migration**: `7fa95b5a0eb7` - "Add speaker_events table for Phase 2"

**Tables**:
- ✅ `users` - Application users
- ✅ `api_tokens` - API authentication tokens  
- ✅ `meetings` - Meeting records with platform information
- ✅ `meeting_sessions` - Session tracking for reconnections
- ✅ `transcriptions` - Transcript segments with timestamps
- ✅ `speaker_events` - Speaker activity timeline (Phase 2)
- ✅ `alembic_version` - Migration version tracking

## Best Practices

### Before Making Changes
1. **Backup database** in production
2. **Test migrations** in development first
3. **Review generated migrations** before applying
4. **Coordinate with team** for schema changes

### Model Development
```python
# In libs/shared-models/shared_models/models.py
class NewModel(Base):
    __tablename__ = "new_table"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # ... other fields
```

### Schema Development
```python
# In libs/shared-models/shared_models/schemas.py
class NewModelBase(BaseModel):
    field_name: str

class NewModelCreate(NewModelBase):
    pass

class NewModelResponse(NewModelBase):
    id: int
    
    class Config:
        orm_mode = True
```

### Migration Generation
```bash
# After model changes
make all TARGET=gpu                    # Rebuild with new models
make migrate-generate MSG="Add new model"  # Generate migration
# Review the generated file in libs/shared-models/alembic/versions/
make migrate-run                       # Apply migration
```

## Troubleshooting

### Common Issues

#### "Migration failed" Error
```bash
# Check current state
make migrate-status

# Check database connectivity
docker-compose exec postgres psql -U postgres -d vexa -c "SELECT 1;"

# Check alembic version table
docker-compose exec postgres psql -U postgres -d vexa -c "SELECT * FROM alembic_version;"
```

#### "Container not running" Error
```bash
# Start services first
make up

# Then run migration commands
make migrate-check
```

#### "Permission denied" Error
```bash
# Ensure proper file permissions
chmod -R 755 libs/shared-models/alembic/
```

### Manual Recovery

If automated migration fails, you can run alembic commands manually:

```bash
# Enter container
docker-compose exec transcription-collector bash

# Navigate to app directory
cd /app

# Check alembic status
alembic current
alembic history

# Run specific migration
alembic upgrade head

# Or upgrade to specific revision
alembic upgrade <revision_id>
```

## Integration with Development

### Makefile Integration
The migration system is integrated with the main Makefile:
- `make all` includes automatic migration checking
- `make up` suggests running `make migrate-check`
- All migration commands follow consistent naming

### Docker Integration
- Migrations run inside the `transcription-collector` container
- Database connection uses existing environment variables
- Files are automatically synchronized between container and host

### Version Control
- Migration files are stored in `libs/shared-models/alembic/versions/`
- Each migration has a unique ID and descriptive message
- Migration history is preserved and trackable

## Production Considerations

### Deployment Process
```bash
# 1. Deploy new code
git pull origin main

# 2. Rebuild containers
make all TARGET=gpu

# 3. Check for migrations
make migrate-status

# 4. Apply if needed
make migrate-run

# 5. Verify success
make migrate-status
```

### Rollback Strategy
```bash
# View available versions
make migrate-history

# Rollback to previous version (manual)
docker-compose exec transcription-collector bash -c "cd /app && alembic downgrade -1"
```

### Monitoring
- Include `make migrate-status` in health checks
- Monitor migration logs during deployments
- Maintain database backups before schema changes

## Phase 2 Speaker Events

The current migration includes the complete **Phase 2 speaker events** schema:

### SpeakerEvent Model
```sql
CREATE TABLE speaker_events (
    id SERIAL PRIMARY KEY,
    meeting_id INTEGER NOT NULL,
    session_uid VARCHAR NOT NULL,
    participant_name VARCHAR(255) NOT NULL,
    participant_id_meet VARCHAR(255) NOT NULL,
    event_type speakereventtype NOT NULL,
    client_timestamp_ms INTEGER NOT NULL,
    server_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    absolute_timestamp TIMESTAMPTZ,
    
    FOREIGN KEY (meeting_id) REFERENCES meetings(id),
    -- Optimized indexes for timeline queries
    INDEX ix_speaker_event_meeting_absolute_time (meeting_id, absolute_timestamp),
    INDEX ix_speaker_event_participant_meeting (meeting_id, participant_id_meet, absolute_timestamp),
    INDEX ix_speaker_event_session_time (session_uid, client_timestamp_ms)
);
```

This enables:
- **Real-time speaker detection** with timeline tracking
- **Multi-session correlation** for reconnections
- **Efficient timeline queries** with optimized indexes
- **Speaker activity analysis** with start/end events

The migration system ensures this schema is consistently deployed across all environments. 