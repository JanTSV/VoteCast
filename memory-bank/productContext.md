# Product Context

## Why VoteCast Exists
VoteCast provides a distributed polling platform where multiple clients can form groups and reach consensus through votes. It is designed for environments where clients connect to a leader-based server cluster and require reliable dissemination of polls and results.

## Problems It Solves
- Coordinating polls among multiple clients in a distributed system.
- Handling leader election and failover in a multi-server setup.
- Ensuring reliable broadcast of voting events and results.

## How It Should Work
- Servers discover each other and build a logical ring.
- A leader is elected using Hirschberg-Sinclair; only the leader handles client communication.
- Clients register with the leader to obtain an auth token.
- Clients create/join/leave groups and start votes.
- Votes are reliably multicast to group members; results are computed and shared.

## User Experience Goals
- Simple CLI flows for server and client actions.
- Deterministic leader discovery and transparent leader updates.
- Clear visibility into group membership, ongoing votes, and results.