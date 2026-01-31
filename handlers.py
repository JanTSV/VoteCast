import time
import uuid
import secrets

from fo_multicast import fo_multicast


def register(server, msg, addr):
    cid = msg.get("id")
    if cid is None:
        server.log(f"Error: Expected key 'id': {msg}")
        return

    token = secrets.token_hex(16)
    server.clients[cid] = {
        "token": token,
        "addr": addr
    }

    if server.is_leader:
        for s in server.servers:
            if s != server.id:
                server.leader_send(s, {
                    "type": "REPL_REGISTER",
                    "id": cid,
                    "token": token,
                    "addr": addr
                })

    server.leader_send(addr, {"type": "REGISTER_OK", "token": token})


def create_group(server, msg, addr):
    cid = msg.get("id")
    name = msg.get("group")

    if cid is None or name is None:
        server.log(f"Error: Expected keys 'id'/'group': {msg}")
        return

    if name in server.groups:
        server.log(f"Error: Group already exists: {name}")
        return

    server.groups[name] = {
        "owner": cid,
        "members": {cid}
    }
    server.S[name] = 0
    server.leader_send(addr, {"type": "CREATE_GROUP_OK", "group": name})


def get_groups(server, msg, addr):
    groups = [g for g in server.groups.keys()]
    server.leader_send(addr, {"type": "GET_GROUPS_OK", "groups": groups})


def join_group(server, msg, addr):
    cid = msg.get("id")
    name = msg.get("group")
    if cid is None or name is None:
        server.log(f"Error: Expected keys 'id'/'group': {msg}")
        return
    if name not in server.groups:
        server.log(f"Error: Group does not exist: {name}")
        return
    server.groups[name]["members"].add(cid)
    server.leader_send(addr, {"type": "JOIN_GROUP_OK", "group": name})


def joined_groups(server, msg, addr):
    cid = msg.get("id")
    if cid is None:
        server.log(f"Error: Expected key 'id': {msg}")
        return
    groups = [g for g in server.groups.keys() if cid in server.groups[g]["members"]]
    server.leader_send(addr, {"type": "JOINED_GROUPS_OK", "groups": groups})


def leave_group(server, msg, addr):
    cid = msg.get("id")
    name = msg.get("group")
    if cid is None or name is None:
        server.log(f"Error: Expected keys 'id'/'group': {msg}")
        return
    if name not in server.groups:
        server.log(f"Error: Group does not exist: {name}")
        return
    if cid not in server.groups[name]["members"]:
        server.log(f"Error: Not a member in group {name}")
        return
    server.groups[name]["members"].remove(cid)
    server.leader_send(addr, {"type": "LEAVE_GROUP_OK", "group": name})


def start_vote(server, msg, addr):
    cid = msg.get("id")
    name = msg.get("group")
    topic = msg.get("topic")
    options = msg.get("options")
    timeout = msg.get("timeout")

    if cid is None or name is None or topic is None or options is None or timeout is None:
        server.log(f"Error: Missing required fields in START_VOTE: {msg}")
        return
    if name not in server.groups:
        server.log(f"Error: Group does not exist: {name}")
        return
    if cid not in server.groups[name]["members"]:
        server.log(f"Error: Not a member in group {name}")
        return

    server.leader_send(addr, {"type": "START_VOTE_OK", "group": name, "topic": topic, "options": options, "timeout": timeout})

    vote_id = str(uuid.uuid4())
    server.votes[vote_id] = {
        "group": name,
        "topic": topic,
        "options": options,
        "votes": []
    }

    if server.is_leader:
        for s in server.servers:
            if s != server.id:
                server.leader_send(s, {
                    "type": "REPL_VOTE",
                    "vote_id": vote_id,
                    "group": name,
                    "topic": topic,
                    "options": options,
                    "timeout": timeout,
                    "votes": []
                })

    payload = {
        "type": "VOTE",
        "vote_id": vote_id,
        "group": name,
        "topic": topic,
        "options": options
    }
    fo_multicast(server, name, payload, timeout)


def vote_ack(server, msg, addr):
    vote_id = msg.get("vote_id")
    group = msg.get("group")
    sender_seq = msg.get("S")

    if not vote_id or not group or sender_seq is None:
        server.log(f"Error in VOTE_ACK: Missing vote_id, group, or S")
        return

    fo_entry = server.fo_pending.get((group, sender_seq))
    if not fo_entry:
        server.log(f"Out-of-order or unknown VOTE_ACK for {group}, seq={sender_seq}")
        return

    sender_id = msg.get("id")
    if sender_id in fo_entry["pending"]:
        fo_entry["pending"].remove(sender_id)

    # Server-side duplicate vote prevention
    if vote_id not in server.client_votes:
        server.client_votes[vote_id] = {}

    if sender_id in server.client_votes[vote_id]:
        server.log(f"Duplicate vote detected from {sender_id} for vote {vote_id}, ignoring")
        return

    # Server-side vote validation
    vote = msg.get("vote")
    if not vote:
        server.log(f"Invalid vote: missing vote field from {sender_id} for vote {vote_id}")
        return

    # Validate vote is in the options list
    if vote not in server.votes[vote_id]["options"]:
        server.log(f"Invalid vote option: {vote} from {sender_id} for vote {vote_id}")
        return

    # Record this client's vote
    server.client_votes[vote_id][sender_id] = msg

    server.votes[vote_id]["votes"].append(msg)
    server.log(f"Vote Acknowledged: {msg}")
