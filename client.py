import socket
import json
import uuid
import sys
import time

class Client:
    def __init__(self, server):
        self.id = str(uuid.uuid4())
        self.server = server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def create_group(self, group):
        self.send({"type": "CREATE_GROUP", "group": group})

    def join_group(self, group):
        self.send({"type": "JOIN_GROUP", "group": group, "client": self.id})

    def vote(self, poll, vote):
        self.send({
            "type": "VOTE",
            "poll": poll,
            "client": self.id,
            "vote": vote
        })

    def send(self, payload):
        self.sock.sendto(json.dumps({
            "type": "MC",
            "payload": payload
        }).encode(), self.server)


if __name__ == "__main__":
    ip = sys.argv[1]
    port = int(sys.argv[2])
    c = Client((ip, port))
    c.create_group("group1")
    time.sleep(1)
    c.join_group("group1")
    c.vote("poll1", "A")
