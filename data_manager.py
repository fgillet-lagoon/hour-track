import json
import os
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class DataManager:
    """Manage data storage in JSON files"""
    
    def __init__(self):
        self.projects_file = 'data/projects.json'
        self.time_entries_file = 'data/time_entries.json'
        self.users_file = 'data/users.json'
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Initialize files if they don't exist
        self.initialize_files()
    
    def initialize_files(self):
        """Initialize JSON files with default data if they don't exist"""
        # Initialize projects file
        if not os.path.exists(self.projects_file):
            default_projects = [
                {
                    'id': self.generate_id(),
                    'name': 'Website Development',
                    'description': 'Frontend and backend development for company website',
                    'created_at': datetime.now().isoformat(),
                    'created_by': 'system'
                },
                {
                    'id': self.generate_id(),
                    'name': 'Mobile App',
                    'description': 'iOS and Android mobile application development',
                    'created_at': datetime.now().isoformat(),
                    'created_by': 'system'
                }
            ]
            self.save_json(self.projects_file, default_projects)
        
        # Initialize time entries file
        if not os.path.exists(self.time_entries_file):
            self.save_json(self.time_entries_file, [])
        
        # Initialize users file
        if not os.path.exists(self.users_file):
            self.save_json(self.users_file, [])
    
    def load_json(self, filename):
        """Load data from JSON file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading {filename}: {str(e)}")
            return []
    
    def save_json(self, filename, data):
        """Save data to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving {filename}: {str(e)}")
            raise
    
    def generate_id(self):
        """Generate unique ID"""
        return str(uuid.uuid4())
    
    def get_projects(self):
        """Get all projects"""
        return self.load_json(self.projects_file)
    
    def add_project(self, project):
        """Add new project"""
        projects = self.get_projects()
        projects.append(project)
        self.save_json(self.projects_file, projects)
    
    def remove_project(self, project_id):
        """Remove project by ID"""
        projects = self.get_projects()
        original_count = len(projects)
        projects = [p for p in projects if p['id'] != project_id]
        
        if len(projects) < original_count:
            self.save_json(self.projects_file, projects)
            
            # Also remove related time entries
            time_entries = self.get_all_time_entries()
            time_entries = [entry for entry in time_entries if entry['project_id'] != project_id]
            self.save_json(self.time_entries_file, time_entries)
            
            return True
        return False
    
    def get_all_time_entries(self):
        """Get all time entries"""
        return self.load_json(self.time_entries_file)
    
    def get_user_time_entries(self, user_email):
        """Get time entries for specific user"""
        all_entries = self.get_all_time_entries()
        return [entry for entry in all_entries if entry.get('user_email') == user_email]
    
    def add_time_entry(self, time_entry):
        """Add new time entry"""
        time_entries = self.get_all_time_entries()
        time_entries.append(time_entry)
        self.save_json(self.time_entries_file, time_entries)
    
    def save_user(self, user_data):
        """Save or update user data"""
        users = self.load_json(self.users_file)
        
        # Check if user exists
        user_email = user_data.get('email')
        existing_user_index = next((i for i, u in enumerate(users) if u.get('email') == user_email), None)
        
        user_record = {
            'email': user_email,
            'firstname': user_data.get('firstname', ''),
            'lastname': user_data.get('lastname', ''),
            'name': user_data.get('name', ''),
            'last_login': datetime.now().isoformat()
        }
        
        if existing_user_index is not None:
            users[existing_user_index] = user_record
        else:
            user_record['created_at'] = datetime.now().isoformat()
            users.append(user_record)
        
        self.save_json(self.users_file, users)
