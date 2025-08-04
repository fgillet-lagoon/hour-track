import os
import logging
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db, User, Project, TimeEntry

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key_change_in_production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_database():
    """Initialize database with tables and default users"""
    with app.app_context():
        db.create_all()
        
        # Check if users already exist
        if User.query.count() == 0:
            # Create default users
            admin_user = User()
            admin_user.username = 'fgillet'
            admin_user.is_admin = True
            admin_user.set_password('fgillet')
            
            regular_user = User()
            regular_user.username = 'htepa'
            regular_user.is_admin = False
            regular_user.set_password('htepa')
            
            db.session.add(admin_user)
            db.session.add(regular_user)
            db.session.flush()  # Flush to get the IDs
            
            # Create default projects
            project1 = Project()
            project1.name = 'Développement Site Web'
            project1.description = 'Développement frontend et backend du site web de l\'entreprise'
            project1.created_by_id = admin_user.id
            
            project2 = Project()
            project2.name = 'Application Mobile'
            project2.description = 'Développement de l\'application mobile iOS et Android'
            project2.created_by_id = admin_user.id
            
            db.session.add(project1)
            db.session.add(project2)
            
            try:
                db.session.commit()
                logger.info("Base de données initialisée avec les utilisateurs et projets par défaut")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
                db.session.rollback()

# Initialize database
init_database()

@app.route('/')
def index():
    """Page d'accueil - redirige vers le tableau de bord si connecté, sinon vers la connexion"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Veuillez entrer un nom d\'utilisateur et un mot de passe.', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            logger.info(f"Utilisateur connecté: {user.username}")
            flash(f'Bienvenue, {user.username} !', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Déconnexion de l'utilisateur"""
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord principal"""
    projects = Project.query.all()
    user_time_entries = TimeEntry.query.filter_by(user_id=current_user.id).order_by(TimeEntry.created_at.desc()).limit(10).all()
    
    # Calculate total hours per project for current user
    project_hours = {}
    all_user_entries = TimeEntry.query.filter_by(user_id=current_user.id).all()
    for entry in all_user_entries:
        project_id = entry.project_id
        hours = entry.hours
        if project_id in project_hours:
            project_hours[project_id] += hours
        else:
            project_hours[project_id] = hours
    
    return render_template('dashboard.html', 
                         projects=projects, 
                         project_hours=project_hours,
                         user_time_entries=user_time_entries)

@app.route('/log_time', methods=['POST'])
@login_required
def log_time():
    """Enregistrer du temps pour un projet"""
    try:
        project_id_str = request.form.get('project_id')
        if not project_id_str:
            flash('Veuillez sélectionner un projet.', 'error')
            return redirect(url_for('dashboard'))
        project_id = int(project_id_str)
        hours = float(request.form.get('hours', 0))
        date_str = request.form.get('date')
        notes = request.form.get('notes', '')
        
        # Validate input
        if not project_id or hours <= 0 or not date_str:
            flash('Veuillez fournir un projet, des heures et une date valides.', 'error')
            return redirect(url_for('dashboard'))
        
        # Parse date
        try:
            entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Format de date invalide.', 'error')
            return redirect(url_for('dashboard'))
        
        # Check if project exists
        project = Project.query.get(project_id)
        if not project:
            flash('Projet sélectionné invalide.', 'error')
            return redirect(url_for('dashboard'))
        
        # Create time entry
        time_entry = TimeEntry()
        time_entry.user_id = current_user.id
        time_entry.project_id = project_id
        time_entry.hours = hours
        time_entry.date = entry_date
        time_entry.notes = notes
        
        db.session.add(time_entry)
        db.session.commit()
        flash(f'{hours} heures enregistrées avec succès !', 'success')
        
    except ValueError:
        flash('Veuillez entrer un nombre d\'heures valide.', 'error')
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement du temps: {str(e)}")
        flash('Erreur lors de l\'enregistrement du temps. Veuillez réessayer.', 'error')
        db.session.rollback()
    
    return redirect(url_for('dashboard'))

@app.route('/admin')
@login_required
def admin():
    """Panneau d'administration"""
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges d\'administrateur requis.', 'error')
        return redirect(url_for('dashboard'))
    
    projects = Project.query.all()
    all_time_entries = TimeEntry.query.order_by(TimeEntry.created_at.desc()).all()
    users = User.query.all()
    
    return render_template('admin.html', 
                         projects=projects, 
                         time_entries=all_time_entries,
                         users=users)

