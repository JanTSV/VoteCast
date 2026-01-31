import socket
import time

from ring import build_ring
from election import hs_start


def discovery_service(server):
    # If this is the first/only server in view at startup, declare self as leader immediately.
    if len(server.servers) <= 1:
        server.leader = server.id
        server.is_leader = True
        server.log(server.color_text(f"HS: Leader elected: {server.leader}", server.COLOR_GREEN))

    while not server.stop_event.is_set():
        try:
            data, addr = server.mcast.recvfrom(1024)
            msg = data.decode()
            if msg.startswith("SERVER:"):
                _, sid = msg.split(":", 1)
                if not sid:
                    continue
                # Always ensure self ID is in the view
                if server.id not in server.servers:
                    server.servers.add(server.id)
                if sid not in server.servers:
                    server.log(server.color_text(f"Server joined: {sid}", server.COLOR_YELLOW))
                    server.servers.add(sid)
                    build_ring(server)
                    # Auto-start HS when we have more than one server and ring is ready; new join triggers election
                    if (
                        not server.election_in_progress
                        and len(server.servers) > 1
                        and server.left is not None
                        and server.right is not None
                    ):
                        hs_start(server)
            elif msg == "WHO_IS_LEADER":
                server.log("Discovery service got leader request")
                if server.is_leader:
                    server.sock.sendto(f"LEADER:{server.id}".encode(), addr)
                    server.log("Replied to leader request")
            elif msg.startswith("CRASH:"):
                # Server left/crashed
                _, sid = msg.split(":", 1)
                # Guard against removing self; ignore if sid is self
                if sid != server.id and sid in server.servers:
                    server.servers.remove(sid)
                    server.log(server.color_text(f"Server left: {sid}", server.COLOR_RED))
                if server.id not in server.servers:
                    server.servers.add(server.id)
                build_ring(server)
        except socket.timeout:
            continue


def discovery_service_broadcast(server, interval=1.0):
    server.log("Starting continuous discovery broadcast thread")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
    msg = f"SERVER:{server.id}".encode()

    while not server.stop_event.is_set():
        # Broadcast for discovery
        try:
            sock.sendto(msg, (server.MCAST_GRP, server.MCAST_PORT))
        except Exception as e:
            server.log(f"Error broadcasting discovery: {e}")

        # Heartbeat
        current_time = time.time()
        if current_time - server.last_heartbeat_time > server.HEARTBEAT_TIMEOUT:
            if server.heartbeat_ack_received:
                server.heartbeat_ack_received = False
                server.log(f"Heartbeat timeout for {server.left}, assuming crash.")
                try:
                    sock.sendto(f"CRASH:{server.left}".encode(), (server.MCAST_GRP, server.MCAST_PORT))
                except Exception as e:
                    server.log(f"Error broadcasting heartbeat discovered crash: {e}")

                time.sleep(2)  # Needed with >1s so that other servers can discover it

                # Start new HS to get a new leader
                hs_start(server)

        server.send_heartbeat()

        time.sleep(interval)

    sock.close()