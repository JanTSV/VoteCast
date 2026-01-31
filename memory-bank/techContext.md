# Tech Context

## Technologies Used
- Python 3
- UDP sockets for communication
- Multicast networking for discovery and leader queries
- `click` for server CLI

## Development Setup
- Run server instances with `python server.py <port>`
- Run clients with `python client.py`
- Configure multicast settings in `config.py`

## Technical Constraints
- Uses UDP; message ordering and reliability handled at application level.
- CLI-driven interface (no GUI or web client).
- Relies on multicast group reachability for discovery.

## Dependencies
- `click` (see `requirements.txt`)

## Tooling Patterns
- No build system; direct Python execution.
- Uses local network interfaces for UDP multicast.