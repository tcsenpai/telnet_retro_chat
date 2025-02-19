def broadcast_message(
    connections, message, sender_addr=None, room=None, system_msg=False
):
    """Broadcasts a message to all users in a room or system-wide."""
    formatted_message = f"\r\n{message}\r\n"
    encoded_message = formatted_message.encode("ascii")

    # Get recipients based on room, unless it's a system message
    recipients = (
        connections.keys()
        if system_msg
        else (room.users if room else connections.keys())
    )

    # Always show to console
    print(formatted_message)

    # Send to other recipients
    for addr in recipients:
        if addr not in connections or addr == ("console", 0):
            continue
        try:
            if sender_addr and addr == sender_addr:
                continue
            connections[addr].sendall(encoded_message)
        except (ConnectionError, BrokenPipeError):
            print(f"Error sending message to {addr}")
        except:
            # If sending fails, we'll let the main loop handle the disconnection
            pass
