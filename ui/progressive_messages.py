import asyncio
import time
from collections import deque
from collections.abc import Mapping

from aiogram.types import Message


class ProgressiveMessage:
    def __init__(
        self,
        message: Message,
        *,
        update_interval: float = 1.2,
        default_min_stage_time: float = 0.0,
    ):
        self.message = message

        self._stop_event = asyncio.Event()
        self._task: asyncio.Task | None = None

        self._stage_text: dict[str, str] = {}

        self._stage_min_time: dict[str, float] = {}
        self._default_min_stage_time = float(default_min_stage_time)

        self._current_stage: str | None = None
        self._stage_started_at: float = 0.0

        self._stage_queue: deque[str] = deque()

        self._dots = ["...", "..", "."]
        self._dot_index = 0
        self._update_interval = float(update_interval)

        self._lock = asyncio.Lock()

    def set_stage_mapping(self, mapping: Mapping[str, str | tuple[str, float]]):
        self._stage_text.clear()
        self._stage_min_time.clear()

        for stage, value in mapping.items():
            if isinstance(value, tuple):
                text, min_time = value
                self._stage_text[stage] = str(text)
                self._stage_min_time[stage] = float(min_time)
            else:
                self._stage_text[stage] = str(value)

    async def start(self):
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        self._stop_event.set()
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def update_stage(self, stage_name: str):
        async with self._lock:
            if self._current_stage is None:
                self._apply_stage(stage_name)
                return

            if stage_name == self._current_stage:
                return

            if self._stage_queue and self._stage_queue[-1] == stage_name:
                return

            self._stage_queue.append(stage_name)

    def _min_time_for(self, stage: str) -> float:
        return self._stage_min_time.get(stage, self._default_min_stage_time)

    def _apply_stage(self, stage: str):
        self._current_stage = stage
        self._dot_index = 0
        self._stage_started_at = time.monotonic()

    async def _run(self):
        try:
            while not self._stop_event.is_set():
                async with self._lock:
                    cur = self._current_stage

                    if cur and self._stage_queue:
                        elapsed = time.monotonic() - self._stage_started_at
                        if elapsed >= self._min_time_for(cur):
                            nxt = self._stage_queue.popleft()
                            if nxt != cur:
                                self._apply_stage(nxt)
                                cur = self._current_stage

                if cur and cur in self._stage_text:
                    base = self._stage_text[cur]
                    dots = self._dots[self._dot_index]
                    try:
                        await self.message.edit_text(f"{base}{dots}")
                    except Exception:
                        pass

                    self._dot_index = (self._dot_index + 1) % len(self._dots)

                await asyncio.sleep(self._update_interval)
        except asyncio.CancelledError:
            return
