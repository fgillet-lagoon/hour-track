# Time Tracker Application

## Overview

A Flask-based time tracking application with Microsoft SAML SSO integration. The application allows users to log hours against projects and provides administrative capabilities for project management. It features a role-based access system with admin users having additional privileges to manage projects and view all time entries.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Flask with Jinja2 templating
- **UI Framework**: Bootstrap 5 with dark theme and Bootstrap Icons
- **Styling**: Custom CSS for enhanced UI components and form styling
- **Templates**: Modular template structure with base template inheritance
- **Client-side**: Minimal JavaScript, primarily server-side rendered

### Backend Architecture
- **Framework**: Flask web framework
- **Session Management**: Flask sessions with configurable secret key
- **Authentication**: SAML-based SSO integration with Microsoft Azure AD
- **Authorization**: Role-based access control with hardcoded admin users
- **Data Layer**: JSON file-based storage with DataManager abstraction
- **Logging**: Python logging module with debug-level configuration

### Data Storage
- **Storage Type**: JSON files in local filesystem
- **Data Structure**: 
  - Projects: ID, name, description, creation metadata
  - Time Entries: User, project, hours, date, notes
  - Users: User profile information
- **File Organization**: Centralized in `/data` directory
- **Initialization**: Automatic creation of default data and directory structure

### Authentication & Authorization
- **Primary Auth**: SAML 2.0 with Microsoft Azure AD
- **Session Management**: Flask sessions for user state persistence
- **Admin Access**: Hardcoded email-based admin user identification
- **Security**: Configurable SAML security settings including signing and encryption options

### Application Structure
- **Entry Point**: `main.py` for development server startup
- **Core Application**: `app.py` containing routes and business logic
- **Authentication Module**: `saml_auth.py` for SAML integration
- **Data Module**: `data_manager.py` for JSON file operations
- **Configuration**: SAML settings in JSON format with environment variable override support

## External Dependencies

### Authentication Services
- **Microsoft Azure AD**: SAML identity provider for SSO authentication
- **SAML Configuration**: Requires tenant ID and X.509 certificates for production use

### Frontend Libraries
- **Bootstrap 5**: UI framework loaded via CDN
- **Bootstrap Icons**: Icon library for UI components
- **Replit Bootstrap Theme**: Dark theme variant for consistent styling

### Python Libraries
- **Flask**: Web framework for application server
- **Standard Library**: datetime, json, os, logging, uuid, urllib, xml.etree.ElementTree for core functionality

### Development Infrastructure
- **File System**: Local JSON files for data persistence
- **Environment Variables**: Configuration for SAML settings and session secrets
- **Static Assets**: CSS and potential future JavaScript files served via Flask