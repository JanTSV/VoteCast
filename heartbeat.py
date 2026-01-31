import time


def send_heartbeat(server):
    if server.left is None or server.left == server.id:
        server.last_heartbeat_time = time.time()
        server.heartbeat_ack_received = True
        return
    server.send(server.left, {"type": "HEARTBEAT", "id": server.id})