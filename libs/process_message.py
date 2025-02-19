from typing import Tuple


class CommandProcessor:
    def __init__(self, user_manager):
        self.user_manager = user_manager
        self.commands = {
            "help": self.cmd_help,
            "login": self.cmd_login,
            "register": self.cmd_register,
            "whoami": self.cmd_whoami,
            "users": self.cmd_users,
            "op": self.cmd_op,
            "deop": self.cmd_deop,
            "kick": self.cmd_kick,
            "ban": self.cmd_ban,
            "broadcast": self.cmd_broadcast,
            "passwd": self.cmd_passwd,
        }

    def process_command(self, message: str, addr: Tuple) -> str:
        """Process a command and return the response."""
        parts = message.strip().split()
        if not parts:
            return ""

        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in self.commands:
            return self.commands[cmd](args, addr)
        return f"Unknown command: {cmd}. Type 'help' for available commands."

    def cmd_help(self, args, addr):
        """Show available commands based on user's role."""
        is_admin = self.user_manager.is_admin(addr)
        is_authenticated = not self.user_manager.get_username(addr).startswith("guest_")

        # Commands for all users (including guests)
        guest_commands = {
            "help": "Show this help message",
            "login": "Login with username and password",
            "whoami": "Show current username",
            "register": "Register new user",
        }

        # Commands for authenticated users
        auth_commands = {
            "broadcast": "Broadcast a message to all users",
            "users": "List online users",
        }

        # Admin commands
        admin_commands = {
            "op": "Give admin privileges to user",
            "deop": "Remove admin privileges from user",
            "kick": "Disconnect a user from the server",
            "ban": "Ban a username from the server",
        }

        # Build help message
        help_msg = [
            "+-------------COMMANDS-------------+",
            "#  Basic Commands:                #",
        ]

        # Add guest commands
        for cmd, desc in guest_commands.items():
            help_msg.append(f"# /{cmd:<10} - {desc:<15} #")

        # Add authenticated user commands
        if is_authenticated:
            help_msg.append("#                                #")
            help_msg.append("#  User Commands:                #")
            for cmd, desc in auth_commands.items():
                help_msg.append(f"# /{cmd:<10} - {desc:<15} #")

        # Add admin commands
        if is_admin:
            help_msg.append("#                                #")
            help_msg.append("#  Admin Commands:               #")
            for cmd, desc in admin_commands.items():
                help_msg.append(f"# /{cmd:<10} - {desc:<15} #")

        help_msg.append("+--------------------------------+")
        return "\n".join(help_msg)

    def cmd_login(self, args, addr):
        """Handle login command."""
        if len(args) != 2:
            return "Usage: login <username> <password>"

        username, password = args
        if self.user_manager.authenticate(username, password):
            self.user_manager.register_session(addr, username)
            self.user_manager.message_timestamps[addr] = []  # Reset rate limit
            return f"Successfully logged in as {username}"
        return "Invalid username or password"

    def cmd_register(self, args, addr):
        """Handle register command."""
        if len(args) != 2:
            return "Usage: register <username> <password>"

        username, password = args
        if self.user_manager.add_user(username, password):
            return f"User {username} registered successfully"
        return "Username already exists"

    def cmd_whoami(self, args, addr):
        """Show current username."""
        username = self.user_manager.get_username(addr)
        return f"You are: {username}"

    def cmd_users(self, args, addr):
        """List online users."""
        # Check if user is authenticated (not a guest)
        username = self.user_manager.get_username(addr)
        if username.startswith("guest_"):
            return "You must be logged in to list users"

        users = [
            f"{addr}: {user}"
            for addr, user in self.user_manager.active_sessions.items()
        ]
        return "Online users:\n" + "\n".join(users)

    def cmd_op(self, args, addr):
        """Make a user admin."""
        if not self.user_manager.is_admin(addr):
            return "You don't have permission to use this command"
        if len(args) != 1:
            return "Usage: op <username>"
        username = args[0]
        if username in self.user_manager.users:
            self.user_manager.users[username]["role"] = "admin"
            self.user_manager._save_users()
            return f"User {username} is now an admin"
        return "User not found"

    def cmd_deop(self, args, addr):
        """Remove admin status from user."""
        if not self.user_manager.is_admin(addr):
            return "You don't have permission to use this command"
        if len(args) != 1:
            return "Usage: deop <username>"
        username = args[0]
        if username in self.user_manager.users:
            self.user_manager.users[username]["role"] = "user"
            self.user_manager._save_users()
            return f"User {username} is no longer an admin"
        return "User not found"

    def cmd_kick(self, args, addr):
        """Kick a user from the server."""
        if not self.user_manager.is_admin(addr):
            return "You don't have permission to use this command"
        if len(args) != 1:
            return "Usage: kick <username>"
        username = args[0]

        # Check if target is admin
        for client_addr, client_name in self.user_manager.active_sessions.items():
            if client_name == username:
                if (
                    username in self.user_manager.users
                    and self.user_manager.users[username]["role"] == "admin"
                ):
                    return "Cannot kick an admin"
                return f"@KICK@{client_addr}"
        return "User not found or not online"

    def cmd_ban(self, args, addr):
        """Ban a username."""
        if not self.user_manager.is_admin(addr):
            return "You don't have permission to use this command"
        if len(args) != 1:
            return "Usage: ban <username>"
        username = args[0]
        if (
            username in self.user_manager.users
            and self.user_manager.users[username]["role"] == "admin"
        ):
            return "Cannot ban an admin"
        self.user_manager.ban_user(username)
        return f"User {username} has been banned"

    def cmd_broadcast(self, args, addr):
        """Broadcast a message to all users."""
        if not args:
            return "Usage: broadcast <message>"

        # Check if user is authenticated (not a guest)
        username = self.user_manager.get_username(addr)
        if username.startswith("guest_"):
            return "You must be logged in to broadcast messages"

        if self.user_manager.is_rate_limited(addr):
            return "Rate limit exceeded. Please wait a moment."

        return f"@BROADCAST@{' '.join(args)}"

    def cmd_passwd(self, args, addr):
        """Change password for current user."""
        if len(args) != 2:
            return "Usage: passwd <old_password> <new_password>"

        old_password, new_password = args
        username = self.user_manager.get_username(addr)

        if username.startswith("guest_"):
            return "You must be logged in to change password"

        if not self.user_manager.authenticate(username, old_password):
            return "Current password is incorrect"

        if self.user_manager.change_password(username, new_password):
            return "Password changed successfully"
        return "Failed to change password"
