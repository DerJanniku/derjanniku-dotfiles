#!/bin/bash
# Toggle Deafen via Discord IPC
python3 -c "
import socket, json, struct, os, glob

sockets = glob.glob(f'/run/user/{os.getuid()}/discord-ipc-*')
if not sockets:
    exit(1)

for SOCKET in sockets:
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(SOCKET)

        handshake = json.dumps({'v': 1, 'client_id': '0'})
        sock.send(struct.pack('<II', 0, len(handshake)) + handshake.encode())
        sock.recv(1024)

        # Toggle Deafen
        cmd = json.dumps({'cmd': 'TOGGLE_SELF_DEAFEN', 'args': {}, 'nonce': '1'})
        sock.send(struct.pack('<II', 1, len(cmd)) + cmd.encode())
        sock.close()
    except:
        continue
"
