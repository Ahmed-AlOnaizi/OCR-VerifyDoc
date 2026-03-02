import asyncio
import json
from typing import Any


class JobStore:
    """In-memory store for job state and SSE notifications."""

    def __init__(self):
        self._jobs: dict[int, dict[str, Any]] = {}
        self._events: dict[int, asyncio.Event] = {}

    def init_job(self, job_id: int):
        self._jobs[job_id] = {
            "status": "pending",
            "phase": "pending",
            "progress": 0.0,
            "result": None,
            "error": None,
        }
        self._events[job_id] = asyncio.Event()

    def update_job(self, job_id: int, **kwargs):
        if job_id in self._jobs:
            self._jobs[job_id].update(kwargs)
            # Signal waiting SSE clients
            if job_id in self._events:
                self._events[job_id].set()
                # Reset for next update
                self._events[job_id] = asyncio.Event()

    def get_job(self, job_id: int) -> dict[str, Any] | None:
        return self._jobs.get(job_id)

    async def wait_for_update(self, job_id: int, timeout: float = 30.0) -> bool:
        event = self._events.get(job_id)
        if event is None:
            return False
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    def serialize_job(self, job_id: int) -> str:
        data = self._jobs.get(job_id)
        if data is None:
            return ""
        return json.dumps({"job_id": job_id, **data})

    def cleanup(self, job_id: int):
        self._jobs.pop(job_id, None)
        self._events.pop(job_id, None)


job_store = JobStore()
