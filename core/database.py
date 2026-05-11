import mysql.connector
from .config import config

class Database:
    def __init__(self):
        # Optimized for OCI HeatWave / MySQL 8.x
        kwargs = {
            "host": config.DB_HOST,
            "port": config.DB_PORT,
            "user": config.DB_USER,
            "password": config.DB_PASSWORD,
            "database": config.DB_NAME,
            "ssl_disabled": True,  # OCI MySQL 9.6-cloud requires SSL disabled
            "use_pure": True,
            "connection_timeout": 10,
        }
        
        # OCI HeatWave often requires specific auth and SSL
        try:
            # Try with standard SSL (often works on OCI if CA is trusted or skipped)
            self.conn = mysql.connector.connect(**kwargs)
        except Exception as e:
            # Fallback for caching_sha2_password issues in non-SSL environments
            # Though OCI HeatWave usually forces SSL, we try to be resilient
            kwargs["auth_plugin"] = 'mysql_native_password'
            self.conn = mysql.connector.connect(**kwargs)
            
        self.conn.autocommit = False

    def get_cursor(self, dictionary=True):
        return self.conn.cursor(dictionary=dictionary)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        if self.conn.is_connected():
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        self.close()
