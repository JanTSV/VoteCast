import socket
import json
import uuid
import sys
import time


class Client:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.server = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(2)

    def discover_leader(self):
        msg = {"type": "WHO_IS_LEADER"}
        self.sock.sendto(json.dumps(msg).encode(), self.server)

        try:
            data, _ = self.sock.recvfrom(1024)
            reply = json.loads(data.decode())
            return reply.get("leader")
        except socket.timeout:
            return None

    def set_server(self, server):
        self.server = server

    def send_request(self, payload):
        msg = {
            "type": "CLIENT_REQUEST",
            "payload": payload
        }
        self.sock.sendto(json.dumps(msg).encode(), self.server)

    def create_group(self, group):
        self.send_request({"type": "CREATE_GROUP", "group": group})

    def join_group(self, group):
        self.send_request({
            "type": "JOIN_GROUP",
            "group": group,
            "client": self.id
        })

    def vote(self, poll, vote):
        self.send_request({
            "type": "VOTE",
            "poll": poll,
            "client": self.id,
            "vote": vote
        })


if __name__ == "__main__":
    client = Client()

    leader = None
    while leader is None:
        leader = client.discover_leader()
        print("Discovering leader...")
        time.sleep(1)

    print("Leader is:", leader)
