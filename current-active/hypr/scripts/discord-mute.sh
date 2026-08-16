#!/bin/bash
# Toggle Mute via Discord IPC
python3 -c "
import socket, json, struct, os, glob

# Find the discord-ipc socket (can be multiple)
sockets = glob.glob(f'/run/user/{os.getuid()}/discord-ipc-*')
if not sockets:
    exit(1)

for SOCKET in sockets:
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(SOCKET)

        # Handshake
        handshake = json.dumps({'v': 1, 'client_id': '0'})
        sock.send(struct.pack('<II', 0, len(handshake)) + handshake.encode())
        sock.recv(1024)

        # Toggle Mute
        cmd = json.dumps({'cmd': 'SET_VOICE_SETTINGS', 'args': {'mute': True}, 'nonce': '1'})
        # Note: True/False toggle is hard via simple IPC, so we just toggle the state
        # Better: use a script that reads the state, but simple toggle is usually enough.
        # However, Vesktop/Vencord supports TOGGLE_MUTE in some versions:
        cmd_toggle = json.dumps({'cmd': 'TOGGLE_MUTE', 'args': {}, 'nonce': '1'})
        sock.send(struct.pack('<II', 1, len(cmd_toggle)) + cmd_toggle.encode())
        sock.close()
    except:
        continue
"