@app.route('/admin/add_project', methods=['POST'])
@login_required
def add_project():
    """Ajouter un nouveau projet (admin seulement)"""
    if not current_user.is_admin:
        flash('Accès refusé.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Le nom du projet est requis.', 'error')
            return redirect(url_for('admin'))
        
        project = Project()
        project.name = name
        project.description = description
        project.created_by_id = current_user.id
        
        db.session.add(project)
        db.session.commit()
        flash(f'Projet "{name}" ajouté avec succès !', 'success')
        
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du projet: {str(e)}")
        flash('Erreur lors de l\'ajout du projet. Veuillez réessayer.', 'error')
        db.session.rollback()
    
    return redirect(url_for('admin'))

@app.route('/admin/remove_project/<int:project_id>', methods=['POST'])
@login_required
def remove_project(project_id):
    """Supprimer un projet (admin seulement)"""
    if not current_user.is_admin:
        flash('Accès refusé.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        project = Project.query.get(project_id)
        if project:
            db.session.delete(project)
            db.session.commit()
            flash('Projet supprimé avec succès !', 'success')
        else:
            flash('Projet introuvable.', 'error')
            
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du projet: {str(e)}")
        flash('Erreur lors de la suppression du projet. Veuillez réessayer.', 'error')
        db.session.rollback()
    
    return redirect(url_for('admin'))

@app.route('/admin/users')
@login_required
def manage_users():
    """Gestion des utilisateurs (admin seulement)"""
    if not current_user.is_admin:
        flash('Accès refusé. Privilèges d\'administrateur requis.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/admin/add_user', methods=['POST'])
@login_required
def add_user():
    """Ajouter un nouvel utilisateur (admin seulement)"""
    if not current_user.is_admin:
        flash('Accès refusé.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        is_admin = bool(request.form.get('is_admin'))
        
        if not username or not password:
            flash('Le nom d\'utilisateur et le mot de passe sont requis.', 'error')
            return redirect(url_for('manage_users'))
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Ce nom d\'utilisateur existe déjà.', 'error')
            return redirect(url_for('manage_users'))
        
        user = User()
        user.username = username
        user.is_admin = is_admin
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        flash(f'Utilisateur "{username}" ajouté avec succès !', 'success')
        
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout de l'utilisateur: {str(e)}")
        flash('Erreur lors de l\'ajout de l\'utilisateur. Veuillez réessayer.', 'error')
        db.session.rollback()
    
    return redirect(url_for('manage_users'))

@app.route('/admin/edit_user/<int:user_id>', methods=['POST'])
@login_required
def edit_user(user_id):
    """Modifier un utilisateur (admin seulement)"""
    if not current_user.is_admin:
        flash('Accès refusé.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        user = User.query.get(user_id)
        if not user:
            flash('Utilisateur introuvable.', 'error')
            return redirect(url_for('manage_users'))
        
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        is_admin = bool(request.form.get('is_admin'))
        
        if not username:
            flash('Le nom d\'utilisateur est requis.', 'error')
            return redirect(url_for('manage_users'))
        
        # Check if username already exists (except for current user)
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            flash('Ce nom d\'utilisateur existe déjà.', 'error')
            return redirect(url_for('manage_users'))
        
        user.username = username
        user.is_admin = is_admin
        
        if password:  # Only update password if provided
            user.set_password(password)
        
        db.session.commit()
        flash(f'Utilisateur "{username}" modifié avec succès !', 'success')
        
    except Exception as e:
        logger.error(f"Erreur lors de la modification de l'utilisateur: {str(e)}")
        flash('Erreur lors de la modification de l\'utilisateur. Veuillez réessayer.', 'error')
        db.session.rollback()
    
    return redirect(url_for('manage_users'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """Supprimer un utilisateur (admin seulement)"""
    if not current_user.is_admin:
        flash('Accès refusé.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        user = User.query.get(user_id)
        if not user:
            flash('Utilisateur introuvable.', 'error')
            return redirect(url_for('manage_users'))
        
        # Prevent deletion of current user
        if user.id == current_user.id:
            flash('Vous ne pouvez pas supprimer votre propre compte.', 'error')
            return redirect(url_for('manage_users'))
        
        db.session.delete(user)
        db.session.commit()
        flash(f'Utilisateur "{user.username}" supprimé avec succès !', 'success')
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'utilisateur: {str(e)}")
        flash('Erreur lors de la suppression de l\'utilisateur. Veuillez réessayer.', 'error')
        db.session.rollback()
    
    return redirect(url_for('manage_users'))

@app.errorhandler(404)
def not_found(error):
    """Gérer les erreurs 404"""
    return render_template('login.html', error="Page introuvable"), 404

@app.errorhandler(500)
def internal_error(error):
    """Gérer les erreurs 500"""
    logger.error(f"Erreur interne du serveur: {str(error)}")
    return render_template('login.html', error="Erreur interne du serveur"), 500