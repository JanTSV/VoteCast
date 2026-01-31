# Project Brief

## Overview
VoteCast is a Python-based, multi-client polling platform built on a multi-server architecture. Clients connect to a leader server, create or join poll groups, and run distributed votes. The system uses reliable multicast patterns, leader election, and replicated state across servers.

## Goals
- Provide reliable group creation, membership, and voting across multiple clients.
- Maintain availability via a leader + backup server model with leader election.
- Ensure votes are reliably multicast and results are shared with participants.

## Core Requirements
- Support discovery of servers and leader election (Hirschberg-Sinclair algorithm).
- Provide client registration/authentication tokens.
- Allow creation/join/leave of groups and starting votes per group.
- Reliably multicast vote requests and results to group members.
- Replicate server state to newly elected leaders.

## Scope Notes
- CLI-driven server and client.
- UDP sockets for communication.
- Python runtime with minimal dependencies (click for server CLI).