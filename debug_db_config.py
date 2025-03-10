#!/usr/bin/env python
"""
Debug script to determine why the application is using SQLite instead of PostgreSQL.
Run this script on the server to debug configuration issues.
"""

import os
import sys
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to load environment variables from .env file
logger.info("Looking for .env files...")
if os.path.exists('.env.production'):
    logger.info("Found .env.production, loading it")
    load_dotenv('.env.production')
elif os.path.exists('.env.local'):
    logger.info("Found .env.local, loading it")
    load_dotenv('.env.local')
elif os.path.exists('.env'):
    logger.info("Found .env, loading it")
    load_dotenv()
else:
    logger.warning("No .env file found!")

# Get the current directory
basedir = os.path.abspath(os.path.dirname(__file__))
logger.info(f"Base directory: {basedir}")

# Print environment variables related to Flask configuration
logger.info("==== Flask Configuration ====")
logger.info(f"FLASK_APP: {os.environ.get('FLASK_APP')}")
logger.info(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")
logger.info(f"FLASK_CONFIG: {os.environ.get('FLASK_CONFIG')}")
logger.info(f"FLASK_DEBUG: {os.environ.get('FLASK_DEBUG')}")

# Print database-related environment variables
logger.info("==== Database Configuration ====")
logger.info(f"DATABASE_URL: {os.environ.get('DATABASE_URL')}")
logger.info(f"DEV_DATABASE_URL: {os.environ.get('DEV_DATABASE_URL')}")
logger.info(f"TEST_DATABASE_URL: {os.environ.get('TEST_DATABASE_URL')}")

# Import app configuration to see what config would be used
try:
    logger.info("==== App Configuration Determination ====")
    # Simulate the logic in create_app() function
    config_name = os.environ.get('FLASK_CONFIG', None)
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    if config_name == 'production':
        config_name = 'production'
    else:
        config_name = 'development'
    
    logger.info(f"Determined config_name: {config_name}")
    
    # Import app config safely
    sys.path.insert(0, basedir)
    from config import config, ProductionConfig, DevelopmentConfig
    
    # Show what database URI would be used
    if config_name == 'production':
        logger.info("Using ProductionConfig")
        db_uri = os.environ.get('DATABASE_URL')
        logger.info(f"ProductionConfig SQLALCHEMY_DATABASE_URI: {db_uri}")
    else:
        logger.info("Using DevelopmentConfig")
        db_uri = os.environ.get('DEV_DATABASE_URL') or f'sqlite:///{os.path.join(basedir, "social_styles_dev.db")}'
        logger.info(f"DevelopmentConfig SQLALCHEMY_DATABASE_URI: {db_uri}")
        
    # Check if SQLite would be used as fallback
    if not db_uri or not db_uri.startswith('postgresql://'):
        logger.warning("No valid PostgreSQL DATABASE_URL - will use SQLite")
        sqlite_path = os.path.join(basedir, "social_styles_dev.db")
        logger.warning(f"SQLite path would be: {sqlite_path}")
        if os.path.exists(sqlite_path):
            logger.warning(f"SQLite database already exists at {sqlite_path}")
            
except ImportError as e:
    logger.error(f"Error importing config: {e}")
except Exception as e:
    logger.error(f"Error: {e}")

# Check for PostgreSQL vs SQLite dependencies
logger.info("==== Database Drivers ====")
try:
    import psycopg2
    logger.info("psycopg2 is installed (PostgreSQL driver)")
except ImportError:
    logger.warning("psycopg2 is NOT installed - PostgreSQL connections won't work")

try:
    import sqlite3
    logger.info("sqlite3 is available (SQLite driver)")
except ImportError:
    logger.info("sqlite3 is NOT available")

# Print debug information about wsgi.py
logger.info("==== WSGI Configuration ====")
wsgi_path = os.path.join(basedir, "wsgi.py")
if os.path.exists(wsgi_path):
    logger.info(f"wsgi.py exists at {wsgi_path}")
    with open(wsgi_path, 'r') as f:
        content = f.read()
        logger.info(f"wsgi.py contents:\n{content}")
else:
    logger.warning(f"wsgi.py not found at {wsgi_path}")

# Output summary
logger.info("==== SUMMARY ====")
logger.info(f"FLASK_ENV = {os.environ.get('FLASK_ENV')}")
logger.info(f"FLASK_CONFIG = {os.environ.get('FLASK_CONFIG')}")
logger.info(f"Determined config mode: {config_name}")
logger.info(f"DATABASE_URL present: {'Yes' if os.environ.get('DATABASE_URL') else 'No'}")
logger.info(f"Will use SQLite: {'Yes' if not db_uri or not db_uri.startswith('postgresql://') else 'No'}")

# Try to actually connect to the database
logger.info("==== Testing Database Connection ====")
if db_uri and db_uri.startswith('postgresql://'):
    try:
        import psycopg2
        # Extract connection parameters from the URI
        # Format: postgresql://username:password@hostname:port/database
        from urllib.parse import urlparse
        
        result = urlparse(db_uri)
        username = result.username
        password = result.password
        database = result.path[1:]
        hostname = result.hostname
        port = result.port or 5432
        
        logger.info(f"Attempting to connect to PostgreSQL: {hostname}:{port}/{database}")
        conn = psycopg2.connect(
            host=hostname,
            port=port,
            database=database,
            user=username,
            password=password
        )
        logger.info("PostgreSQL connection successful!")
        
        # Verify schema exists
        cursor = conn.cursor()
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public';")
        tables = cursor.fetchall()
        logger.info(f"Database tables: {tables}")
        
        conn.close()
    except Exception as e:
        logger.error(f"PostgreSQL connection error: {e}")
else:
    logger.warning("Not testing PostgreSQL connection - no valid PostgreSQL URI") 