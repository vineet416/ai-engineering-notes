import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def start_worker(extra_args=(), env_overrides=None):
    env = dict(os.environ, **(env_overrides or {}))
    return subprocess.Popen(
        [sys.executable, "-m", "app.worker", *extra_args],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def wait_for(check, timeout=30.0, every=0.05):
    end = time.time() + timeout
    while time.time() < end:
        if check():
            return True
        time.sleep(every)
    return False
