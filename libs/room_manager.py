from pathlib import Path
import json


class Room:
    def __init__(self, name, description=""):
        self.name = name
        self.description = description
        self.users = set()  # Set of addr tuples

    def add_user(self, addr):
        self.users.add(addr)

    def remove_user(self, addr):
        self.users.discard(addr)


class RoomManager:
    def __init__(self):
        self.rooms = {}  # {name: Room}
        self.user_rooms = {}  # {addr: room_name}
        self.rooms_file = Path("data/rooms.json")
        self._load_rooms()

    def _load_rooms(self):
        if self.rooms_file.exists():
            with open(self.rooms_file) as f:
                rooms_data = json.load(f)
                for name, data in rooms_data.items():
                    self.rooms[name] = Room(name, data.get("description", ""))
        else:
            # Create default lounge
            self.rooms_file.parent.mkdir(exist_ok=True)
            self.rooms["lounge"] = Room("lounge", "The default chat room")
            self._save_rooms()

    def _save_rooms(self):
        rooms_data = {
            name: {"description": room.description} for name, room in self.rooms.items()
        }
        with open(self.rooms_file, "w") as f:
            json.dump(rooms_data, f, indent=2)

    def create_room(self, name, description=""):
        if name.lower() in self.rooms:
            return False
        self.rooms[name.lower()] = Room(name, description)
        self._save_rooms()
        return True

    def join_room(self, addr, room_name):
        """Join a chat room."""
        room_name = room_name.lower()
        if room_name not in self.rooms:
            return False

        # Get old room for notification
        old_room = None
        if addr in self.user_rooms:
            old_room_name = self.user_rooms[addr]
            old_room = self.rooms[old_room_name]

        # Remove from current room
        self.leave_current_room(addr)

        # Add to new room
        self.rooms[room_name].add_user(addr)
        self.user_rooms[addr] = room_name

        return True

    def leave_current_room(self, addr):
        if addr in self.user_rooms:
            current_room = self.rooms[self.user_rooms[addr]]
            current_room.remove_user(addr)
            del self.user_rooms[addr]

    def get_room_users(self, room_name):
        room = self.rooms.get(room_name.lower())
        return room.users if room else set()

    def get_user_room(self, addr):
        return self.user_rooms.get(addr, "lounge")

    def list_rooms(self):
        return {name: room.description for name, room in self.rooms.items()}
