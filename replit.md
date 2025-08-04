# Application de Suivi du Temps Lagoon

## Overview

Une application Flask de suivi du temps avec authentification basique par nom d'utilisateur/mot de passe. L'application permet aux utilisateurs d'enregistrer des heures sur des projets et fournit des capacités administratives pour la gestion de projets et d'utilisateurs. Elle dispose d'un système d'accès basé sur les rôles avec des utilisateurs administrateurs ayant des privilèges supplémentaires.

## Recent Changes (2025-08-04)

- **Migration d'authentification**: Changement de SAML SSO vers authentification basique login/password
- **Base de données PostgreSQL**: Migration de JSON vers PostgreSQL avec Flask-SQLAlchemy
- **Utilisateurs par défaut**: Création automatique de fgillet (admin) et htepa (utilisateur standard)
- **Interface française**: Toutes les interfaces traduites en français avec branding Lagoon
- **Gestion CRUD**: Interface complète pour la gestion des utilisateurs (admin uniquement)
- **Vue personnelle**: Nouvelle section "Mes Entrées" avec recherche par projet/terme et CRUD complet
- **Gestion des mots de passe**: Interface pour changer son mot de passe + admin peut changer celui des autres
- **Graphiques personnels**: 2 premiers graphiques de la vue globale adaptés à l'utilisateur individuel

## User Preferences

- Preferred communication style: Simple, everyday language.
- Language: French (all UI text and messages)
- Branding: Lagoon logo and color scheme (blue #2563EB and orange #EA580C)
- Authentication: Basic username/password (fgillet/fgillet pour admin, htepa/htepa pour utilisateur)

## System Architecture

### Frontend Architecture
- **Framework**: Flask with Jinja2 templating
- **UI Framework**: Bootstrap 5 with Replit dark theme and Bootstrap Icons
- **Styling**: Custom CSS with Lagoon color palette and gradient buttons
- **Templates**: Modular template structure with base template inheritance
- **Client-side**: Minimal JavaScript, primarily server-side rendered

### Backend Architecture
- **Framework**: Flask web framework with Flask-Login for session management
- **Authentication**: Simple username/password authentication with password hashing
- **Authorization**: Role-based access control with database-stored admin flags
- **Data Layer**: PostgreSQL database with SQLAlchemy ORM
- **Logging**: Python logging module with debug-level configuration

### Data Storage
- **Storage Type**: PostgreSQL database
- **Data Models**: 
  - Users: username, password_hash, is_admin, created_at
  - Projects: name, description, created_by_id, created_at
  - TimeEntries: user_id, project_id, hours, date, notes, created_at
- **Database Initialization**: Automatic table creation and default data seeding
- **Relationships**: Proper foreign keys and cascading deletes

### Authentication & Authorization
- **Primary Auth**: Flask-Login with username/password authentication
- **Password Security**: Werkzeug password hashing with salt
- **Session Management**: Flask sessions for user state persistence
- **Admin Access**: Database flag-based admin user identification
- **Default Users**: fgillet (admin), htepa (regular user)

### Application Structure
- **Entry Point**: `main.py` for Gunicorn server startup
- **Core Application**: `app.py` containing all routes and business logic
- **Data Models**: `models.py` with SQLAlchemy model definitions
- **Templates**: French language templates with Lagoon branding
  - `my_entries.html`: Vue personnelle avec recherche et graphiques
  - `edit_my_entry.html`: Formulaire d'édition d'entrée personnelle
  - `change_password.html`: Interface de changement de mot de passe
  - `users.html`: Gestion des utilisateurs avec modals séparées
- **Static Assets**: Custom CSS with Lagoon color scheme and logo

## External Dependencies

### Database Services
- **PostgreSQL**: Primary database for all application data
- **Environment Variables**: DATABASE_URL and related PG* variables

### Frontend Libraries
- **Bootstrap 5**: UI framework with Replit dark theme
- **Bootstrap Icons**: Icon library for UI components
- **Custom CSS**: Lagoon-branded styling with gradient effects

### Python Libraries
- **Flask**: Web framework and extensions (Flask-Login, Flask-SQLAlchemy)
- **SQLAlchemy**: ORM for database operations
- **Werkzeug**: Password hashing and security utilities
- **Gunicorn**: WSGI server for production deployment

### Development Infrastructure
- **PostgreSQL Database**: Persistent data storage
- **Environment Variables**: Configuration for database and session secrets
- **Static Assets**: Logo and custom CSS served via Flask