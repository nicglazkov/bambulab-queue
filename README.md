# Bambu Lab Print Queue Manager

A web-based application for managing 3D print requests in a shared environment, specifically designed for Bambu Lab 3D printers. This system allows users to submit print jobs, administrators to manage requests, and provides a 3D preview of G-code files.

## Features

- **User Authentication System**

  - User registration with email verification
  - Secure login system
  - Role-based access control (Admin/User)

- **Print Request Management**

  - Submit G-code files for printing
  - Track print request status
  - Add notes to print requests
  - Automatic G-code analysis for print parameters

- **Administrative Features**

  - User management interface
  - Print request approval/denial system
  - User role management

- **G-code Visualization**
  - 3D preview of print files
  - Build volume verification
  - Print dimensions display
  - Interactive model viewer

## Installation

### Prerequisites

- Python 3.12 or higher
- pip package manager
- SQLite3

### Using Docker

1. Build the Docker image:

```bash
docker build -t bambulab-queue .
```

2. Run the container:

```bash
docker run -d -p 5000:5000 -v uploads:/app/uploads -v instance:/app/instance bambulab-queue
```

### Manual Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/bambulab-queue.git
cd bambulab-queue
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Initialize the database:

```bash
python scripts/init_db.py
```

5. Create an admin user:

```bash
flask create-admin
```

6. Run the application:

```bash
python app.py
```

## Configuration

The application can be configured through environment variables:

- `FLASK_APP`: Set to `app.py`
- `FLASK_ENV`: Set to `production` for deployment
- `SECRET_KEY`: Set a secure secret key for session management

## Usage

1. Access the application at `http://localhost:5000`
2. Register a new user account or log in
3. Submit print requests through the web interface
4. Administrators can approve or deny print requests
5. Users can track their print request status

## Development

### Project Structure

```
bambulab-queue/
├── app.py              # Main application file
├── templates/          # HTML templates
├── scripts/           # Utility scripts
├── uploads/           # Upload directory for G-code files
└── instance/          # Instance-specific files
```

### Dependencies

Main dependencies include:

- Flask
- Flask-SQLAlchemy
- Flask-Login
- Three.js (for G-code visualization)
