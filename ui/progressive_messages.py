import asyncio
from aiogram.types import Message

class ProgressiveMessage:
    def __init__(
        self,
        message: Message,
        total_timeout: float = 8.0,
        update_interval: float = 0.8,
    ):
        """
        :param message: объект Message из aiogram
        :param total_timeout: общий таймаут (можно не использовать)
        :param update_interval: интервал обновления точек
        """
        self.message = message
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task | None = None
        self._stage_map: dict[str, str] = {}  # {"embedding": "🧠 Разбираю ваш запрос"}
        self._current_stage: str | None = None
        self._dots = ["...", "..", "."]  # точки идут убыванием
        self._dot_index = 0
        self._update_interval = update_interval

    def set_stage_mapping(self, mapping: dict[str, str]):
        """Задаём текст стадий"""
        self._stage_map = mapping

    async def start(self):
        """Запуск цикла анимации точек"""
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        """Остановка прогресса"""
        self._stop_event.set()
        if self._task:
            await self._task

    async def update_stage(self, stage_name: str):
        """Меняем текущую стадию прогресса и сбрасываем точки"""
        self._current_stage = stage_name
        self._dot_index = 0  # сброс цикла точек при смене стадии

    async def _run(self):
        """Цикличное добавление точек в убывающем порядке"""
        while not self._stop_event.is_set():
            if self._current_stage and self._current_stage in self._stage_map:
                base_text = self._stage_map[self._current_stage]
                dots_text = self._dots[self._dot_index]
                try:
                    await self.message.edit_text(f"{base_text}{dots_text}")
                except Exception:
                    pass

                # переключаем индекс по кругу
                self._dot_index = (self._dot_index + 1) % len(self._dots)

            await asyncio.sleep(self._update_interval)
