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

The `improved_deploy.sh` script includes built-in functionality for PostgreSQL setup and data migration:

### Configuring PostgreSQL in the Deployment Script

1. Update the PostgreSQL settings in the `improved_deploy.sh` script:
   ```bash
   # PostgreSQL settings
   DB_USER="your_database_user" # PostgreSQL database user
   DB_NAME="your_database_name" # PostgreSQL database name
   ```

2. Update your `.env.production` file with the PostgreSQL connection string:
   ```
   DATABASE_URL=postgresql://username:password@hostname:port/database?sslmode=require
   ```

### Using the Deployment Script for PostgreSQL Setup

1. Run the deployment script:
   ```bash
   ./improved_deploy.sh
   ```

2. Select Option 3: "Database Setup/Migration" from the menu.

The script will:
- Install PostgreSQL client and dependencies on your server
- Configure your application to use PostgreSQL
- Run database migrations
- Initialize the application data

### Migrating Existing Data (Optional)

If you have existing data in SQLite that you want to migrate to PostgreSQL:

1. Run the deployment script:
   ```bash
   ./improved_deploy.sh
   ```

2. Select Option 4: "Database Migration" from the menu.

## Step 3: Verify the Setup

After running the deployment script, you should verify that your application is working correctly with PostgreSQL:

1. Visit your application URL
2. Try to register a new user
3. Log in with an existing user (if you migrated data)
4. Take an assessment and check if the results are saved correctly

## Troubleshooting

If you encounter any issues, check the following:

### Database Connection Issues

1. Verify that your PostgreSQL connection details are correct in your `.env.production` file
2. Make sure your Digital Ocean droplet can access the PostgreSQL server (check firewall rules)
3. Check if the PostgreSQL server is running and accepting connections

### Application Errors

1. Check the application logs for error messages:
   ```bash
   ./improved_deploy.sh
   # Select Option 6: "View Application Logs" from the menu
   ```

2. Restart the application service:
   ```bash
   ./improved_deploy.sh
   # Select Option 5: "Restart Application" from the menu
   ```

### Database Migration Issues

1. If data migration fails, you can try running the database migration again
2. For specific table migration issues, check the migrations log output

## Conclusion

Your Social Styles Assessment application should now be using PostgreSQL as its database backend. This provides better performance, reliability, and scalability compared to SQLite.

If you need to make any changes to the database configuration in the future, you can update the `.env.production` file and redeploy using the `improved_deploy.sh` script. 