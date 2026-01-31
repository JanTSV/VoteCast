# System Patterns

## Architecture Overview
- Multi-server cluster using UDP sockets for communication.
- Servers discover peers via multicast and form a logical ring.
- Hirschberg-Sinclair leader election selects a single leader.
- Leader communicates with clients; followers receive replicated state.

## Key Patterns
- **Leader-based coordination**: Only leader handles client requests and multicasts results.
- **State replication**: Leader replicates state to backups and on leader handoff.
- **Reliable multicast (FO)**: Vote requests are reliably multicast with sequence numbers and pending retransmits.
- **FIFO per-sender ordering**: Clients maintain hold-back queues per sender to process votes in order.
- **Heartbeat detection**: Servers send heartbeat messages to detect crashes.

## Component Relationships
- `server.py` manages discovery, election, client handling, replication, and multicast.
- `client.py` discovers leader, registers, manages groups and voting, and handles vote ordering.
- `config.py` provides multicast configuration and buffer sizing.

## Critical Implementation Paths
- Server discovery → ring build → HS election → leader set.
- Client leader discovery → registration → group management → vote lifecycle.
- FO multicast: leader sends vote → client acks → leader finalizes vote and broadcasts results.