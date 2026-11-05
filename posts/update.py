"""One command to refresh the site after you have re-aggregated the provinces (posts/monthly_agg.py ab|sk|bc FOLDER).
Runs, in order: post generators, scorecard, revision tracker, feed/site build, number verification. Stops on the first failure.
Usage: python posts/update.py [--skip-gen]"""
import subprocess
import sys
from pathlib import Path

P = Path(__file__).resolve().parent
STEPS = [["gen_posts.py"], ["gen_posts2.py"], ["gen_posts3.py"], ["scorecard.py"], ["revisions.py"], ["build_feed.py"], ["verify_site.py"]]
if __name__ == "__main__":
    for step in STEPS:
        if "--skip-gen" in sys.argv and step[0].startswith("gen_posts"):
            continue
        print("==>", " ".join(step), flush=True)
        r = subprocess.run([sys.executable, str(P / step[0])], cwd=P.parent)
        if r.returncode:
            sys.exit(f"{step[0]} failed")
    print("Done. Review `git status`, then commit and push.")
