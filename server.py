import socket
import threading
import json
import time
import sys
import uuid
import signal

MCAST_GRP = "224.1.1.1"
MCAST_PORT = 5007
BUF = 4096
HS_TIMEOUT = 2


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


class Server:
    def __init__(self, port):
        self.ip = get_local_ip()
        self.port = port
        self.id = f"{self.ip}:{self.port}"

        # Shutdown control
        self.stop_event = threading.Event()

        # Membership
        self.servers = set([self.id])
        self.ring = []
        self.left = None
        self.right = None

        # Leader
        self.is_leader = False
        self.leader = None

        # Poll groups
        self.groups = {}
        self.polls = {}
        self.votes = {}

        # FIFO multicast
        self.S_p = 0
        self.R_q = {}
        self.holdback = {}
        self.sent = {}

        # EiG
        self.eig_msgs = {}

        # Networking
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip, self.port))
        self.sock.settimeout(1.0)

        self.mcast = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        self.mcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.mcast.bind(("", MCAST_PORT))
        self.mcast.settimeout(1.0)

        mreq = socket.inet_aton(MCAST_GRP) + socket.inet_aton("0.0.0.0")
        self.mcast.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        # Signal handling (SIGINT, SIGTERM)
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, signum, frame):
        print(f"\n[{self.id}] shutting down (signal {signum})")
        self.stop_event.set()

    def discovery_listener(self):
        while not self.stop_event.is_set():
            try:
                data, _ = self.mcast.recvfrom(1024)
            except socket.timeout:
                continue
            except OSError:
                break

            msg = data.decode()
            if msg.startswith("SERVER"):
                print(msg)
                _, sid = msg.split(":", 1)
                self.servers.add(sid)
                self.R_q.setdefault(sid, 0)

    def announce(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.sendto(f"SERVER:{self.id}".encode(), (MCAST_GRP, MCAST_PORT))
        s.close()

    def form_ring(self):
        self.ring = sorted(self.servers)
        i = self.ring.index(self.id)
        self.left = self.ring[(i + 1) % len(self.ring)]
        self.right = self.ring[(i - 1) % len(self.ring)]

    def start_hs(self):
        msg = {
            "type": "HS",
            "origin": self.id,
            "candidate": self.id,
            "hop": 1
        }
        self.send_to(self.right, msg)

    def handle_hs(self, msg):
        cand = msg["candidate"]

        if cand > self.id:
            msg["hop"] -= 1
            if msg["hop"] > 0:
                self.send_to(self.right, msg)
        elif cand < self.id:
            self.send_to(self.right, {
                "type": "HS",
                "origin": self.id,
                "candidate": self.id,
                "hop": msg["hop"]
            })
        else:
            self.leader = self.id
            self.is_leader = True
            self.multicast({"type": "LEADER", "leader": self.id})

    def multicast(self, payload):
        self.S_p += 1
        msg = {
            "type": "MC",
            "sender": self.id,
            "seq": self.S_p,
            "ack": self.R_q,
            "payload": payload
        }
        self.sent[self.S_p] = msg
        for s in self.servers:
            ip, port = s.split(":")
            self.sock.sendto(json.dumps(msg).encode(), (ip, int(port)))

    def handle_mc(self, msg):
        sender, seq = msg["sender"], msg["seq"]
        self.R_q.setdefault(sender, 0)
        self.holdback.setdefault(sender, {})

        if seq == self.R_q[sender] + 1:
            self.deliver(msg)
            self.R_q[sender] += 1
            while self.R_q[sender] + 1 in self.holdback[sender]:
                m = self.holdback[sender].pop(self.R_q[sender] + 1)
                self.deliver(m)
                self.R_q[sender] += 1
        elif seq > self.R_q[sender] + 1:
            self.holdback[sender][seq] = msg
            self.send_nack(sender)

    def send_nack(self, sender):
        ip, port = sender.split(":")
        nack = {"type": "NACK", "expect": self.R_q[sender] + 1}
        self.sock.sendto(json.dumps(nack).encode(), (ip, int(port)))

    def deliver(self, msg):
        p = msg["payload"]

        if p["type"] == "CREATE_GROUP":
            self.groups.setdefault(p["group"], set())

        if p["type"] == "JOIN_GROUP":
            self.groups.setdefault(p["group"], set()).add(p["client"])

        if p["type"] == "VOTE":
            poll = p["poll"]
            self.votes.setdefault(poll, {})
            if p["client"] not in self.votes[poll]:
                self.votes[poll][p["client"]] = p["vote"]

        if p["type"] == "LEADER":
            self.leader = p["leader"]
            self.is_leader = (self.leader == self.id)

    def eig(self, poll):
        local = self.aggregate(poll)
        self.multicast({"type": "EIG", "poll": poll, "value": local})
        time.sleep(2)
        values = [local] + self.eig_msgs.get(poll, [])
        return max(sorted(values), key=values.count)

    def aggregate(self, poll):
        c = {}
        for v in self.votes.get(poll, {}).values():
            c[v] = c.get(v, 0) + 1
        return max(sorted(c), key=c.get)

    def send_to(self, target, msg):
        ip, port = target.split(":")
        self.sock.sendto(json.dumps(msg).encode(), (ip, int(port)))

    def run(self):
        threading.Thread(
            target=self.discovery_listener,
            daemon=True
        ).start()

        time.sleep(1)
        self.announce()
        time.sleep(2)
        self.form_ring()
        self.start_hs()

        print(f"[{self.id}] running (Ctrl+C to stop)")

        try:
            while not self.stop_event.is_set():
                try:
                    data, _ = self.sock.recvfrom(BUF)
                except socket.timeout:
                    continue
                except OSError:
                    break

                msg = json.loads(data.decode())

                if msg["type"] == "HS":
                    self.handle_hs(msg)
                elif msg["type"] == "MC":
                    if msg["payload"]["type"] == "EIG":
                        self.eig_msgs.setdefault(
                            msg["payload"]["poll"], []
                        ).append(msg["payload"]["value"])
                    self.handle_mc(msg)

        finally:
            self.sock.close()
            self.mcast.close()
            print(f"[{self.id}] stopped cleanly")


if __name__ == "__main__":
    port = int(sys.argv[1])
    Server(port).run()
