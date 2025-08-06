import os
import logging
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import func, extract, or_, and_
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

@app.route('/entries')
@login_required
def view_entries():
    """Vue des statistiques globales avec recherche et pagination"""
    from datetime import timedelta
    
    # Récupérer les paramètres de recherche et pagination
    search_project = request.args.get('project', '')
    search_term = request.args.get('term', '')
    search_user = request.args.get('user', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Nombre d'entrées par page
    
    # Query de base pour toutes les entrées
    query = TimeEntry.query
    
    # Filtrage par projet si spécifié
    if search_project:
        query = query.filter(TimeEntry.project_id == search_project)
    
    # Filtrage par terme de recherche dans les notes
    if search_term:
        query = query.filter(TimeEntry.notes.ilike(f'%{search_term}%'))
    
    # Filtrage par utilisateur si spécifié
    if search_user:
        query = query.filter(TimeEntry.user_id == search_user)
    
    # Pagination des entrées filtrées avec détails
    entries_pagination = query.join(Project).join(User).order_by(TimeEntry.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    filtered_entries = entries_pagination.items
    
    # Récupérer tous les projets et utilisateurs pour les filtres
    projects = Project.query.all()
    users = User.query.all()
    
    # Récupérer toutes les entrées groupées par projet
    project_stats = db.session.query(
        Project.name.label('project_name'),
        func.sum(TimeEntry.hours).label('total_hours'),
        func.count(TimeEntry.id).label('entry_count')
    ).join(TimeEntry).group_by(Project.id, Project.name).all()
    
    # Récupérer les entrées récentes avec détails
    all_entries = db.session.query(TimeEntry, Project.name, User.username).join(
        Project, TimeEntry.project_id == Project.id
    ).join(
        User, TimeEntry.user_id == User.id
    ).order_by(TimeEntry.date.desc(), TimeEntry.created_at.desc()).all()
    
    # Calcul des heures par projet par mois pour les 12 derniers mois
    today = datetime.now().date()
    current_year = today.year
    current_month = today.month
    
    # Calculer l'année et le mois d'il y a 12 mois
    start_year = current_year
    start_month = current_month - 11
    if start_month <= 0:
        start_month += 12
        start_year -= 1
    
    monthly_project_stats = db.session.query(
        TimeEntry.year.label('year'),
        TimeEntry.month.label('month'),
        Project.name.label('project_name'),
        func.sum(TimeEntry.hours).label('total_hours')
    ).join(Project).filter(
        or_(
            and_(TimeEntry.year == start_year, TimeEntry.month >= start_month),
            and_(TimeEntry.year > start_year, TimeEntry.year <= current_year),
            and_(TimeEntry.year == current_year, TimeEntry.month <= current_month)
        )
    ).group_by(
        TimeEntry.year,
        TimeEntry.month,
        Project.id,
        Project.name
    ).order_by('year', 'month').all()
    
    # Créer la liste des 12 derniers mois avec noms français
    monthly_labels = []
    month_names = {
        1: 'Jan', 2: 'Fév', 3: 'Mar', 4: 'Avr', 5: 'Mai', 6: 'Juin',
        7: 'Juil', 8: 'Août', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Déc'
    }
    
    iter_year = start_year
    iter_month = start_month
    
    for i in range(12):
        month_name = f"{month_names[iter_month]} {iter_year}"
        monthly_labels.append(month_name)
        
        # Passer au mois suivant
        iter_month += 1
        if iter_month > 12:
            iter_month = 1
            iter_year += 1
    
    # Organiser les données par projet et par mois
    projects_monthly_data = {}
    for stat in project_stats:
        projects_monthly_data[stat.project_name] = [0] * 12
    
    iter_year = start_year
    iter_month = start_month
    
    for month_idx in range(12):
        month_total = 0
        month_data = {}
        
        # Calculer les heures par projet pour ce mois
        for stat in monthly_project_stats:
            if int(stat.year) == iter_year and int(stat.month) == iter_month:
                month_data[stat.project_name] = float(stat.total_hours)
                month_total += float(stat.total_hours)
        
        # Convertir en pourcentages
        for project_name in projects_monthly_data:
            if month_total > 0 and project_name in month_data:
                percentage = (month_data[project_name] / month_total) * 100
                projects_monthly_data[project_name][month_idx] = round(percentage, 1)
        
        # Passer au mois suivant
        iter_month += 1
        if iter_month > 12:
            iter_month = 1
            iter_year += 1
    

    
    return render_template('entries.html', 
                         project_stats=project_stats, 
                         all_entries=filtered_entries,
                         projects_monthly_data=projects_monthly_data,
                         monthly_labels=monthly_labels,
                         projects=projects,
                         users=users,
                         search_project=search_project,
                         search_term=search_term,
                         search_user=search_user,
                         pagination=entries_pagination)

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
        month_year = request.form.get('month_year')  # Format: "2025-01" (année-mois)
        notes = request.form.get('notes', '')
        
        # Validate input - hours can be more than 24 now
        if not project_id or hours <= 0 or not month_year:
            flash('Veuillez fournir un projet, des heures (> 0) et un mois valides.', 'error')
            return redirect(url_for('dashboard'))
        
        # Parse month and year
        try:
            year_str, month_str = month_year.split('-')
            year = int(year_str)
            month = int(month_str)
            if month < 1 or month > 12:
                raise ValueError("Mois invalide")
        except (ValueError, IndexError):
            flash('Format de mois invalide.', 'error')
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
        time_entry.month = month
        time_entry.year = year
        time_entry.notes = notes
        # Don't set old date fields
        
        db.session.add(time_entry)
        db.session.commit()
        
        # Success message showing the month
        month_display = time_entry.get_display_month()
        flash(f'{hours} heures enregistrées avec succès pour {month_display} !', 'success')
        
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

@app.route('/delete_entry/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    """Supprimer une entrée de temps"""
    try:
        entry = TimeEntry.query.get(entry_id)
        if not entry:
            flash('Entrée introuvable.', 'error')
            return redirect(url_for('dashboard'))
        
        # Vérifier les permissions
        # Les utilisateurs peuvent supprimer leurs propres entrées
        # Les admins peuvent supprimer toutes les entrées
        if not current_user.is_admin and entry.user_id != current_user.id:
            flash('Vous ne pouvez supprimer que vos propres entrées.', 'error')
            return redirect(url_for('dashboard'))
        
        # Récupérer les infos avant suppression pour le message
        project_name = entry.project.name
        hours = entry.hours
        
        db.session.delete(entry)
        db.session.commit()
        
        flash(f'Entrée supprimée : {hours}h sur {project_name}', 'success')
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'entrée: {str(e)}")
        flash('Erreur lors de la suppression. Veuillez réessayer.', 'error')
        db.session.rollback()
    
    # Rediriger vers la page d'origine
    referer = request.headers.get('Referer')
    if referer and '/entries' in referer:
        return redirect(url_for('view_entries'))
    else:
        return redirect(url_for('dashboard'))

@app.route('/edit_entry/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):
    """Modifier une entrée de temps"""
    try:
        entry = TimeEntry.query.get(entry_id)
        if not entry:
            flash('Entrée introuvable.', 'error')
            return redirect(url_for('dashboard'))
        
        # Vérifier les permissions
        if not current_user.is_admin and entry.user_id != current_user.id:
            flash('Vous ne pouvez modifier que vos propres entrées.', 'error')
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            # Traitement de la modification
            project_id_str = request.form.get('project_id')
            if not project_id_str:
                flash('Veuillez sélectionner un projet.', 'error')
                return redirect(url_for('edit_entry', entry_id=entry_id))
            
            project_id = int(project_id_str)
            hours = float(request.form.get('hours', 0))
            date_str = request.form.get('date')
            notes = request.form.get('notes', '')
            
            # Validation
            if not project_id or hours <= 0 or not date_str:
                flash('Veuillez fournir un projet, des heures et une date valides.', 'error')
                return redirect(url_for('edit_entry', entry_id=entry_id))
            
            # Vérifier que le projet existe
            project = Project.query.get(project_id)
            if not project:
                flash('Projet sélectionné invalide.', 'error')
                return redirect(url_for('edit_entry', entry_id=entry_id))
            
            # Parser la date
            try:
                entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Format de date invalide.', 'error')
                return redirect(url_for('edit_entry', entry_id=entry_id))
            
            # Mettre à jour l'entrée
            entry.project_id = project_id
            entry.hours = hours
            entry.date = entry_date
            entry.notes = notes
            
            db.session.commit()
            flash(f'Entrée modifiée avec succès : {hours}h sur {project.name}', 'success')
            
            # Rediriger vers la page d'origine
            referer = request.headers.get('Referer')
            if referer and '/entries' in referer:
                return redirect(url_for('view_entries'))
            else:
                return redirect(url_for('dashboard'))
        
        # GET - Afficher le formulaire d'édition
        projects = Project.query.all()
        return render_template('edit_entry.html', entry=entry, projects=projects)
        
    except Exception as e:
        logger.error(f"Erreur lors de la modification de l'entrée: {str(e)}")
        flash('Erreur lors de la modification. Veuillez réessayer.', 'error')
        db.session.rollback()
        return redirect(url_for('dashboard'))

@app.route('/my_entries')
@login_required
def my_entries():
    """Vue personnelle des entrées avec recherche et pagination"""
    from datetime import timedelta
    
    # Récupérer les paramètres de recherche et pagination
    search_project = request.args.get('project', '')
    search_term = request.args.get('term', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Nombre d'entrées par page
    
    # Query de base pour les entrées de l'utilisateur
    query = TimeEntry.query.filter_by(user_id=current_user.id)
    
    # Filtrage par projet si spécifié
    if search_project:
        query = query.filter(TimeEntry.project_id == search_project)
    
    # Filtrage par terme de recherche dans les notes
    if search_term:
        query = query.filter(TimeEntry.notes.ilike(f'%{search_term}%'))
    
    # Pagination des entrées triées par date décroissante avec les détails du projet
    entries_pagination = query.join(Project).order_by(TimeEntry.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    entries = entries_pagination.items
    
    # Récupérer tous les projets pour le filtre
    projects = Project.query.all()
    
    return render_template('my_entries.html', 
                         entries=entries, 
                         projects=projects,
                         search_project=search_project,
                         search_term=search_term,
                         pagination=entries_pagination)

@app.route('/my_entries/add', methods=['POST'])
@login_required
def add_my_entry():
    """Ajouter une nouvelle entrée depuis la vue personnelle"""
    try:
        project_id = request.form.get('project_id')
        hours = request.form.get('hours')
        month_year = request.form.get('month_year')
        notes = request.form.get('notes', '').strip()
        
        # Validation
        if not project_id or not hours or not month_year:
            flash('Le projet, les heures et le mois sont obligatoires.', 'error')
            return redirect(url_for('my_entries'))
        
        # Validation du projet
        project = Project.query.get(project_id)
        if not project:
            flash('Projet invalide.', 'error')
            return redirect(url_for('my_entries'))
        
        # Validation des heures - pas de limite à 24h
        try:
            hours_float = float(hours)
            if hours_float <= 0:
                flash('Le nombre d\'heures doit être positif.', 'error')
                return redirect(url_for('my_entries'))
        except ValueError:
            flash('Nombre d\'heures invalide.', 'error')
            return redirect(url_for('my_entries'))
        
        # Parse month and year
        try:
            year_str, month_str = month_year.split('-')
            year = int(year_str)
            month = int(month_str)
            if month < 1 or month > 12:
                raise ValueError("Mois invalide")
        except (ValueError, IndexError):
            flash('Format de mois invalide.', 'error')
            return redirect(url_for('my_entries'))
        
        # Créer l'entrée
        entry = TimeEntry()
        entry.user_id = current_user.id
        entry.project_id = project_id
        entry.hours = hours_float
        entry.month = month
        entry.year = year
        entry.notes = notes
        # Don't set old date fields
        
        db.session.add(entry)
        db.session.commit()
        
        # Success message with month display
        month_display = entry.get_display_month()
        flash(f'Entrée ajoutée: {hours_float}h sur {project.name} ({month_display})', 'success')
        
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout de l'entrée: {str(e)}")
        flash('Erreur lors de l\'ajout. Veuillez réessayer.', 'error')
        db.session.rollback()
    
    return redirect(url_for('my_entries'))

@app.route('/my_entries/edit/<int:entry_id>', methods=['GET', 'POST'])
@login_required 
def edit_my_entry(entry_id):
    """Éditer une entrée depuis la vue personnelle"""
    entry = TimeEntry.query.get_or_404(entry_id)
    
    # Vérifier que l'utilisateur peut modifier cette entrée
    if entry.user_id != current_user.id and not current_user.is_admin:
        flash('Vous ne pouvez modifier que vos propres entrées.', 'error')
        return redirect(url_for('my_entries'))
    
    if request.method == 'POST':
        try:
            project_id = request.form.get('project_id')
            hours = request.form.get('hours')
            month_year = request.form.get('month_year')
            notes = request.form.get('notes', '').strip()
            
            # Validation
            if not project_id or not hours or not month_year:
                flash('Le projet, les heures et le mois sont obligatoires.', 'error')
                return redirect(url_for('edit_my_entry', entry_id=entry_id))
            
            # Validation du projet
            project = Project.query.get(project_id)
            if not project:
                flash('Projet invalide.', 'error')
                return redirect(url_for('edit_my_entry', entry_id=entry_id))
            
            # Validation des heures - pas de limite
            try:
                hours_float = float(hours)
                if hours_float <= 0:
                    flash('Le nombre d\'heures doit être positif.', 'error')
                    return redirect(url_for('edit_my_entry', entry_id=entry_id))
            except ValueError:
                flash('Nombre d\'heures invalide.', 'error')
                return redirect(url_for('edit_my_entry', entry_id=entry_id))
            
            # Parse month and year
            try:
                year_str, month_str = month_year.split('-')
                year = int(year_str)
                month = int(month_str)
                if month < 1 or month > 12:
                    raise ValueError("Mois invalide")
            except (ValueError, IndexError):
                flash('Format de mois invalide.', 'error')
                return redirect(url_for('edit_my_entry', entry_id=entry_id))
            
            # Mettre à jour l'entrée
            entry.project_id = project_id
            entry.hours = hours_float
            entry.month = month
            entry.year = year
            entry.notes = notes
            
            db.session.commit()
            flash('Entrée modifiée avec succès !', 'success')
            return redirect(url_for('my_entries'))
            
        except Exception as e:
            logger.error(f"Erreur lors de la modification de l'entrée: {str(e)}")
            flash('Erreur lors de la modification. Veuillez réessayer.', 'error')
            db.session.rollback()
            return redirect(url_for('edit_my_entry', entry_id=entry_id))
    
    # GET request - afficher le formulaire d'édition
    projects = Project.query.all()
    return render_template('edit_my_entry.html', entry=entry, projects=projects)

@app.route('/my_entries/delete/<int:entry_id>', methods=['POST'])
@login_required
def delete_my_entry(entry_id):
    """Supprimer une entrée depuis la vue personnelle"""
    try:
        entry = TimeEntry.query.get_or_404(entry_id)
        
        # Vérifier que l'utilisateur peut supprimer cette entrée
        if entry.user_id != current_user.id and not current_user.is_admin:
            flash('Vous ne pouvez supprimer que vos propres entrées.', 'error')
            return redirect(url_for('my_entries'))
        
        project_name = entry.project.name
        hours = entry.hours
        
        db.session.delete(entry)
        db.session.commit()
        flash(f'Entrée supprimée: {hours}h sur {project_name}', 'success')
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'entrée: {str(e)}")
        flash('Erreur lors de la suppression. Veuillez réessayer.', 'error')
        db.session.rollback()
    
    return redirect(url_for('my_entries'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Changer le mot de passe de l'utilisateur connecté"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not current_password or not new_password or not confirm_password:
            flash('Tous les champs sont obligatoires.', 'error')
            return redirect(url_for('change_password'))
        
        if new_password != confirm_password:
            flash('La confirmation du mot de passe ne correspond pas.', 'error')
            return redirect(url_for('change_password'))
        
        if len(new_password) < 4:
            flash('Le mot de passe doit contenir au moins 4 caractères.', 'error')
            return redirect(url_for('change_password'))
        
        # Vérifier le mot de passe actuel
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Mot de passe actuel incorrect.', 'error')
            return redirect(url_for('change_password'))
        
        try:
            # Mettre à jour le mot de passe
            current_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Mot de passe modifié avec succès.', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            logger.error(f"Erreur lors du changement de mot de passe: {str(e)}")
            flash('Erreur lors du changement de mot de passe. Veuillez réessayer.', 'error')
            db.session.rollback()
    
    return render_template('change_password.html')

@app.route('/admin/change_user_password/<int:user_id>', methods=['POST'])
@login_required
def admin_change_user_password(user_id):
    """Changer le mot de passe d'un utilisateur (admin uniquement)"""
    if not current_user.is_admin:
        flash('Accès refusé. Seuls les administrateurs peuvent modifier les mots de passe.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        user = User.query.get(user_id)
        if not user:
            flash('Utilisateur introuvable.', 'error')
            return redirect(url_for('manage_users'))
        
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not new_password or not confirm_password:
            flash('Tous les champs sont obligatoires.', 'error')
            return redirect(url_for('manage_users'))
        
        if new_password != confirm_password:
            flash('La confirmation du mot de passe ne correspond pas.', 'error')
            return redirect(url_for('manage_users'))
        
        if len(new_password) < 4:
            flash('Le mot de passe doit contenir au moins 4 caractères.', 'error')
            return redirect(url_for('manage_users'))
        
        # Mettre à jour le mot de passe
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash(f'Mot de passe de {user.username} modifié avec succès.', 'success')
        
    except Exception as e:
        logger.error(f"Erreur lors du changement de mot de passe: {str(e)}")
        flash('Erreur lors du changement de mot de passe. Veuillez réessayer.', 'error')
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