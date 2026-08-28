# Chatbot Bootstrap

When this file is the chat runtime's repository entrypoint, establish repository guidance before continuing the task:

1. Read and follow the root [`AGENTS.md`](AGENTS.md).
2. For every concrete repository path involved in the task, walk from the repository root to that path's directory and read every nested `AGENTS.md` encountered, shallowest to deepest. Apply all files whose directory scope contains the target path.
3. If the task starts without a concrete target path, load nested `AGENTS.md` files when a target path becomes known. Re-evaluate the applicable stack whenever the task materially changes paths.
4. Read [`.agents/route/ROUTE.md`](.agents/route/ROUTE.md) and follow its Skill and Rule routing metadata.

`CHATBOT.md` alone owns this root-and-nested `AGENTS.md` loading harness. Do not require one `AGENTS.md` to discover or load another `AGENTS.md`.

Do not copy or reinterpret repository policy here. The loaded `AGENTS.md` files and canonical agent-asset sources remain authoritative.
