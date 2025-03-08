# PostgreSQL Setup Guide for Social Styles Assessment

This guide will walk you through the process of setting up PostgreSQL for your Social Styles Assessment application on Digital Ocean.

## Prerequisites

1. A Digital Ocean account with a droplet running your Social Styles application
2. A PostgreSQL database created on Digital Ocean (or any other provider)
3. Database connection details (host, port, database name, username, password)

## Step 1: Create a PostgreSQL Database on Digital Ocean

1. Log in to your Digital Ocean account
2. Navigate to Databases in the left sidebar
3. Click "Create Database Cluster"
4. Select PostgreSQL as the database engine
5. Choose your preferred plan (Starter is fine for small applications)
6. Select a datacenter region (preferably the same region as your droplet)
7. Give your database cluster a name (e.g., `socialstyles-db`)
8. Click "Create Database Cluster"

Once your database cluster is created, you'll need to:

1. Create a database (e.g., `socialstyles`)
2. Create a user with appropriate permissions
3. Note down the connection details (host, port, database name, username, password)

## Step 2: Update Your Application to Use PostgreSQL

We've created two scripts to help you set up PostgreSQL for your Social Styles application:

1. `setup_postgres.sh`: Updates your application configuration to use PostgreSQL and initializes the database
2. `migrate_data.sh`: Migrates existing data from SQLite to PostgreSQL (if needed)

### Running the Setup Script

1. Run the setup script:
   ```bash
   ./setup_postgres.sh
   ```

2. Enter your PostgreSQL connection details when prompted:
   - Database Name: The name of your database (e.g., `socialstyles`)
   - Database User: The username for your database
   - Database Password: The password for your database
   - Database Host: The hostname or IP address of your database server
   - Database Port: The port number (default is 5432)

The script will:
- Install PostgreSQL client and dependencies on your server
- Install the psycopg2 Python package for PostgreSQL connectivity
- Update your application's configuration to use PostgreSQL
- Initialize the database with the required tables and initial data

### Migrating Existing Data (Optional)

If you have existing data in SQLite that you want to migrate to PostgreSQL, run the migration script:

```bash
./migrate_data.sh
```

This script will:
- Find your SQLite database file
- Connect to both SQLite and PostgreSQL databases
- Migrate all tables and data from SQLite to PostgreSQL
- Handle data type conversions as needed

## Step 3: Verify the Setup

After running the scripts, you should verify that your application is working correctly with PostgreSQL:

1. Visit your application at https://teamsocialstyles.com
2. Try to register a new user
3. Log in with an existing user (if you migrated data)
4. Take an assessment and check if the results are saved correctly

## Troubleshooting

If you encounter any issues, check the following:

### Database Connection Issues

1. Verify that your PostgreSQL connection details are correct
2. Make sure your Digital Ocean droplet can access the PostgreSQL server (check firewall rules)
3. Check if the PostgreSQL server is running and accepting connections

### Application Errors

1. Check the application logs for error messages:
   ```bash
   ssh root@67.205.184.178 "journalctl -u socialstyles.service -n 50"
   ```

2. Restart the application service:
   ```bash
   ssh root@67.205.184.178 "systemctl restart socialstyles.service"
   ```

### Database Migration Issues

1. If data migration fails, you can try running the migration script again
2. For specific table migration issues, you might need to manually migrate the data

## Conclusion

Your Social Styles Assessment application should now be using PostgreSQL as its database backend. This provides better performance, reliability, and scalability compared to SQLite.

If you need to make any changes to the database configuration in the future, you can update the `.env.production` file on your server:

```bash
ssh root@67.205.184.178 "nano /var/www/socialstyles/.env.production"
```

And update the `DATABASE_URL` line with your new connection details. 