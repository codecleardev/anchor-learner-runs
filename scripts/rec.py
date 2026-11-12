# Appends one step to transcript.jsonl and transcript.txt. Called by the in-container driver.
import json, sys, time
phase, cmd, rc, t0, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
rd = lambda p: open(p, errors="replace").read()
so, se = rd("/tmp/o"), rd("/tmp/e")
row = {"phase": phase, "cmd": cmd, "stdout": so, "stderr": se, "exit": rc, "seconds": round(time.time() - t0, 2)}
open(f"{out}/transcript.jsonl", "a").write(json.dumps(row) + "\n")
with open(f"{out}/transcript.txt", "a") as f:
    f.write(f"[{phase}] $ {cmd}\n{so}{se}[exit {rc}, {row['seconds']}s]\n\n")
