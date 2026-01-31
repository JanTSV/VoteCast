def send_replicate_state(server, new_leader):
    # Ensure all sets are converted to lists before sending
    state = {
        "type": "REPL_STATE",
        "clients": {cid: {"token": client["token"], "addr": client["addr"]} for cid, client in server.clients.items()},
        "groups": {name: {"owner": group["owner"], "members": list(group["members"])} for name, group in server.groups.items()},
        "votes": server.votes,
        "S": server.S,
        "fo_pending": server.fo_pending,
    }
    server.leader_send(new_leader, state)


def replicate_state_apply(server, msg):
    # Convert sets to lists
    server.clients = {cid: {"token": client["token"], "addr": tuple(client["addr"])} for cid, client in msg["clients"].items()}

    server.groups = {name: {
        "owner": group["owner"],
        "members": list(group["members"])
    } for name, group in msg["groups"].items()}

    server.votes = msg["votes"]
    server.S = msg["S"]
    server.fo_pending = msg["fo_pending"]

    # Tell clients that this is the new leader
    tell_clients_about_new_leader(server)


def tell_clients_about_new_leader(server):
    for cid, client in server.clients.items():
        server.leader_send(client["addr"], {"type": "NEW_LEADER", "id": server.id})