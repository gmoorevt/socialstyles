# Flask-Migrate Database Troubleshooting Guide

This guide provides detailed steps for troubleshooting and solving common Flask-Migrate issues when working with PostgreSQL databases.

## Common Issues and Solutions

### 1. Missing Migrations Directory

**Symptoms:**
- Error: "Error: Directory migrations does not exist"
- Cannot run `flask db upgrade` or `flask db migrate`

**Solutions:**

```bash
# Initialize the migrations directory
cd /var/www/socialstyles
export FLASK_APP=wsgi.py
flask db init
```

### 2. Alembic Version Control Tables Missing

**Symptoms:**
- Error: "Can't locate revision identified by..."
- Error about missing alembic_version table

**Solutions:**

```bash
# Check if alembic_version table exists
psql -U username -h hostname -d database_name -c "SELECT * FROM alembic_version;"

# If not exists, initialize migrations and create a blank first migration
export FLASK_APP=wsgi.py
flask db init
flask db migrate -m "initial migration"
flask db upgrade
```

### 3. Migration Script Errors

**Symptoms:**
- Errors when running `flask db migrate`
- Generated migrations with errors

**Solutions:**

- Check the generated migration file in `migrations/versions/`
- Edit the file to fix any errors
- If necessary, manually create a migration:

```bash
# Create an empty migration
flask db revision -m "manual migration"

# Edit the file in migrations/versions/ to add your changes
```

### 4. Migration Conflicts

**Symptoms:**
- Multiple heads in migration history
- Error: "Multiple head revisions are present"

**Solutions:**

```bash
# Check migration heads
flask db heads

# Create a merge migration
flask db merge heads
flask db upgrade
```

### 5. Database Connection Issues

**Symptoms:**
- Cannot connect to database
- Timeout errors

**Solutions:**

- Verify database connection string:

```bash
# Test PostgreSQL connection
export PGPASSWORD='your_password'
psql -U username -h hostname -p port -d database_name -c "SELECT 1;"
```

- Check if the server can access the database:

```bash
# Install and use netcat to test connectivity
apt-get install -y netcat
nc -zv database_hostname port
```

### 6. Complete Reset (Use with caution!)

If migrations are completely broken and you need to start over:

```bash
# Drop and recreate tables (WARNING: DESTROYS ALL DATA)
psql -U username -h hostname -d database_name -c "DROP TABLE alembic_version;"

# Remove migrations directory
rm -rf migrations/

# Reinitialize migrations
export FLASK_APP=wsgi.py
flask db init
flask db migrate -m "fresh start"
flask db upgrade

# Reinitialize application data
python initialize_assessment.py
```

## Step-by-Step Migration Process

For a clean migration process, follow these steps:

### 1. Backup Current Database

```bash
# Create a backup
pg_dump -U username -h hostname database_name > backup_before_migration.sql
```

### 2. Check Current Status

```bash
# Check current migration status
flask db current
flask db history
```

### 3. Create New Migration

```bash
# Create migration based on model changes
flask db migrate -m "description of changes"
```

### 4. Review Migration Script

Manually review the generated script in `migrations/versions/` to ensure it correctly represents your changes.

### 5. Apply Migration

```bash
# Apply the migration
flask db upgrade
```

### 6. Verify Changes

```bash
# Connect to database and verify changes
psql -U username -h hostname -d database_name -c "\dt"
psql -U username -h hostname -d database_name -c "SELECT * FROM alembic_version;"
```

## Diagnosing Migration Issues

To get more information about migration issues:

```bash
# Enable verbose output
flask db upgrade --verbose

# View migration SQL without applying
flask db upgrade --sql > migration.sql
```

## Special Case: First-Time PostgreSQL Setup

If setting up migrations for the first time with an existing PostgreSQL database:

1. Make sure models match existing tables
2. Initialize migrations:

```bash
export FLASK_APP=wsgi.py
flask db init
```

3. Create a "stamp" migration to mark current state:

```bash
flask db stamp head
```

4. Now you can make changes and create new migrations

## If All Else Fails: Direct SQL Approach

If Flask-Migrate continues to cause issues, you can manually execute SQL:

1. Create a SQL script with necessary changes
2. Apply it directly:

```bash
psql -U username -h hostname -d database_name -f your_changes.sql
```

3. If using Flask-Migrate in the future, stamp the current state:

```bash
flask db stamp revision_id
```

## Useful Commands

```bash
# Show current revision
flask db current

# Show migration history
flask db history

# Show pending migrations
flask db check

# Show SQL for migration without running
flask db upgrade --sql

# Downgrade to previous version
flask db downgrade

# Go to specific revision
flask db upgrade revision_id
```

Remember to always back up your database before performing migrations in production! 