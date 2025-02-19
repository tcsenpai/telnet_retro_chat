def broadcast_message(connections, message, sender_addr=None):
    """
    Broadcasts a message to all connected clients.

    Args:
        connections (dict): Dictionary of active connections {addr: socket}
        message (str): Message to broadcast
        sender_addr (tuple, optional): Address of the sender to exclude
    """
    formatted_message = f"\r\n{message}\r\n"
    encoded_message = formatted_message.encode("ascii")

    for addr, conn in connections.items():
        try:
            # Don't send back to the sender if specified
            if sender_addr and addr == sender_addr:
                continue
            conn.sendall(encoded_message)
        except (ConnectionError, BrokenPipeError):
            print(f"Error sending message to {addr}")
        except:
            # If sending fails, we'll let the main loop handle the disconnection
            pass
