# Lagoon Time Tracker 🏗️

A comprehensive Flask-based time tracking web application with advanced analytics, user management, and project reporting capabilities.

## 🚀 Features

### Core Functionality
- **Time Tracking**: Record hours spent on projects with flexible date selection (daily or monthly entries)
- **Project Management**: Create, edit, and manage projects with descriptions
- **User Management**: Admin interface for user creation, modification, and role management
- **Advanced Analytics**: Interactive charts and statistics with Chart.js
- **Personal Dashboard**: User-specific views with personal statistics and search capabilities
- **Export Capabilities**: CSV export functionality for time reports

### User Experience
- **French Interface**: Complete French localization with Lagoon branding
- **Responsive Design**: Bootstrap 5 with custom Lagoon color scheme
- **Dark Theme**: Professional dark theme with Replit integration
- **Search & Filtering**: Advanced search capabilities across all data
- **Pagination**: Efficient data handling for large datasets

### Technical Features
- **Role-Based Access**: Admin and regular user permissions
- **Password Security**: Werkzeug password hashing
- **Database Integrity**: PostgreSQL with SQLAlchemy ORM
- **Session Management**: Flask-Login for secure authentication
- **Performance Optimized**: Efficient database queries and caching

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask (Python web framework)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Flask-Login with password hashing
- **Session Management**: Flask sessions with database storage
- **Server**: Gunicorn WSGI server

### Frontend
- **UI Framework**: Bootstrap 5 with custom Lagoon theme
- **Charts**: Chart.js for interactive data visualization
- **Icons**: Bootstrap Icons
- **Templating**: Jinja2 with template inheritance

### Infrastructure
- **Containerization**: Docker and Docker Compose
- **Database**: PostgreSQL 15 with Alpine Linux
- **Optional Tools**: pgAdmin for database management
- **Package Management**: UV for fast Python dependency management

## 📋 Prerequisites

- Docker and Docker Compose
- Git (for cloning the repository)
- Web browser (Chrome, Firefox, Safari, Edge)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd lagoon-time-tracker
```

### 2. Start with Docker Compose
```bash
# Start the application and database
docker-compose up -d

# Or start with pgAdmin for database management
docker-compose --profile tools up -d

# For testing (automated validation)
chmod +x scripts/test-docker.sh
./scripts/test-docker.sh
```

### 3. Access the Application
- **Main Application**: http://localhost:5000
- **pgAdmin** (optional): http://localhost:8080

### 4. Default Login Credentials
- **Admin User**: `fgillet` / `fgillet`
- **Regular User**: `htepa` / `htepa`

## 🔧 Configuration

### Environment Variables
The application uses the following environment variables:

```bash
# Database Configuration
DATABASE_URL=postgresql://lagoon_user:lagoon_password@db:5432/lagoon_timetracker

# Session Security
SESSION_SECRET=your-super-secret-session-key-change-in-production

