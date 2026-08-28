# Chatbot Bootstrap

1. Read and follow the root [`AGENTS.md`](AGENTS.md).
2. For each concrete target path, read every nested `AGENTS.md` below the root on the path to the target directory,
   shallowest to deepest. Re-evaluate the stack when target paths materially change.
3. Read [`.agents/route/ROUTE.md`](.agents/route/ROUTE.md) and follow it.

`CHATBOT.md` is the only repository-owned compatibility harness for cross-`AGENTS.md` loading. `AGENTS.md` files own
repository guidance; route metadata must not load the same AGENTS-backed Rules again.
