# Social Styles Assessment - Claude AI Context

## Project Overview

**Social Styles Assessment** is a Flask-based web application that helps users identify their social style based on the Social Styles framework developed by David Merrill and Roger Reid. The application measures assertiveness and responsiveness to categorize users into four social styles: Analytical, Driver, Amiable, or Expressive.

**Current Version:** 1.4.0
**Repository:** https://github.com/gmoorevt/socialstyles
**Production URL:** https://teamsocialstyles.com
**Server IP:** 134.209.128.212

## Project Architecture

### Technology Stack

- **Backend Framework:** Flask 2.3.3 (Python)
- **Database:**
  - SQLAlchemy 2.0.38 ORM
  - PostgreSQL (production) via psycopg2-binary
  - SQLite (development)
- **Frontend:**
  - HTML5, CSS3, JavaScript
  - Bootstrap 5
  - Socket.IO for real-time features
- **Authentication:** Flask-Login
- **Email:** Flask-Mail with AWS SES support (optional)
- **PDF Generation:** ReportLab
- **Data Visualization:** Matplotlib
- **Deployment:**
  - Docker containerized
  - Gunicorn WSGI server
  - Nginx reverse proxy
  - Cloudflare for DNS/SSL

### Application Structure

```
social-styles/
├── app/                          # Main application package
│   ├── __init__.py              # App factory and extensions
│   ├── models/                  # Database models
│   │   ├── user.py             # User model with auth
│   │   ├── assessment.py       # Assessment & results models
│   │   └── team.py             # Team collaboration models
│   ├── auth/                    # Authentication blueprint
│   ├── assessment/              # Assessment logic blueprint
│   ├── team/                    # Team management blueprint
│   ├── admin/                   # Admin dashboard blueprint
│   ├── main/                    # Main routes blueprint
│   ├── websockets/              # Socket.IO events
│   ├── templates/               # Jinja2 templates
│   └── static/                  # CSS, JS, images
├── migrations/                   # Alembic database migrations
├── config.py                    # Configuration classes
├── wsgi.py                      # Production entry point
├── app.py                       # Legacy entry point
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container definition
├── docker-compose.yml           # Docker orchestration
└── docker_deploy.sh            # Deployment script
```

## Core Features

### 1. Assessment System
- **Paired Opposites Format:** 30 questions measuring assertiveness (Q1-15) and responsiveness (Q16-30)
- **Scoring Algorithm:**
  - Assertiveness score: Average of responses 1-15
  - Responsiveness score: Average of responses 16-30
  - Cutoff point: 2.5 (midpoint of 1-4 scale)
- **Social Style Determination:**
  - **DRIVER:** High assertiveness (≥2.5), Low responsiveness (<2.5)
  - **EXPRESSIVE:** High assertiveness (≥2.5), High responsiveness (≥2.5)
  - **AMIABLE:** Low assertiveness (<2.5), High responsiveness (≥2.5)
  - **ANALYTICAL:** Low assertiveness (<2.5), Low responsiveness (<2.5)

### 2. User Management
- Registration and authentication system
- Password reset via email (JWT tokens, 1-hour expiration)
- Admin user roles (`is_admin` flag)
- Anonymous assessment support (`is_anonymous_assessment` flag)
- Last login tracking

### 3. Team Collaboration
- **Team Creation:** Users can create teams with name/description
- **Team Invitations:** Email-based invites with UUID tokens (7-day expiration)
- **Join URLs:** Base62-encoded shareable team links
- **Team Members:** Many-to-many relationship with roles (owner/member)
- **Team Dashboard:** Aggregate view of team member social styles

### 4. Reporting
- PDF report generation with ReportLab
- Social Styles grid visualization with Matplotlib
- Detailed feedback based on social style
- Assessment history dashboard

### 5. Admin Features
- User management and statistics
- Assessment results viewing
- System analytics dashboard

## Database Schema

### Key Models

**User** (`users` table)
- Fields: `id`, `email`, `password_hash`, `name`, `created_at`, `last_login`, `is_admin`, `is_anonymous_assessment`
- Relationships: `assessment_results`, `owned_teams`, `team_memberships`

**Assessment** (`assessments` table)
- Fields: `id`, `name`, `description`, `questions` (JSON), `created_at`
- Stores the assessment template/questions

**AssessmentResult** (`assessment_results` table)
- Fields: `id`, `user_id`, `assessment_id`, `responses` (JSON), `assertiveness_score`, `responsiveness_score`, `social_style`, `created_at`
- Stores individual user results

**Team** (`teams` table)
- Fields: `id`, `name`, `description`, `created_at`, `owner_id`
- Relationships: `members`, `invites`

**TeamMember** (`team_members` table)
- Fields: `id`, `team_id`, `user_id`, `role`, `joined_at`
- Junction table with unique constraint on (team_id, user_id)

