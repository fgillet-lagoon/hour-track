# Application de Suivi du Temps Lagoon

## Overview

Une application Flask de suivi du temps avec authentification basique par nom d'utilisateur/mot de passe. L'application permet aux utilisateurs d'enregistrer des heures sur des projets et fournit des capacités administratives pour la gestion de projets et d'utilisateurs. Elle dispose d'un système d'accès basé sur les rôles avec des utilisateurs administrateurs ayant des privilèges supplémentaires.

## Recent Changes (2025-08-10)

- **Système de couleurs complet**: Colonne couleur ajoutée aux projets avec migration sécurisée
- **Palette de couleurs**: 8 couleurs prédéfinies pour les projets avec sélection dans les formulaires
- **Graphiques colorés**: Couleurs des projets appliquées dans tous les graphiques (circulaires et mensuels)
- **Badges colorés**: Badges des projets colorés dans toutes les interfaces (/dashboard, /entries, /my_entries)
- **Cartes colorées**: Bordures gauches colorées sur les cartes de projets de la page d'accueil
- **Administration colorée**: Couleurs visibles dans les tableaux d'administration et formulaires
- **Interface cohérente**: Couleurs personnalisées utilisées partout pour distinguer visuellement les projets

## Previous Changes (2025-08-07)

- **Modification des projets**: Interface complète d'édition des projets avec validation
- **Graphiques personnels**: Ajout de graphiques dans "Mes Entrées" filtrés par utilisateur connecté
- **Filtrage des statistiques**: Graphiques intelligents avec filtrage par utilisateur sélectionné
- **Dockerisation complète**: Dockerfile, docker-compose.yml avec PostgreSQL et pgAdmin
- **Documentation complète**: README détaillé avec instructions d'installation et test
- **Configuration de production**: Variables d'environnement, health checks, et optimisations
- **Fonctionnalités d'export**: Boutons d'export CSV dans toutes les interfaces
- **Interface standardisée**: Border-radius cohérent sur tous les éléments UI
- **Gestion CRUD complète**: Interface pour modification/suppression de projets et utilisateurs
- **Authentification sécurisée**: Login/password avec hachage Werkzeug

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
  - Projects: name, description, color, created_by_id, created_at
  - TimeEntries: user_id, project_id, hours, month, year, notes, created_at
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
- **Chart.js**: Interactive charts for analytics and statistics
- **Custom CSS**: Lagoon-branded styling with gradient effects

### Python Libraries
- **Flask**: Web framework and extensions (Flask-Login, Flask-SQLAlchemy)
- **SQLAlchemy**: ORM for database operations
- **Werkzeug**: Password hashing and security utilities
- **Gunicorn**: WSGI server for production deployment
- **python-dateutil**: Precise date calculations for monthly statistics

### Development Infrastructure
- **Docker**: Containerization for consistent deployment environments
- **Docker Compose**: Multi-service orchestration (web app + database)
- **PostgreSQL Database**: Persistent data storage with health checks
- **UV Package Manager**: Fast Python dependency management
- **pgAdmin**: Optional web-based database administration tool
- **Static Assets**: Logo and custom CSS served via Flask