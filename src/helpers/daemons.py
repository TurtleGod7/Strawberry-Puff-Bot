from sqlite3 import connect
from os import name as os_name
from platform import uname as os_uname
from time import sleep
from threading import Thread, Lock
from atexit import register
from ctypes import windll
from subprocess import Popen
from pathlib import Path

class BannedUsersHandler:
    def __init__(self, db_name="users.db", interval=1800):
        # Resolve path to: src/assets/database/users.db
        base_dir = Path(__file__).resolve().parent.parent  # goes from src/helpers -> src
        db_path = str(base_dir / "assets" / "database" / db_name)  # goes from src -> assets/database/users.db
        self.conn = connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.interval = interval
        self.data_lock = Lock()
        self.pending_data = []  # Store new data to commit later

        # Start periodic saving
        self._start_commit_thread()

        # Ensure final save on exit
        register(self.close)

    def add_data(self, data):
        """Queue new data for saving. Must be in format of [(username, time), ...]"""
        with self.data_lock:
            self.pending_data.extend(data)

    def save_data(self):
        """Commit queued data to the database."""
        with self.data_lock:
            if self.pending_data:
                self.cursor.executemany("INSERT OR REPLACE INTO banned_users (username, time) VALUES (?, ?)", self.pending_data)
                self.pending_data.clear()
                self.conn.commit()
                print("Data committed to DB")

    def _periodic_commit(self):
        """Background task that commits data every interval."""
        while True:
            sleep(self.interval)
            self.save_data()

    def _start_commit_thread(self):
        """Start the background commit thread."""
        commit_thread = Thread(target=self._periodic_commit, daemon=True)
        commit_thread.start()

    def close(self):
        """Ensure data is saved and connection closed properly on exit."""
        print("Closing database and committing any remaining data")
        self.save_data()  # Save one last time
        self.conn.close()

class SleepPrevention:
    def __init__(self):
        """Initialize the command shell to not let the system sleep."""
        self.sleep_proc = None
        self._start_commit_thread()

    def _prevent_sleep(self):
        """Prevent system from sleeping depending on OS."""
        if os_name == "nt":  # Windows
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            while True: self.sleep_proc = windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
        elif os_uname().system == "Darwin":  # macOS
            self.sleep_proc = Popen(["caffeinate"])  # Keeps system awake
        elif os_uname().system == "Linux":  # Linux
            self.sleep_proc = Popen(["systemd-inhibit", "--what=idle", "--who=bot", "--why=Prevent bot sleep", "bash", "-c", "while true; do sleep 60; done"])
        else:
            print("⚠️ Sleep prevention not supported on this OS.")

    def _start_commit_thread(self):
        """Start the background commit thread."""
        commit_thread = Thread(target=self._prevent_sleep, daemon=True)
        commit_thread.start()

    def close(self):
        """Ensure background processes terminate when bot stops."""
        if self.sleep_proc:
            self.sleep_proc.terminate()  # Kill sleep prevention process
            print("💤 Sleep prevention disabled.")

class PuffRetriever:
    def __init__(self, global_var, db_name="puffs.db", interval=10):
        """Initialize the database connection and start the background commit thread."""
        db_path = "assets\\database\\" + db_name if os_name == "nt" else "assets/database/" + db_name
        self.conn = connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.interval = interval
        self.data_lock = Lock()
        self.global_var = global_var

        # Start periodic saving
        self._start_commit_thread()

    def retrieve_data(self):
        """Commit queued data to the database."""
        with self.data_lock:
            if self.global_var:
                keys = [vals for vals in self.global_var[0]]
                # Create a string of question marks, separated by commas
                placeholders = ', '.join(['?'] * len(keys))

                # Now, build your SQL query using this string of placeholders
                sql_query = f"SELECT * FROM puffs WHERE id NOT IN ({placeholders})"
                self.cursor.execute(sql_query, keys)
                self.global_var.extend(self.cursor.fetchall())  # Fetch all new puffs
                print("Data retrieved to DB")

    def _periodic_commit(self):
        """Background task that commits data every interval."""
        while True:
            sleep(self.interval)
            self.retrieve_data()

    def _start_commit_thread(self):
        """Start the background commit thread."""
        commit_thread = Thread(target=self._periodic_commit, daemon=True)
        commit_thread.start()

import os

# Get the current working directory
current_working_directory = os.getcwd()
print(__file__)