**TeamInvite** (`team_invites` table)
- Fields: `id`, `team_id`, `email`, `token`, `status`, `created_at`, `expires_at`
- Status values: 'pending', 'accepted', 'rejected', 'expired', 'auto_accepted'

## Configuration

### Environment Variables

The application uses `.env` files for configuration:
- **`.env`** - Local development
- **`.env.local`** - Local overrides (takes precedence)
- **`.env.production`** - Production settings (not tracked in git)

**Key Environment Variables:**
```bash
# Flask
SECRET_KEY=<secure-random-key>
FLASK_CONFIG=development|production|testing

# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname  # Production
DEV_DATABASE_URL=sqlite:///social_styles_dev.db       # Development

# Email (SMTP or AWS SES)
USE_SES=True|False
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=<email>
MAIL_PASSWORD=<password>
MAIL_DEFAULT_SENDER=<email>

# AWS (if USE_SES=True)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>

# Application
APP_NAME=Social Styles Assessment
ADMIN_EMAIL=<admin-email>
```

### Configuration Classes

**DevelopmentConfig** (`config.py:51`)
- Debug mode enabled
- SQLite database
- CSRF enabled

**ProductionConfig** (`config.py:66`)
- PostgreSQL database from `DATABASE_URL`
- Logging to stderr
- CSRF with relaxed referrer checking

**TestingConfig** (`config.py:58`)
- In-memory SQLite
- CSRF disabled

## Development Workflow

### Local Setup

1. **Clone and setup:**
```bash
git clone https://github.com/gmoorevt/socialstyles.git
cd social-styles
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Initialize database:**
```bash
# Set up migrations (first time only)
flask db init

# Create and apply migrations
flask db migrate -m "Initial migration"
flask db upgrade

# Initialize assessment questions
python manage.py init-assessment
```

3. **Run locally:**
```bash
flask run --debug  # Development server with hot reload
```

### Database Migrations

The project uses Flask-Migrate (Alembic) for schema management:

```bash
# Create migration after model changes
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback
flask db downgrade

# View history
flask db history
```

**Important:** Always review generated migrations in `migrations/versions/` before applying.

### CLI Commands

Custom management commands via `manage.py`:
- `python manage.py init-assessment` - Initialize assessment questions in database

## Deployment

### Docker Deployment (Current Method)

The application uses Docker with external PostgreSQL:

**docker-compose.yml:**
- Single web service container
- Maps port 5001:5000
- Uses `.env` file for configuration
- Health check on `/health` endpoint
- Volume mount for logs: `./logs:/app/logs`
- Uses `host.docker.internal` for database access

**Dockerfile:**
- Base: `python:3.9-slim`
- Production WSGI: Gunicorn
- Entry point: `wsgi.py`

**Deployment Script:** `docker_deploy.sh`
```bash
./docker_deploy.sh  # Handles docker-compose down, build, up -d
```

### Legacy Deployment (improved_deploy.sh)

Interactive deployment script with options:
1. Full deployment (new servers)
2. Application update only
3. Database setup/migration
4. Individual deployment steps

**Configuration variables in script:**
- `DROPLET_IP`: 134.209.128.212
- `DOMAIN_NAME`: teamsocialstyles.com
- `GITHUB_REPO`: Repository URL
- `GITHUB_BRANCH`: Branch to deploy

### Production Server

- **Platform:** DigitalOcean Droplet
- **Web Server:** Nginx (reverse proxy)
- **Application Server:** Gunicorn
- **DNS/SSL:** Cloudflare (Flexible SSL mode)
- **Service Management:** systemd (`socialstyles.service`)

**Verify deployment:**
```bash
# Check service status
ssh -i ~/.ssh/id_ed25519 root@134.209.128.212 "systemctl status socialstyles.service"

