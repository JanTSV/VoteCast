import time
from collections import defaultdict


def fo_multicast(server, group, payload, timeout):
    """
    FO-multicast(g, m):
    - piggyback S_pg
    - increment S_pg
    - B-multicast
    """
    seq = server.S[group]

    msg = {
        "S": seq,
        "sender": server.id,
        **payload
    }

    pending = set(server.groups[group]["members"])

    # Buffer pending requests
    server.fo_pending[(group, seq)] = {
        "pending": set(server.groups[group]["members"]),
        "deadline": time.time() + timeout,
        "msg": msg,
        "vote_id": payload.get("vote_id")
    }

    # Increment S_pg
    server.S[group] += 1

    # B-multicast
    for cid in pending:
        server.leader_send(server.clients[cid]["addr"], msg)


def fo_retransmit_loop(server):
    while not server.stop_event.is_set():
        now = time.time()
        finished = []

        for key, entry in list(server.fo_pending.items()):
            group, seq = key

            if now > entry["deadline"] or not entry["pending"]:
                finished.append(key)
                continue

            for cid in entry["pending"]:
                server.leader_send(server.clients[cid]["addr"], entry["msg"])

        for key in finished:
            group, seq = key
            entry = server.fo_pending.pop(key)

            vote_id = entry.get("vote_id")
            if vote_id:
                finalize_vote(server, vote_id)

            server.log(f"FO multicast completed: {group}, seq={seq}")

        time.sleep(0.5)


def finalize_vote(server, vote_id):
    server.log(f"Finalizing vote {vote_id}")

    vote = server.votes.get(vote_id)
    if not vote:
        server.log(f"Vote {vote_id} not found")
        return

    # Select winner with tie-breaking
    winner = "No votes, no winner"
    if len(vote["votes"]) > 0:
        vote_counts = defaultdict(int)
        for vote_entry in vote["votes"]:
            vote_counts[vote_entry["vote"]] += 1

        # Find all options with maximum votes
        max_votes = max(vote_counts.values())
        winners = [option for option, count in vote_counts.items() if count == max_votes]

        # Tie-breaking: select the option that appears first in the original options list
        if len(winners) > 1:
            # Find which winner appears first in original options
            winner = min(winners, key=lambda x: vote["options"].index(x))
            server.log(f"Tie detected between {winners}, breaking tie by list order: {winner}")
        else:
            winner = winners[0]

    # Announce the result via group multicast
    result_msg = {
        "type": "VOTE_RESULT",
        "vote_id": vote_id,
        "group": vote["group"],
        "topic": vote["topic"],
        "winner": winner
    }

    for cid in server.groups[vote["group"]]["members"]:
        server.leader_send(server.clients[cid]["addr"], result_msg)
