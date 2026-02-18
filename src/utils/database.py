import psycopg2
import os

from configparser import ConfigParser
from typing import Optional, Any


class Database:
    """Singleton class for database connection management."""
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialised = False
        return cls._instance
    
    def __init__(self, config_file: str = 'database.ini', section: str = 'postgresql'):
        if self._initialised:
            return
        
        self.config_file = config_file
        self.section = section

        # Load configuration/connection parameters
        self.__load_config()

        # Initialise connection to database
        self.__create_db_connection(self.dbname)

        # Initialise database
        self.__initialise_db()
        self._initialised = True

    def __load_config(self) -> None:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(BASE_DIR, self.config_file)
        
        parser = ConfigParser()
        parser.read(filename)

        print("Fetching database connection parameters...")

        if parser.has_section(self.section):
            self.host = parser.get(self.section, 'host')
            self.port = parser.get(self.section, 'port')
            self.dbname = parser.get(self.section, 'dbname')
            self.user = parser.get(self.section, 'user')
            self.password = parser.get(self.section, 'password')
        else:
            raise Exception(f"Section '{self.section}' not found in file '{filename}'.")
        
        print(f"Configuration loaded from {self.config_file}, section: {self.section}")
        print(f"Connecting to database {self.dbname} on {self.host}:{self.port}...")
        self.__verify_database_exists()

    def __create_db_connection(self, dbname: str) -> None:
        try:
            self.connection = psycopg2.connect(
                dbname=dbname,
                user=self.user,
                password=self.password,
                port=self.port,
                host=self.host
            )
        except psycopg2.Error as e:
            print(f"Failed to connect to Database {dbname} on {self.host}. Error: {e}")

        print(f"→ Connected to database {dbname}.")

    def __initialise_db(self, path: str = 'init_sql') -> None:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(project_root, path)
        self.__execute_init_sql(full_path)

    def execute(self, query: str, *vars: Any) -> psycopg2.extensions.cursor:
        cur = self.connection.cursor()
        try:
            cur.execute(query, vars)
        except psycopg2.Error as e:
            if self.connection:
                self.connection.rollback()
            print(f"Error executing query... Error: {e}")
            raise
        
        return cur
    
    def execute_and_fetch_one(self, query: str, *vars: Any) -> Optional[Any]:
        cur = self.execute(query, *vars)
        return cur.fetchone()
    
    def execute_and_commit(self, query: str, *vars: Any) -> None:
        self.execute(query, *vars)
        self.connection.commit()

    def execute_and_fetchall(self, query: str, *vars: Any) -> list[tuple]:
        cur = self.execute(query, *vars)
        return cur.fetchall()
    
    def __create_database(self) -> None:
        self.execute("CREATE DATABASE %s", [self.dbname])
        self.connection.commit()

        print(f"Created Database {self.dbname}.")
    
    def __execute_init_sql(self, path: str) -> None:
        dir = os.scandir(path)

        print("="*60)

        for file in dir:
            if file.is_file() and file.name.endswith(".sql"):
                print(f"Running SQL file: {file.name}")
                
                with open(file.path, "r") as f:
                    sql = f.read()
                    self.execute_and_commit(sql)

    def __verify_database_exists(self):
        print("→ Testing PostgreSQL database connection...")
        test_dbname = "postgres"
        self.__create_db_connection(test_dbname)
        all_databases = self.execute_and_fetchall("SELECT datname FROM pg_database;")

        if (self.dbname,) not in all_databases:
            print(f"Database {self.dbname} does not exist. Creating {self.dbname}...")
            self.__create_database(self.dbname)

        self.close_db_connection(test_dbname)

    def close_db_connection(self, *dbname: str) -> None:
        if not dbname:
            dbname = self.dbname
        self.connection.close()
        print(f"→ Connection with database {dbname} ended.")