"""In-process job queue for audit runs."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

JobHandler = Callable[[str, dict[str, Any]], Awaitable[None]]


class JobQueue:
    """Simple in-process async job queue."""

    def __init__(self, max_concurrent: int = 2) -> None:
        self.queue: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue()
        self.max_concurrent = max_concurrent
        self.workers: list[asyncio.Task[None]] = []
        self.running = False

    async def start(self, worker_func: JobHandler) -> None:
        """Start worker tasks."""
        self.running = True
        for _ in range(self.max_concurrent):
            worker = asyncio.create_task(self._worker(worker_func))
            self.workers.append(worker)

    async def stop(self) -> None:
        """Stop all workers."""
        self.running = False
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

    async def enqueue(self, job_id: str, job_data: dict[str, Any]) -> None:
        """Enqueue a job."""
        await self.queue.put((job_id, job_data))

    async def _worker(self, worker_func: JobHandler) -> None:
        """Process jobs until the queue is stopped."""
        while self.running:
            try:
                job_id, job_data = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                await worker_func(job_id, job_data)
                self.queue.task_done()
            except TimeoutError:
                continue
            except Exception as exc:
                print(f"Worker error: {type(exc).__name__}")
