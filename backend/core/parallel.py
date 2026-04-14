# ============================================================
# VIO 83 AI ORCHESTRA — Copyright (c) 2026 Viorica Porcu (vio83)
# DUAL LICENSE: Proprietary + AGPL-3.0 — See LICENSE files
# ALL RIGHTS RESERVED — https://github.com/vio83/vio83-ai-orchestra
# ============================================================
"""
VIO 83 AI ORCHESTRA — Parallel Processing Engine
Esecuzione parallela e concorrente di task:

- TaskPool: Esegui N task in parallelo con limiti di concorrenza
- ParallelQuery: Query multiple sorgenti contemporaneamente
- BatchProcessor: Processa batch di documenti in parallelo
- PipelineExecutor: Pipeline di trasformazioni async
- Cross-Check: Verifica incrociata parallela tra provider AI

Pattern: Semaphore-bounded async parallelism
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger("vio83.parallel")

T = TypeVar("T")


@dataclass
class TaskResult:
    """Risultato di un task parallelo."""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    latency_ms: int = 0
    source: str = ""


class TaskPool:
    """
    Pool di task asincroni con limite di concorrenza.
    Usa asyncio.Semaphore per controllare il parallelismo.

    Esempio:
        pool = TaskPool(max_concurrent=5)
        results = await pool.run_all([
            ("task1", fetch_from_wikipedia, ["query"]),
            ("task2", fetch_from_crossref, ["query"]),
            ("task3", fetch_from_openalex, ["query"]),
        ])
    """

    def __init__(self, max_concurrent: int = 10, timeout: float = 60.0):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_tasks = 0
        self._completed_tasks = 0
        self._failed_tasks = 0

    async def _run_task(
        self, task_id: str, func: Callable, args: list = None, kwargs: dict = None
    ) -> TaskResult:
        """Esegui un singolo task con semaphore."""
        args = args or []
        kwargs = kwargs or {}
        start = time.time()
        async with self._semaphore:
            self._active_tasks += 1
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await asyncio.wait_for(
                        func(*args, **kwargs), timeout=self.timeout
                    )
                else:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: func(*args, **kwargs)
                    )
                latency = int((time.time() - start) * 1000)
                self._completed_tasks += 1
                return TaskResult(
                    task_id=task_id, success=True, result=result,
                    latency_ms=latency, source=func.__name__
                )
            except asyncio.TimeoutError:
                self._failed_tasks += 1
                return TaskResult(
                    task_id=task_id, success=False,
                    error=f"Timeout dopo {self.timeout}s",
                    latency_ms=int((time.time() - start) * 1000),
                    source=func.__name__
                )
            except Exception as e:
                self._failed_tasks += 1
                return TaskResult(
                    task_id=task_id, success=False, error=str(e),
                    latency_ms=int((time.time() - start) * 1000),
                    source=func.__name__
                )
            finally:
                self._active_tasks -= 1

    async def run_all(
        self, tasks: list[tuple[str, Callable, list]]
    ) -> list[TaskResult]:
        """
        Esegui tutti i task in parallelo.
        tasks: lista di (task_id, function, args)
        """
        coroutines = [
            self._run_task(task_id, func, args)
            for task_id, func, args in tasks
        ]
        results = await asyncio.gather(*coroutines, return_exceptions=False)
        return list(results)

    async def run_first_success(
        self, tasks: list[tuple[str, Callable, list]]
    ) -> Optional[TaskResult]:
        """
        Esegui tutti i task ma ritorna il primo che ha successo.
        Cancella i rimanenti (ottimizzazione latenza).
        """
        pending = set()
        for task_id, func, args in tasks:
            coro = self._run_task(task_id, func, args)
            pending.add(asyncio.create_task(coro))

        first_success = None
        while pending:
            done, pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED
            )
            for task in done:
                result = task.result()
                if result.success:
                    first_success = result
                    for p in pending:
                        p.cancel()
                    return first_success

        return first_success

    @property
    def stats(self) -> dict:
        return {
            "max_concurrent": self.max_concurrent,
            "active_tasks": self._active_tasks,
            "completed": self._completed_tasks,
            "failed": self._failed_tasks,
        }


class ParallelQueryEngine:
    """
    Esegue query su multiple sorgenti di conoscenza in parallelo.
    Merge e deduplica i risultati.
    """

    def __init__(self, max_concurrent: int = 5, timeout: float = 30.0):
        self.pool = TaskPool(max_concurrent=max_concurrent, timeout=timeout)

    async def query_all_sources(
        self,
        query: str,
        sources: dict[str, Callable],
    ) -> dict[str, TaskResult]:
        """
        Interroga tutte le sorgenti in parallelo.
        sources: {"wikipedia": fetch_func, "crossref": fetch_func, ...}
        """
        tasks = [
            (name, func, [query])
            for name, func in sources.items()
        ]
        results = await self.pool.run_all(tasks)
        return {r.task_id: r for r in results}

    async def cross_check(
        self,
        question: str,
        providers: dict[str, Callable],
        min_agreement: float = 0.6,
    ) -> dict:
        """
        Verifica incrociata: invia la stessa domanda a N provider AI
        e confronta le risposte per consistenza.
        """
        results = await self.query_all_sources(question, providers)
        successful = {k: v for k, v in results.items() if v.success}

        if len(successful) < 2:
            return {
                "verified": False,
                "reason": "Meno di 2 provider hanno risposto",
                "results": {k: v.result for k, v in successful.items()},
            }

        # Calcola similarità tra risposte (semplice: overlap parole)
        responses = {k: str(v.result).lower().split() for k, v in successful.items()}
        provrs_list = list(responses.keys())
        agreements = []

        for i in range(len(provrs_list)):
            for j in range(i + 1, len(provrs_list)):
                words_a = set(responses[provrs_list[i]])
                words_b = set(responses[provrs_list[j]])
                if words_a and words_b:
                    overlap = len(words_a & words_b) / max(len(words_a | words_b), 1)
                    agreements.append(overlap)

        avg_agreement = sum(agreements) / len(agreements) if agreements else 0

        return {
            "verified": avg_agreement >= min_agreement,
            "agreement_score": round(avg_agreement, 4),
            "provrs_responded": list(successful.keys()),
            "latencies": {k: v.latency_ms for k, v in successful.items()},
            "results": {k: v.result for k, v in successful.items()},
        }


class BatchProcessor:
    """
    Processa batch di elementi in parallelo con progress tracking.
    ale per ingestion massiva di documenti.
    """

    def __init__(self, max_concurrent: int = 5, batch_size: int = 50):
        self.pool = TaskPool(max_concurrent=max_concurrent)
        self.batch_size = batch_size

    async def process_batch(
        self,
        items: list[Any],
        processor: Callable,
        on_progress: Optional[Callable] = None,
    ) -> list[TaskResult]:
        """
        Processa una lista di elementi in batch paralleli.
        """
        all_results = []
        total = len(items)

        for i in range(0, total, self.batch_size):
            batch = items[i:i + self.batch_size]
            tasks = [
                (f"item_{i+j}", processor, [item])
                for j, item in enumerate(batch)
            ]
            batch_results = await self.pool.run_all(tasks)
            all_results.extend(batch_results)

            if on_progress:
                progress = min(i + len(batch), total) / total
                on_progress(progress, len(all_results), total)

        return all_results


class PipelineExecutor:
    """
    Pipeline di trasformazioni async.
    Ogni step riceve l'output dello step precedente.

    Esempio:
        pipeline = PipelineExecutor()
        pipeline.add_step("extract", extract_text)
        pipeline.add_step("chunk", split_into_chunks)
        pipeline.add_step("embed", generate_embeddings)
        pipeline.add_step("index", store_in_db)
        result = await pipeline.execute(raw_document)
    """

    def __init__(self):
        self._steps: list[tuple[str, Callable]] = []

    def add_step(self, name: str, func: Callable):
        self._steps.append((name, func))
        return self

    async def execute(self, input_data: Any) -> dict:
        """Esegui la pipeline step by step."""
        current = input_data
        timings = {}
        for name, func in self._steps:
            start = time.time()
            try:
                if asyncio.iscoroutinefunction(func):
                    current = await func(current)
                else:
                    current = func(current)
                timings[name] = int((time.time() - start) * 1000)
            except Exception as e:
                return {
                    "success": False,
                    "failed_step": name,
                    "error": str(e),
                    "timings": timings,
                }
        return {
            "success": True,
            "result": current,
            "timings": timings,
            "total_ms": sum(timings.values()),
        }
