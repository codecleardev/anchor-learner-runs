"""transcript.jsonl -> transcript.cast (asciicast v2), without running anything again. cast.py <out_dir>"""
import json, os, sys

out = sys.argv[1]
tp = f"{out}/transcript.jsonl"
if not os.path.exists(tp):
    sys.exit(0)
t = 0.0
with open(f"{out}/transcript.cast", "w") as f:
    f.write(json.dumps({"version": 2, "width": 120, "height": 32, "env": {"TERM": "xterm-256color", "SHELL": "/bin/bash"}}) + "\n")
    for line in open(tp):
        r = json.loads(line)
        f.write(json.dumps([round(t, 2), "o", "[%s] $ %s\r\n" % (r["phase"], r["cmd"])]) + "\n")
        t += r["seconds"]
        text = (r["stdout"] + r["stderr"]).replace("\r\n", "\n").replace("\n", "\r\n")
        f.write(json.dumps([round(t, 2), "o", text + "[exit %s, %ss]\r\n\r\n" % (r["exit"], r["seconds"])]) + "\n")
        t += 0.5
