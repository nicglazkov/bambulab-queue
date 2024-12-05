# Bambu Lab Print Queue Manager

A web-based application for managing 3D print requests in a shared environment, specifically designed for Bambu Lab 3D printers. This system allows users to submit print jobs, administrators to manage requests, and provides a 3D preview of G-code files.

## Features

### Print Management

- Submit G-code files for printing
- Track print request status (pending, approved, denied)
- View detailed print information including:
  - Estimated print time
  - Material type and amount
  - Layer height
  - Custom notes

### G-code Visualization

- Interactive 3D preview of print files
- Visualize different aspects of the print:
  - Printing moves
  - Travel moves
  - Retractions
- Layer-by-layer viewing
- Build volume verification
- Customizable colors for different move types
- Multiple view angles (top, front, custom)

### User Management

- Simple user registration and login
- Optional email and ID number fields
- Admin user management interface
- First user automatically becomes admin
- Role-based access control

## Installation

### Using Docker (Recommended)

1. Clone the repository:

```bash
git clone https://github.com/nicglazkov/bambulab-queue.git
cd bambulab-queue
```

2. Build and run with Docker:

```bash
docker build -t bambulab-queue .
docker run -d -p 5000:5000 \
  -v uploads:/app/uploads \
  -v instance:/app/instance \
  bambulab-queue
```

3. Access the application at `http://localhost:5000`

### Manual Installation

Prerequisites:

- Python 3.12 or higher
- pip package manager

1. Clone the repository and install dependencies:

```bash
git clone https://github.com/nicglazkov/bambulab-queue.git
cd bambulab-queue
pip install -r requirements.txt
```

2. Run the application:

```bash
python app.py
```

3. Access the application at `http://localhost:5000`

## Initial Setup

1. Access the website for the first time
2. Register a new user account
   - The first user to register automatically becomes an administrator
3. Subsequent users will be registered as regular users
4. Administrators can manage users and approve print requests

## Usage

### For Users

1. Register an account
2. Log in to your account
3. Submit print requests:
   - Upload G-code files
   - Add notes to your request
   - View request status
4. View your print requests in the dashboard
5. Download or preview your G-code files

### For Administrators

1. Log in to your admin account
2. Manage print requests:
   - View all submitted requests
   - Approve or deny requests
   - Download and preview G-code files
3. Manage users:
   - View all users
   - Grant or revoke admin privileges
   - Delete users

## Development

### Project Structure

```
bambulab-queue/
├── app.py              # Main application file
├── templates/          # HTML templates
├── uploads/           # Upload directory for G-code files
└── instance/          # Instance-specific files (database)
```

### Key Dependencies

- Flask - Web framework
- Flask-SQLAlchemy - Database ORM
- Flask-Login - User authentication
- Three.js - 3D visualization

## Configuration

The application can be configured through environment variables:

- `FLASK_APP`: Set to `app.py`
- `FLASK_ENV`: Set to `production` for deployment
- `SECRET_KEY`: Set a secure secret key for session management

## Security Features

- Password strength requirements
- Secure file handling
- Role-based access control
- File type restrictions (G-code only)
