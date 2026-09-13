import queue
import threading
from collections.abc import Callable


threading.stack_size(1024 * 1024)


class MinimalThreadPoolExecutor:
    """Stripped down performant ThreadPoolExecutor for submit only"""
    def __init__(self, min_threads: int, max_threads: int):
        self.__min_threads = min_threads
        self.__max_threads = max_threads
        self.__shutdown_requested = False

        self.__threads = []
        self.__task_queue = queue.SimpleQueue()

        self.busy_thread_count = 0
        self.__busy_thread_count_lock = threading.Lock()

        self.thread_count = min_threads
        self.__thread_count_lock = threading.Lock()

        for _ in range(min_threads):
            thread = threading.Thread(target=self.__thread_worker, daemon=True)
            thread.start()
            self.__threads.append(thread)

    def submit(self, callable_: Callable, *args, **kwargs) -> None:
        self.__task_queue.put((callable_, args, kwargs))

        if self.thread_count == self.busy_thread_count and self.thread_count < self.__max_threads:
            with self.__thread_count_lock:
                self.thread_count += 1
            thread = threading.Thread(target=self.__thread_worker, daemon=True)
            thread.start()
            self.__threads.append(thread)

    def __thread_worker(self)  -> None:
        while True:
            call, args, kwargs = self.__task_queue.get()

            with self.__busy_thread_count_lock:
                self.busy_thread_count += 1

            call(*args, **kwargs)

            with self.__busy_thread_count_lock:
                self.busy_thread_count -= 1
