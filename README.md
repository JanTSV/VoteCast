# VoteCast

_VoteCast_ is a multi-client poll platform.

Multiple clients can form 'poll groups' in which a consensus should be reached among them. In order to form a group, they have to connect to a multi-server system (one leader, multiple backup servers). Upon connecting they receive a list of existing groups which they can join, or form a new group. The information of the creation of a new group should be available to all already connected clients.
In each group, every client can start a poll request. If multiple clients want to start a request simultaneously, use e.g. the Hirschberg and Sinclair algorithm to decide upon the 'poll master'. The poll and poll master are reliably multicasted by the server (leader) to all group participants. Upon receiving the poll request, each client can vote for the preferred option. The aggregated result of the vote is again reliably multicasted to every group member that participated in the voting.