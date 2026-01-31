# Active Context

## Current Focus
- Stabilize multi-server discovery and leader-election demos for exam readiness.

## Recent Changes
- Added `SO_REUSEPORT` in `server.py` discovery socket to allow multiple servers to bind multicast port on macOS.
- Added yellow ANSI highlight for the discovery log line when a new server is found.
- Attempted automated 5-server launch; observed ring-build crash when a server builds a ring without its own ID in the list.

## Next Steps
- Investigate and resolve ring-build crash (`ValueError: <id> is not in list`) during rapid multi-server startup.
- Provide manual test checklist and expected logs for leader election and crash scenarios if needed.

## Decisions & Considerations
- Limit changes to non-logic fixes and observability improvements unless explicitly approved.
- Use CLI-driven manual testing for leader election and crash scenarios when automated inputs are impractical.

## Learnings
- macOS requires `SO_REUSEPORT` to allow multiple UDP sockets to bind the same multicast port.
- Rapid parallel startup can expose ring-build assumptions if a server hasn’t yet seen its own ID in discovery.