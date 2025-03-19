from sqlite3 import connect
from os import name as os_name
from time import sleep
from threading import Thread, Lock
from atexit import register

class Banned_Users_Handler:
    def __init__(self, db_name="users.db", interval=1800):
        """Initialize the database connection and start the background commit thread."""
        db_path = "assets\\database\\" + db_name if os_name == "nt" else "assets/database/" + db_name
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