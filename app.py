import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
import json
from saml_auth import SAMLAuth
from data_manager import DataManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key_change_in_production")

# Initialize components
saml_auth = SAMLAuth()
data_manager = DataManager()

# Hardcoded admin users (email addresses)
ADMIN_USERS = [
    'admin@company.com',
    'manager@company.com'
]

def is_authenticated():
    """Check if user is authenticated"""
    return 'user_email' in session and 'user_name' in session

def is_admin():
    """Check if current user is an admin"""
    return is_authenticated() and session.get('user_email') in ADMIN_USERS

@app.route('/')
def index():
    """Main route - redirect to dashboard if authenticated, otherwise to login"""
    if is_authenticated():
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    """Login page"""
    if is_authenticated():
        return redirect(url_for('dashboard'))
    
    # Generate SAML login URL
    saml_login_url = saml_auth.get_login_url()
    return render_template('login.html', saml_login_url=saml_login_url)

@app.route('/saml/sso', methods=['POST'])
def saml_callback():
    """SAML callback endpoint"""
    try:
        # Process SAML response
        user_data = saml_auth.process_response(request.form.get('SAMLResponse', ''))
        
        if user_data:
            # Store user data in session
            session['user_email'] = user_data.get('email', '')
            session['user_name'] = user_data.get('name', '')
            session['user_firstname'] = user_data.get('firstname', '')
            session['user_lastname'] = user_data.get('lastname', '')
            
            # Store user data
            data_manager.save_user(user_data)
            
            logger.info(f"User authenticated: {session['user_email']}")
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Authentication failed. Please try again.', 'error')
            return redirect(url_for('login'))
            
    except Exception as e:
        logger.error(f"SAML authentication error: {str(e)}")
        flash('Authentication error occurred. Please try again.', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    if not is_authenticated():
        return redirect(url_for('login'))
    
    projects = data_manager.get_projects()
    user_time_entries = data_manager.get_user_time_entries(session['user_email'])
    
    # Calculate total hours per project for current user
    project_hours = {}
    for entry in user_time_entries:
        project_id = entry['project_id']
        hours = entry['hours']
        if project_id in project_hours:
            project_hours[project_id] += hours
        else:
            project_hours[project_id] = hours
    
    return render_template('dashboard.html', 
                         projects=projects, 
                         project_hours=project_hours,
                         user_time_entries=user_time_entries,
                         is_admin=is_admin())

@app.route('/log_time', methods=['POST'])
def log_time():
    """Log time for a project"""
    if not is_authenticated():
        return redirect(url_for('login'))
    
    try:
        project_id = request.form.get('project_id')
        hours = float(request.form.get('hours', 0))
        date = request.form.get('date')
        notes = request.form.get('notes', '')
        
        # Validate input
        if not project_id or hours <= 0 or not date:
            flash('Please provide valid project, hours, and date.', 'error')
            return redirect(url_for('dashboard'))
        
        # Check if project exists
        projects = data_manager.get_projects()
        if not any(p['id'] == project_id for p in projects):
            flash('Invalid project selected.', 'error')
            return redirect(url_for('dashboard'))
        
        # Create time entry
        time_entry = {
            'id': data_manager.generate_id(),
            'user_email': session['user_email'],
            'project_id': project_id,
            'hours': hours,
            'date': date,
            'notes': notes,
            'created_at': datetime.now().isoformat()
        }
        
        data_manager.add_time_entry(time_entry)
        flash(f'Successfully logged {hours} hours!', 'success')
        
    except ValueError:
        flash('Please enter a valid number of hours.', 'error')
    except Exception as e:
        logger.error(f"Error logging time: {str(e)}")
        flash('Error logging time. Please try again.', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/admin')
def admin():
    """Admin panel"""
    if not is_authenticated():
        return redirect(url_for('login'))
    
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    projects = data_manager.get_projects()
    all_time_entries = data_manager.get_all_time_entries()
    
    return render_template('admin.html', projects=projects, time_entries=all_time_entries)

@app.route('/admin/add_project', methods=['POST'])
def add_project():
    """Add new project (admin only)"""
    if not is_authenticated() or not is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Project name is required.', 'error')
            return redirect(url_for('admin'))
        
        project = {
            'id': data_manager.generate_id(),
            'name': name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'created_by': session['user_email']
        }
        
        data_manager.add_project(project)
        flash(f'Project "{name}" added successfully!', 'success')
        
    except Exception as e:
        logger.error(f"Error adding project: {str(e)}")
        flash('Error adding project. Please try again.', 'error')
    
    return redirect(url_for('admin'))

@app.route('/admin/remove_project/<project_id>', methods=['POST'])
def remove_project(project_id):
    """Remove project (admin only)"""
    if not is_authenticated() or not is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        if data_manager.remove_project(project_id):
            flash('Project removed successfully!', 'success')
        else:
            flash('Project not found.', 'error')
            
    except Exception as e:
        logger.error(f"Error removing project: {str(e)}")
        flash('Error removing project. Please try again.', 'error')
    
    return redirect(url_for('admin'))

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('login.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return render_template('login.html', error="Internal server error"), 500
