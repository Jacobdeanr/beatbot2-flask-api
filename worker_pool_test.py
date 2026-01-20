from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Generic, Optional, TypeVar


TResult = TypeVar("TResult")

# -----------------------------------------------------------------------------
# Data objects you pass around
# -----------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Job(Generic[TResult]):
    """
    A unit of work.

    This object is created by the PRODUCER (your code that wants work done).
    It contains:
      - name: just for logging/debugging
      - payload: input data for the work
      - handler: the async function that will actually do the work

    The worker never knows what this job really means. It just runs handler(payload).
    """
    name: str
    payload: Any
    handler: Callable[[Any], Awaitable[TResult]]


@dataclass(frozen=True, slots=True)
class JobResult(Generic[TResult]):
    """
    The outcome of running a Job.

    This is what the WORKER produces and gives back to the SUBMITTER.
    It wraps both success and failure so the worker never throws into the pool.
    """
    job_name: str
    ok: bool
    value: Optional[TResult] = None
    error: Optional[BaseException] = None


@dataclass(slots=True)
class JobEnvelope(Generic[TResult]):
    """
    Internal glue object.

    Created by submit(), consumed by a Worker.

    It bundles:
      - the Job (what to run)
      - the Future (where the answer must be written)

    Whoever submitted the job is awaiting this Future.
    """
    job: Job[TResult]
    future: asyncio.Future[JobResult[TResult]]


# -----------------------------------------------------------------------------
# Worker
# -----------------------------------------------------------------------------

class Worker:
    """
    A Worker is ONE asyncio Task that runs forever.

    It repeatedly:
      - pulls one JobEnvelope from the queue
      - executes the job
      - writes the result into the envelope.future

    Multiple Workers share the same queue.
    """

    def __init__(self, *, name: str, queue: asyncio.Queue[JobEnvelope[Any]]) -> None:
        self._name = name
        self._queue = queue
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        """
        Creates the asyncio Task that runs _run_loop().

        Nothing runs until this is called.
        """
        if self._task is not None:
            raise RuntimeError("Worker already started")

        # The worker task is now running in the background
        self._task = asyncio.create_task(self._run_loop(), name=f"worker:{self._name}")

    async def stop(self) -> None:
        """
        Stop this worker by cancelling its Task.
        """
        if self._task is None:
            return

        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass

    async def _run_loop(self) -> None:
        """
        The infinite worker loop.

        This never exits on its own.
        WorkerPool.stop() cancels this task to make it exit.
        """
        while True:
            # Wait until someone submits a job
            envelope = await self._queue.get()

            try:
                job = envelope.job

                # If the caller timed out or cancelled, skip this job.
                # (The work might still be running elsewhere, but we avoid doing it here.)
                if envelope.future.cancelled():
                    continue

                try:
                    # Run the job. This is where the real work happens.
                    value = await job.handler(job.payload)

                    # Package success as data
                    result: JobResult[Any] = JobResult(
                        job_name=job.name,
                        ok=True,
                        value=value,
                        error=None,
                    )
                except Exception as exc:
                    # Package failure as data
                    result = JobResult(
                        job_name=job.name,
                        ok=False,
                        value=None,
                        error=exc,
                    )

                # Deliver the result to whoever submitted the job
                if not envelope.future.cancelled():
                    envelope.future.set_result(result)

            finally:
                # Tell the queue "this job is done"
                self._queue.task_done()


# -----------------------------------------------------------------------------
# WorkerPool (one queue, N workers)
# -----------------------------------------------------------------------------

class WorkerPool:
    """
    This is the public API you use.

    It owns:
      - the shared queue
      - all Worker tasks

    You never talk to Workers directly, only through submit().
    """

    def __init__(self, *, worker_count: int) -> None:
        self._queue: asyncio.Queue[JobEnvelope[Any]] = asyncio.Queue()

        # Create N workers that all listen to the same queue
        self._workers = [Worker(name=str(i), queue=self._queue) for i in range(worker_count)]

        self._closed = False

    async def __aenter__(self) -> "WorkerPool":
        # Start all workers when entering the async with block
        for w in self._workers:
            w.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def submit(self, job: Job[TResult], *, timeout: float | None = None) -> JobResult[TResult]:
        """
        This is called by PRODUCERS.

        It:
          1) creates a Future
          2) wraps Job + Future into a JobEnvelope
          3) puts it into the queue
          4) waits until a Worker completes the Future
        """
        if self._closed:
            raise RuntimeError("WorkerPool is closed")

        loop = asyncio.get_running_loop()

        # This Future is what the caller will await
        future: asyncio.Future[JobResult[TResult]] = loop.create_future()

        envelope: JobEnvelope[TResult] = JobEnvelope(job=job, future=future)

        # Put the work into the shared queue
        await self._queue.put(envelope)

        # Wait for a Worker to set_result() on this future
        if timeout is None:
            return await future
        return await asyncio.wait_for(future, timeout=timeout)

    async def drain(self) -> None:
        """
        Wait until all queued jobs have been processed.
        """
        await self._queue.join()

    async def close(self) -> None:
        """
        Shut down the pool.

        First wait for queued jobs to finish,
        then cancel all worker tasks.
        """
        if self._closed:
            return
        self._closed = True

        await self.drain()

        for w in self._workers:
            await w.stop()


# -----------------------------------------------------------------------------
# Example job handlers (async functions)
# -----------------------------------------------------------------------------

async def slow_add(payload: dict[str, int]) -> int:
    """
    This is just a user-defined job handler.

    The worker does not care what it does.
    """
    await asyncio.sleep(4)
    return payload["a"] + payload["b"]


async def main() -> None:
    # Create 2 background workers
    async with WorkerPool(worker_count=2) as pool:
        jobs = [
            Job[int](name="add-1", payload={"a": 1, "b": 2}, handler=slow_add),
            Job[int](name="add-2", payload={"a": 10, "b": 20}, handler=slow_add),
            Job[int](name="add-3", payload={"a": 7, "b": 9}, handler=slow_add),
        ]

        # Submit all jobs at once.
        # Each submit() call creates a Future and waits on it.
        # Workers fill those Futures as jobs complete.
        results = await asyncio.gather(*(pool.submit(job, timeout=10) for job in jobs))

        for r in results:
            if r.ok:
                print(f"{r.job_name} -> {r.value}")
            else:
                print(f"{r.job_name} failed: {r.error!r}")


if __name__ == "__main__":
    asyncio.run(main())
