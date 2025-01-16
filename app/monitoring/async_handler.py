import logging
import queue
import threading

class AsyncHandler(logging.Handler):
    def __init__(self, handler):
        super().__init__()
        self.handler = handler
        self.log_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._log_worker)
        self.thread.daemon = True
        self.thread.start()

    def emit(self, record):
        try:
            self.log_queue.put(record)
        except Exception:
            self.handleError(record)

    def _log_worker(self):
        while not self.stop_event.is_set():
            try:
                record = self.log_queue.get(timeout=0.2)
                self.handler.emit(record)
                self.log_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                # 로깅 중 오류 처리
                print(f"Async logging error: {e}")

    def close(self):
        self.stop_event.set()
        self.thread.join()
        super().close()