# Application Environment
FLASK_ENV=production
```

### Docker Compose Services

#### Web Application (`web`)
- **Port**: 5000
- **Dependencies**: PostgreSQL database
- **Health**: Auto-restart unless stopped
- **Volumes**: Static files mounted read-only

#### PostgreSQL Database (`db`)
- **Port**: 5432
- **Database**: `lagoon_timetracker`
- **User**: `lagoon_user`
- **Volume**: Persistent data storage
- **Health Check**: Automatic service health monitoring

#### pgAdmin (`pgadmin`) - Optional
- **Port**: 8080
- **Default Email**: admin@lagoon.com
- **Default Password**: admin123
- **Profile**: `tools` (start with `--profile tools`)

## 🧪 Testing the Application

### 1. User Authentication
1. Navigate to http://localhost:5000
2. Login with default credentials
3. Verify role-based access (admin vs regular user)

### 2. Time Entry Management
1. **Add Time Entry**:
   - Select a project
   - Enter hours (no 24h limit)
   - Choose date or month/year
   - Add optional notes
   
2. **Edit/Delete Entries**:
   - Use the "Mes Entrées" section
   - Test search and filtering
   - Verify CRUD operations

### 3. Project Management (Admin Only)
1. **Create Project**:
   - Go to Administration
   - Add new project with name and description
   - Verify unique name validation
   
2. **Edit Project**:
   - Click pencil icon in project list
   - Modify name and description
   - Test validation rules

### 4. Analytics and Reports
1. **View Statistics**:
   - Check "Projet et Temps" section
   - Test user filtering
   - Verify chart responsiveness
   
2. **Personal Analytics**:
   - View "Mes Entrées" charts
   - Verify user-specific data filtering
   
3. **Export Data**:
   - Test CSV export functionality
   - Verify filtered exports

### 5. User Management (Admin Only)
1. **Manage Users**:
   - Create new users
   - Edit existing users
   - Test admin/regular role assignment
   
2. **Password Management**:
   - Change personal password
   - Admin change user passwords

## 📁 Project Structure

```
lagoon-time-tracker/
├── app.py                 # Main Flask application
├── models.py             # Database models (SQLAlchemy)
├── main.py               # Application entry point
├── templates/            # Jinja2 templates
│   ├── base.html         # Base template
│   ├── dashboard.html    # Main dashboard
│   ├── entries.html      # Time entries view
│   ├── my_entries.html   # Personal entries
│   ├── admin.html        # Administration panel
│   ├── users.html        # User management
│   └── edit_project.html # Project editing
├── static/               # Static assets
│   ├── style.css         # Custom CSS
│   └── lagoon-logo.svg   # Logo asset
├── docker/               # Docker configuration
│   └── init-db.sql       # Database initialization
├── Dockerfile            # Container definition
├── docker-compose.yml    # Multi-service configuration
├── pyproject.toml        # Python dependencies
└── README.md             # This file
```

## 🔍 Key Features Deep Dive

### Time Tracking System
- **Flexible Entry Types**: Daily entries or full month reporting
- **No Hour Limits**: Support for projects requiring >24h entries
- **Rich Notes**: Detailed descriptions for each time entry
- **Search Capabilities**: Filter by project, user, or note content

### Analytics Dashboard
- **Project Distribution**: Pie charts showing time allocation
- **Monthly Trends**: 12-month historical data with percentage breakdown
- **User Filtering**: Admin can view any user's statistics
- **Export Reports**: CSV downloads with filtering options

### Administrative Features
- **Project CRUD**: Complete project lifecycle management
- **User Management**: Create, edit, delete users with role assignment
- **Data Oversight**: View all time entries across the organization
- **Security Controls**: Admin-only access to sensitive operations

### User Experience
- **Intuitive Navigation**: Clear breadcrumbs and consistent UI
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Feedback**: Success/error messages for all operations
- **Efficient Pagination**: Handle large datasets gracefully

## 🚨 Production Considerations

### Security
- Change `SESSION_SECRET` in production
- Use strong database passwords
- Enable HTTPS in production environment
- Regular security updates for dependencies

### Performance
- Configure database connection pooling
- Implement Redis for session storage (large deployments)
- Use reverse proxy (nginx) for static file serving
- Monitor application performance and database queries

### Backup
- Regular PostgreSQL database backups
- Volume backup for persistent data
- Configuration backup for environment variables

### Monitoring
- Application health checks
- Database performance monitoring
- User activity logging
- Error tracking and alerting

## 📝 Development

### Local Development Setup
```bash
# Clone and setup
git clone <repository-url>
cd lagoon-time-tracker

# Start development environment
docker-compose up --build

# For development with auto-reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Database Management
```bash
# Access PostgreSQL directly
docker exec -it lagoon-time-tracker_db_1 psql -U lagoon_user -d lagoon_timetracker

# Backup database
docker exec lagoon-time-tracker_db_1 pg_dump -U lagoon_user lagoon_timetracker > backup.sql

# Restore database
docker exec -i lagoon-time-tracker_db_1 psql -U lagoon_user lagoon_timetracker < backup.sql
```

## 🐛 Troubleshooting

### Common Issues
1. **Database Connection Errors**: Check if PostgreSQL container is healthy
2. **Permission Denied**: Ensure correct file ownership in containers
3. **Port Conflicts**: Verify ports 5000, 5432, 8080 are available
4. **Memory Issues**: Increase Docker memory allocation if needed

### Logs Access
```bash
# View application logs
docker-compose logs web

# View database logs
docker-compose logs db

# Follow logs in real-time
docker-compose logs -f web
```

## 📄 License

This project is developed for Lagoon internal use. All rights reserved.

## 🤝 Support

For support and questions, contact the development team or refer to the internal documentation.

---

*Built with ❤️ by the Lagoon development team*