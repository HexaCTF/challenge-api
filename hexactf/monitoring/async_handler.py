import logging
import queue
import threading

class AsyncHandler(logging.Handler):
    def __init__(self, handler):
        super().__init__()
        self.handler = handler
        self.log_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._log_worker, name="AsyncLogWorker")
        self.thread.daemon = True
        self.thread.start()

    def emit(self, record):
        """Put a log record in the queue."""
        try:
            self.log_queue.put(record, block=False)
        except queue.Full:
            # If the queue is full, we drop the log to avoid blocking.
            print("Log queue is full. Dropping log record.")

    def _log_worker(self):
        """Process log records from the queue."""
        while not self.stop_event.is_set():
            try:
                # Wait for a log record from the queue
                record = self.log_queue.get(timeout=0.2)
                try:
                    self.handler.emit(record)
                except Exception as handler_error:
                    # If an error occurs in the handler, we log it
                    print(f"Error emitting log record: {handler_error}")
                finally:
                    self.log_queue.task_done()
            except queue.Empty:
                # Continue if the queue is empty
                continue
            except Exception as e:
                # Handle unexpected exceptions
                print(f"Unexpected error in async logging: {e}")

    def close(self):
        """Shutdown the logging thread gracefully."""
        self.stop_event.set()
        self.thread.join()
        super().close()
