# TELTCSERVER - Retro Telnet Chat Server

A lightweight telnet chat server designed with retro computers in mind. Perfect for your Commodore 64, ZX Spectrum, Amiga, or any other vintage computer with telnet capabilities!

Hosted instance: [discus.sh:2323](telnet://discus.sh:2323)

Connect using any telnet client (e.g. `telnet discus.sh 2323` or `atdt discus.sh:2323`)

## Features

- Multi-room chat system
- Works with ASCII-based terminals
- Compatible with vintage computers
- User authentication system
- Room management
- Admin controls
- Rate limiting
- Ban system

## Designed for Retro

TELTCSERVER is specifically designed to work with older computers and terminals. It uses:

- Simple ASCII characters
- 40-column display support
- Minimal bandwidth requirements
- Basic telnet protocol
- No fancy graphics or colors

## Security Notice

This is a fun project for retro computing enthusiasts. Please note:

- Messages are NOT encrypted
- Passwords are hashed but transmitted in plaintext
- No SSL/TLS support
- Intended for hobby use only
- Do not use for sensitive communications

## Getting Started

1. Install Python 3.6 or higher and the dependencies:

```bash
pip install -r requirements.txt
```

2. Run the server:

```bash
python main.py
```

3. Connect using any telnet client
4. Default admin credentials: admin/admin (change these!)

## Commands

Basic commands (available to all, including guests):

- /help - Show available commands
- /login - Log into your account
- /register - Create new account
- /whoami - Show current username
- /quit - Disconnect from server

Authenticated user commands:

- /rooms - List available chat rooms
- /join - Enter a chat room
- /users - List online users
- /broadcast - Send message to all users
- /passwd - Change your password

Admin commands:

- /op - Give admin privileges to user
- /deop - Remove admin privileges from user
- /kick - Disconnect a user from the server
- /ban - Ban a username from the server
- /createroom - Create a new chat room

Note: Admin commands are only available after logging in with admin privileges.
Messages are sent by simply typing without any command prefix.

## Community

This is a hobby project aimed at retro computing enthusiasts. Feel free to:

- Share with other vintage computer fans
- Modify for your needs
- Host for your retro computing group
- Connect using your favorite old machine

## Contributing

Contributions welcome! Keep in mind the project's focus on retro compatibility.

## License

MIT License - See LICENSE file for details

Remember: This is for fun and educational purposes. Enjoy chatting like it's 1985!
