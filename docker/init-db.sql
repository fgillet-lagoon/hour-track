-- Initialize the database with some basic settings
-- This file is executed when the PostgreSQL container starts for the first time

-- Set timezone to UTC
SET timezone = 'UTC';

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE lagoon_timetracker TO lagoon_user;

-- This ensures the database is ready for the Flask application
-- The Flask app will create the actual tables via SQLAlchemy