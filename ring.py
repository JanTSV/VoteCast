from typing import List


def build_ring(server) -> None:
    """Compute ordered ring and set left/right neighbors safely."""
    # Ensure self is present
    if server.id not in server.servers:
        server.servers.add(server.id)

    ordered: List[str] = sorted(server.servers)
    server.log(f"Ordered ring: {ordered}")

    if not ordered:
        server.log("Warning: Empty ring, cannot set neighbors")
        return

    idx = ordered.index(server.id)
    server.left = ordered[(idx - 1) % len(ordered)]
    server.right = ordered[(idx + 1) % len(ordered)]

    # CRITICAL FIX: Validate that neighbors are not None
    if server.left is None or server.right is None:
        server.log(f"Warning: Ring building failed - left={server.left}, right={server.right}")
        return

    server.log(f"Created ring left={server.left}, right={server.right}")
