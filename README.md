# Social Styles Assessment

A web-based application for taking the Social Styles assessment, built with Flask.

## Features

- User registration and authentication
- Interactive Social Styles assessment with paired opposites format
- Dynamic visualization of results on the Social Styles grid
- Detailed feedback based on your social style (Analytical, Driver, Amiable, or Expressive)
- PDF report generation with comprehensive insights
- User dashboard for tracking assessment history

## Technology Stack

- **Backend**: Python, Flask
- **Database**: SQLAlchemy with SQLite
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Data Visualization**: Matplotlib
- **PDF Generation**: ReportLab

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/gmoorevt/socialstyles.git
   cd socialstyles
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```
   python initialize_assessment.py
   ```

5. Run the application:
   ```
   flask run
   ```

6. Access the application at http://localhost:5000

## Deployment

The application includes a comprehensive deployment script for Digital Ocean:

```bash
./improved_deploy.sh
```

The script provides an interactive menu with various deployment options:
- Full deployment (for new servers)
- Application update only (for code updates)
- Database operations (migrations and setup)
- Individual steps for customized deployments

Make sure to update the configuration variables at the top of the script before running.

For detailed deployment instructions, see the [Deployment Guide](DEPLOYMENT_GUIDE.md).

## Social Styles Framework

The Social Styles framework measures two key dimensions:
- **Assertiveness**: The degree to which you are perceived as trying to influence others' thoughts and actions
- **Responsiveness**: The degree to which you are perceived as showing emotions and building relationships

These dimensions create four quadrants representing different social styles:
- **Analytical**: Low assertiveness, low responsiveness
- **Driver**: High assertiveness, low responsiveness
- **Amiable**: Low assertiveness, high responsiveness
- **Expressive**: High assertiveness, high responsiveness

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- The Social Styles framework was developed by David Merrill and Roger Reid
- This application is for educational purposes only 