# View logs
ssh -i ~/.ssh/id_ed25519 root@134.209.128.212 "journalctl -u socialstyles.service -f"
```

## File Paths Reference

### Entry Points
- **`wsgi.py`** - Production WSGI entry point (current)
- **`app.py`** - Legacy entry point (kept for compatibility)

### Core Application
- **`app/__init__.py:29`** - `create_app()` factory function
- **`config.py`** - Configuration classes

### Models
- **`app/models/user.py:10`** - User model
- **`app/models/assessment.py:5`** - Assessment model
- **`app/models/assessment.py:24`** - AssessmentResult model
- **`app/models/team.py:43`** - Team model
- **`app/models/team.py:28`** - TeamMember junction model
- **`app/models/team.py:101`** - TeamInvite model

### Blueprints
- **`app/auth/views.py`** - Authentication routes
- **`app/assessment/views.py`** - Assessment taking/results
- **`app/team/routes.py`** - Team management
- **`app/admin/views.py`** - Admin dashboard
- **`app/main/views.py`** - Main application routes

### Utilities
- **`app/assessment/utils.py`** - Assessment scoring logic
- **`app/email.py`** - Email sending (SMTP/SES)
- **`app/utils.py`** - Version info utilities
- **`app/decorators.py`** - Custom decorators
- **`app/commands.py`** - CLI commands

### Frontend
- **`app/templates/base.html`** - Base template
- **`app/static/js/social_styles_grid.js`** - Grid visualization
- **`app/static/js/main.js`** - Main JavaScript

### Scripts
- **`initialize_assessment.py`** - Loads assessment questions into DB
- **`manage.py`** - Management CLI
- **`docker_deploy.sh`** - Docker deployment
- **`improved_deploy.sh`** - Legacy deployment script

## Recent Changes (v1.4.0)

Latest commit: `ce4eace` - "Update Docker deployment to use external PostgreSQL database"

**Notable changes:**
- Migrated from embedded to external PostgreSQL database
- Docker deployment streamlined
- Removed SQLite from production
- Added CLI assessment initialization command
- Enhanced error handling in app initialization

**Deleted files (pending commit):**
- Documentation: DATABASE_MIGRATION_GUIDE.md, DEPLOYMENT_CHECKLIST.md, etc.
- Scripts: backup_database.sh, create_*.py, test_ses.py, postgres_setup_guide.md

**Untracked files (pending commit):**
- .dockerignore
- Dockerfile

## Testing & Quality

### Running Tests
```bash
pytest  # Run test suite
```

### Code Quality
- Uses Flask best practices
- Blueprint-based modular architecture
- Factory pattern for app creation
- Environment-based configuration
- Database migrations for schema management

## Common Issues & Solutions

### Database Connection
- **Local:** Uses SQLite by default (`social_styles_dev.db`)
- **Production:** Requires `DATABASE_URL` environment variable
- **Docker:** Uses `host.docker.internal` to connect to host PostgreSQL

### Cloudflare Issues
- SSL/TLS mode: Set to "Flexible" (Cloudflare handles SSL termination)
- Temporarily disable proxy to test direct connection
- Check DNS A record points to 134.209.128.212

### CSRF Errors
- `WTF_CSRF_SSL_STRICT = False` for compatibility
- Token expiration: 1 hour (`WTF_CSRF_TIME_LIMIT = 3600`)

### Email Delivery
- Supports both SMTP (Gmail) and AWS SES
- Toggle with `USE_SES` environment variable
- Test email functionality after configuration changes

## Development Best Practices

1. **Always test locally before deploying**
2. **Use feature branches** for development
3. **Update `version.txt`** for significant changes
4. **Create git tags** for releases (e.g., `v1.4.0`)
5. **Review migrations** before applying to production
6. **Back up database** before schema changes
7. **Monitor logs** after deployment
8. **Keep `.env.production` secure** (never commit)

## API Reference

### Key Functions

**Assessment Scoring** (`app/models/assessment.py:44`)
```python
def calculate_scores(self):
    """Calculate assertiveness and responsiveness scores based on responses."""
    # Returns tuple: (assertiveness_score, responsiveness_score)
```

**Social Style Determination** (`app/models/assessment.py:61`)
```python
def determine_social_style(self):
    """Determine the social style based on assertiveness and responsiveness scores."""
    # Returns: "EXPRESSIVE" | "DRIVER" | "AMIABLE" | "ANALYTICAL"
```

**Password Reset Token** (`app/models/user.py:48`)
```python
def generate_reset_token(self, expires_in=3600):
    """Generate a token for password reset that expires in 1 hour."""
    # Returns JWT token
```

**Team Join URL** (`app/models/team.py:86`)
```python
def get_join_url(self):
    """Get the URL for joining this team"""
    # Returns: Full URL with Base62-encoded token
```

## Social Styles Framework Reference

The assessment is based on the framework from:
https://programs.changeosity.com/wp-content/uploads/2020/07/2.0-Prework_Social-Styles-Self-Assessment-20200701.pdf

**Dimensions:**
- **Assertiveness:** Degree of influence on others' thoughts/actions (Low → High)
- **Responsiveness:** Degree of emotional expression and relationship-building (Low → High)

**Quadrants:**
```
        Low Assertiveness          High Assertiveness
       ┌─────────────────────────┬─────────────────────────┐
High   │      AMIABLE            │      EXPRESSIVE         │
Resp.  │  (Relationship-focused) │  (Energetic, Social)    │
       ├─────────────────────────┼─────────────────────────┤
Low    │      ANALYTICAL         │      DRIVER             │
Resp.  │  (Data-driven, Logical) │  (Results-oriented)     │
       └─────────────────────────┴─────────────────────────┘
```

## Future Considerations

- Consider adding integration tests
- Implement API endpoints for mobile/external access
- Add real-time team collaboration features (websockets already configured)
- Enhance admin analytics dashboard
- Consider adding assessment versioning
- Implement assessment result comparison tools

---

**For support or questions:** Contact admin at ADMIN_EMAIL (from environment variables)
**License:** MIT License
**Educational Use:** This application is for educational purposes only
