import json
import os
import random
import string
from pathlib import Path
import time
import hashlib


class UserManager:
    def __init__(self):
        self.users = {}  # {username: {'password': hash, 'role': role}}
        self.active_sessions = {}  # {addr: username}
        self.users_file = Path("data/users.json")
        self.message_timestamps = {}  # {addr: [timestamps]}
        self.banned_users = set()  # Store banned usernames
        self._load_users()

    def _hash_password(self, password):
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _load_users(self):
        """Load users from JSON file."""
        if self.users_file.exists():
            with open(self.users_file) as f:
                self.users = json.load(f)
                # Convert any plain text passwords to hashed
                needs_update = False
                for username, data in self.users.items():
                    if len(data["password"]) != 64:  # Not a SHA-256 hash
                        data["password"] = self._hash_password(data["password"])
                        needs_update = True
                if needs_update:
                    self._save_users()
        else:
            # Create default admin user if no users exist
            self.users_file.parent.mkdir(exist_ok=True)
            default_password = self._hash_password("admin")  # Hash the default password
            self.users = {
                "admin": {
                    "password": default_password,
                    "role": "admin",
                }
            }
            self._save_users()

    def _save_users(self):
        """Save users to JSON file."""
        with open(self.users_file, "w") as f:
            json.dump(self.users, f, indent=2)

    def generate_guest_name(self):
        """Generate a random guest username."""
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
        return f"guest_{suffix}"

    def authenticate(self, username, password):
        """Check if username and password match."""
        if username in self.users:
            hashed_password = self._hash_password(password)
            return self.users[username]["password"] == hashed_password
        return False

    def register_session(self, addr, username=None):
        """Register a new session for an address."""
        if not username:
            username = self.generate_guest_name()
        self.active_sessions[addr] = username
        return username

    def get_username(self, addr):
        """Get username for an address."""
        return self.active_sessions.get(addr)

    def remove_session(self, addr):
        """Remove a session."""
        if addr in self.active_sessions:
            del self.active_sessions[addr]

    def add_user(self, username, password, role="user"):
        """Add a new user."""
        if username not in self.users:
            self.users[username] = {
                "password": self._hash_password(password),
                "role": role,
            }
            self._save_users()
            return True
        return False

    def is_admin(self, addr):
        """Check if user is admin."""
        username = self.get_username(addr)
        return username in self.users and self.users[username]["role"] == "admin"

    def is_rate_limited(self, addr):
        """Check if user is rate limited (2 messages per second)."""
        if self.is_admin(addr):
            return False

        now = time.time()
        timestamps = self.message_timestamps.setdefault(addr, [])

        # Remove timestamps older than 1 second
        timestamps = [t for t in timestamps if now - t < 1]
        self.message_timestamps[addr] = timestamps

        # Check if more than 2 messages in the last second
        if len(timestamps) >= 2:
            return True

        timestamps.append(now)
        return False

    def ban_user(self, username):
        """Ban a username."""
        self.banned_users.add(username.lower())

    def unban_user(self, username):
        """Unban a username."""
        self.banned_users.discard(username.lower())

    def is_banned(self, username):
        """Check if username is banned."""
        return username.lower() in self.banned_users

    def change_password(self, username, new_password):
        """Change a user's password."""
        if username in self.users:
            self.users[username]["password"] = self._hash_password(new_password)
            self._save_users()
            return True
        return False
