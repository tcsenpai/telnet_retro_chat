import socket
import threading
import os
from dotenv import load_dotenv
from libs.broadcast import broadcast_message
from libs.user_manager import UserManager
from libs.process_message import CommandProcessor
from libs.banner import load_banner
from libs.room_manager import RoomManager

# Load environment variables
load_dotenv()

# Server configuration
HOST = "0.0.0.0"  # Listen on all available network interfaces
PORT = 2323  # Standard Telnet alternative port
MAX_CONNECTIONS = int(
    os.getenv("MAX_CONNECTIONS", "5")
)  # Default to 5 if not specified

# Dictionary to store active connections
active_connections = {}
connections_lock = threading.Lock()  # Thread-safe operations on active_connections

# Initialize user management
user_manager = UserManager()
room_manager = RoomManager()
command_processor = CommandProcessor(user_manager, room_manager)


def handle_backspace(display_buffer, conn):
    """Handle backspace/delete character input."""
    if display_buffer:
        display_buffer = display_buffer[:-1]
        # Send backspace, space, backspace to clear the character
        conn.sendall(b"\x08 \x08")
    return display_buffer


def process_input_byte(byte, display_buffer, conn):
    """Process a single byte of input and handle display."""
    if byte in (127, 8):  # Backspace/delete
        return handle_backspace(display_buffer, conn)

    # Add character to display buffer and echo back
    display_buffer += bytes([byte])
    conn.sendall(bytes([byte]))
    return display_buffer


def process_complete_line(line, addr, active_connections, conn):
    """Process a complete line of input and broadcast if valid."""
    try:
        # Clean up the input by processing backspaces
        cleaned = []
        for char in line:
            if char in (8, 127):  # Backspace/delete
                if cleaned:
                    cleaned.pop()
            else:
                cleaned.append(char)

        message = bytes(cleaned).decode("ascii", "ignore").strip()
        print(f"Client {addr}: {message}")

        # Process commands
        if message.startswith("/"):
            response = command_processor.process_command(message[1:], addr)

            # Handle special responses
            if response.startswith("@KICK@"):
                _, kick_addr = response.split("@", 2)
                # Convert string addr back to tuple
                kick_addr = eval(kick_addr)  # Safe here as we control the input
                if kick_addr in active_connections:
                    active_connections[kick_addr].sendall(
                        b"\r\nYou have been kicked from the server.\r\n"
                    )
                    active_connections[kick_addr].close()
                return

            if response.startswith("@BROADCAST@"):
                parts = response.split("@", 2)  # Split into max 3 parts
                broadcast_msg = parts[2] if len(parts) > 2 else ""
                username = user_manager.get_username(addr)
                broadcast_message(
                    active_connections, f"[BROADCAST] {username}: {broadcast_msg}"
                )
                return

            conn.sendall(f"\r\n{response}\r\n".encode("ascii"))
        else:
            # Regular chat message
            username = user_manager.get_username(addr)

            # Check if user is authenticated (not a guest)
            if username.startswith("guest_"):
                conn.sendall(
                    b"\r\nYou must be logged in to chat. Use /help for commands.\r\n"
                )
                return

            # Check rate limit
            if user_manager.is_rate_limited(addr):
                conn.sendall(b"\r\nRate limit exceeded. Please wait a moment.\r\n")
                return

            # Broadcast the message
            current_room = room_manager.get_user_room(addr)
            room = room_manager.rooms[current_room]
            message_with_user = f"[{username}@{current_room}]: {message}"

            # Send to room members
            broadcast_message(
                active_connections,
                message_with_user,
                addr,
                room,
            )
            # Send back to sender
            conn.sendall(f"\r\n{message_with_user}\r\n".encode("ascii"))
    except UnicodeDecodeError:
        print("UnicodeDecodeError: ", line)


def handle_client(conn, addr):
    """
    Handles individual client connections.

    Args:
        conn (socket): Client socket connection
        addr (tuple): Client address information
    """
    print(f"Connected by {addr}")

    # Register as guest initially
    username = user_manager.register_session(addr)
    room_manager.join_room(addr, "lounge")  # Put user in default room

    # Check if username is banned
    if user_manager.is_banned(username):
        conn.sendall(b"You are banned from this server.\r\n")
        conn.close()
        return

    with connections_lock:
        active_connections[addr] = conn

    # Send banner and welcome message
    banner = load_banner()
    welcome_msg = (
        f"\r\n{banner}\r\n"
        f"You are connected as: {username}\r\n"
        "Type '/help' for available commands.\r\n"
    )
    conn.sendall(welcome_msg.encode("ascii"))
    broadcast_message(
        active_connections,
        f"* New user connected from {addr[0]} as {username}",
        addr,
        system_msg=True,
    )

    # Initialize buffers
    input_buffer = b""
    display_buffer = b""

    try:
        while True:
            # Receive data from client
            data = conn.recv(1024)
            if not data:
                break

            # Process each byte for display
            for byte in data:
                display_buffer = process_input_byte(byte, display_buffer, conn)

            # Handle complete lines
            input_buffer += data
            if b"\r" in input_buffer:
                # Split into complete line and remaining buffer
                line, *remaining = input_buffer.split(b"\r", 1)
                input_buffer = remaining[0] if remaining else b""
                display_buffer = b""

                # Remove trailing LF if present
                if input_buffer.startswith(b"\n"):
                    input_buffer = input_buffer[1:]

                process_complete_line(line, addr, active_connections, conn)

    finally:
        # Clean up disconnected client
        cleanup_client_connection(addr)


def cleanup_client_connection(addr):
    """Clean up resources when a client disconnects."""
    print(f"Client {addr} disconnected")
    username = user_manager.get_username(addr)
    room_manager.leave_current_room(addr)
    with connections_lock:
        del active_connections[addr]
    broadcast_message(
        active_connections, f"* User {username} disconnected", system_msg=True
    )


def start_server():
    """
    Starts the server and listens for incoming connections.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen(MAX_CONNECTIONS)
        print(f"Listening on port {PORT}...")
        print(f"Maximum connections allowed: {MAX_CONNECTIONS}")

        while True:
            # Accept new connection
            conn, addr = server.accept()

            # Check if maximum connections reached
            if len(active_connections) >= MAX_CONNECTIONS:
                conn.sendall(b"Server is full. Please try again later.\r\n")
                conn.close()
                continue

            # Create a new thread for each client
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True  # Thread will close when main program exits
            client_thread.start()


if __name__ == "__main__":
    start_server()
