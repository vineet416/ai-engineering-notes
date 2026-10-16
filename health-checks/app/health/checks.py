# The readiness checks. Each one answers: "can I actually reach this thing right now?"
import asyncio
import time
import urllib.request
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List

from sqlalchemy import text
from sqlalchemy.engine import Engine


@dataclass
class Check:
    name: str
    run: Callable[[], Awaitable[None]]  # raises if the dependency is broken
    # critical=True: the app is useless without it, so stop sending it traffic.
    # critical=False: report it, but keep serving (the app can work around it).
    critical: bool = True


def database_check(engine: Engine) -> Callable[[], Awaitable[None]]:
    def ping() -> None:
        # A real round trip. Opens a connection and reads from the tasks table,
        # so a missing file, a locked DB or a missing table all show up here.
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM tasks LIMIT 1"))

    async def run() -> None:
        await asyncio.to_thread(ping)  # don't block the event loop

    return run


def http_check(url: str, timeout: float) -> Callable[[], Awaitable[None]]:
    def ping() -> None:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "health-check"})
        with urllib.request.urlopen(req, timeout=timeout) as res:
            if res.status >= 500:
                raise RuntimeError(f"HTTP {res.status}")

    async def run() -> None:
        await asyncio.to_thread(ping)

    return run


async def _run_one(check: Check, timeout: float) -> Dict[str, Any]:
    start = time.perf_counter()
    try:
        # wait_for: if a dependency hangs, we give up after `timeout` seconds
        # instead of making the load balancer wait forever.
        await asyncio.wait_for(check.run(), timeout=timeout)
        result: Dict[str, Any] = {"status": "up"}
    except asyncio.TimeoutError:
        result = {"status": "down", "error": f"timed out after {timeout}s"}
    except Exception as exc:  # any failure means "down", with the reason
        # SQLAlchemy wraps the driver's error; .orig is the short, readable one
        err = getattr(exc, "orig", None) or exc
        result = {"status": "down", "error": str(err) or type(err).__name__}
    result["critical"] = check.critical
    result["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
    return result


async def run_checks(checks: List[Check], timeout: float) -> Dict[str, Any]:
    # All checks run at the same time, so 3 slow checks cost 2s, not 6s.
    results = await asyncio.gather(*(_run_one(c, timeout) for c in checks))
    by_name = {c.name: r for c, r in zip(checks, results)}

    critical_down = any(r["status"] == "down" and r["critical"] for r in results)
    anything_down = any(r["status"] == "down" for r in results)

    if critical_down:
        status = "not_ready"
    elif anything_down:
        status = "degraded"
    else:
        status = "ready"
    return {"status": status, "checks": by_name}
