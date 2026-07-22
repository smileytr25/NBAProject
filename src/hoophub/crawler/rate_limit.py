import atexit
import json
import os
import signal
import time
import uuid 
from pathlib import Path
from types import FrameType
from typing import Callable, Optional

STATE_PATH = Path(
    os.getenv(
        "HOOPHUB_RATE_LIMIT_STATE",
        Path.home() / ".cache" / "hoophub" / "crawler_rate_limit.json",
    )
)
SAFETY_BUFFER_SECONDS = 1.0


class Stack():
    def __init__(self, page_limit: int, dropoff_time: int):
        if page_limit < 1:
            raise ValueError("page_limit must be at least 1")

        self.capacity = page_limit 
        self.dropoff_time = dropoff_time
        self.stack = {}
        self.load()

    def pop(self, reqId: uuid.UUID):
        del self.stack[reqId]
        
    def size(self):
        return len(self.stack)
    
    def add(self, progress_writer: Callable[[str], None] | None = None):
        while True:
            self.check_requests_for_dropoff()

            if not self.check_capacity():
                self.stack[uuid.uuid4()] = time.time()
                self.save()
                return True

            wait_time = self.calculate_wait()
            message = f"Rate limited: waiting {wait_time:.2f} seconds"
            if progress_writer is None:
                print(message)
            else:
                progress_writer(message)
            time.sleep(wait_time)

    def check_requests_for_dropoff(self):
        current_time = time.time() 
        changed = False

        stack_contents = list(self.stack.items())

        for reqId, pushTime in stack_contents:
            time_on_stack = current_time - pushTime
            if time_on_stack >= self.dropoff_time + SAFETY_BUFFER_SECONDS:
                self.pop(reqId)
                changed = True

        if changed:
            self.save()

    def check_capacity(self):
        return self.size() >= self.capacity
    
    def calculate_wait(self):
        earliest_time_on_stack = min(self.stack.values())
        time_to_wait = max(
            self.dropoff_time + SAFETY_BUFFER_SECONDS - (time.time() - earliest_time_on_stack),
            SAFETY_BUFFER_SECONDS,
        )
        return time_to_wait

    def load(self):
        if not STATE_PATH.exists():
            return

        try:
            state = json.loads(STATE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return

        timestamps = state.get("timestamps", [])
        self.stack = {
            uuid.uuid4(): float(timestamp)
            for timestamp in timestamps
        }
        self.check_requests_for_dropoff()

    def save(self):
        state = {
            "timestamps": list(self.stack.values())
        }
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state))

_shared_stack = None

def get_shared_stack(page_limit: int, dropoff_time: int = 60):
    global _shared_stack

    if (
        _shared_stack is None
        or _shared_stack.capacity != page_limit
        or _shared_stack.dropoff_time != dropoff_time
    ):
        _shared_stack = Stack(page_limit, dropoff_time)

    return _shared_stack

def wait_for_rate_limit(
    page_limit: int,
    dropoff_time:int = 60,
    progress_writer: Callable[[str], None] | None = None,
):
    get_shared_stack(page_limit, dropoff_time).add(progress_writer=progress_writer)

def save_shared_stack():
    if _shared_stack is not None:
        _shared_stack.save()

def handle_exit(signum: int, frame: Optional[FrameType]) -> None:
    save_shared_stack()
    raise KeyboardInterrupt

atexit.register(save_shared_stack)
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)
