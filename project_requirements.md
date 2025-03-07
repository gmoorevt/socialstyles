# Social Styles Assessment - Project Requirements

This document outlines the original requirements for the Social Styles Assessment web application.

## Core Requirements

- Use Python and the Flask framework
- Create a simple ability to take the questionnaire and collect the results
- Give the user detailed feedback about what their results are
- Plot the results in graphs that are in alignment with the Social Styles framework
- Create a results page that gives the user a lot of feedback on their score and how it relates to the framework
- Create deployment scripts to deploy to Digital Ocean
- Have a user give their email address to track their responses
- Store the results in a database
- Use Flask best practices
- Use a modern web UI
- Create a PDF report that the user can download

## Social Styles Framework

The application is based on the Social Styles framework, which categorizes individuals into four main styles:

1. **Driver**: High assertiveness, low responsiveness
2. **Expressive**: High assertiveness, high responsiveness
3. **Amiable**: Low assertiveness, high responsiveness
4. **Analytical**: Low assertiveness, low responsiveness

The assessment measures two key dimensions:
- **Assertiveness**: The degree to which a person is perceived as trying to influence others' thoughts and actions
- **Responsiveness**: The degree to which a person is perceived as showing emotions or demonstrating sensitivity to the feelings of others

## Technical Implementation

The application includes:

- User authentication system
- Assessment taking interface with paired opposites format
- Results calculation and visualization
- Detailed feedback based on the user's social style
- PDF report generation
- Database storage for user data and assessment results
- Responsive, modern UI design
- Deployment scripts for Digital Ocean hosting

## Deployment

The application is deployed on Digital Ocean with:

- Gunicorn as the WSGI server
- Systemd for service management
- Automatic startup after server reboots
- Monitoring and automatic restart capabilities

## Reference

The application is based on the Social Styles framework as described in:
https://programs.changeosity.com/wp-content/uploads/2020/07/2.0-Prework_Social-Styles-Self-Assessment-20200701.pdf 