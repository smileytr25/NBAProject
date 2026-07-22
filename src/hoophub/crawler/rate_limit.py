import atexit
import json
import signal
import time
import uuid 
from pathlib import Path
from types import FrameType
from typing import Optional

STATE_PATH = Path(".crawler_rate_limit.json")


class Stack():
    def __init__(self, page_limit: int, dropoff_time: int):
        self.capacity = page_limit 
        self.dropoff_time = dropoff_time
        self.stack = {}
        self.load()

    def pop(self, reqId: uuid.UUID):
        del self.stack[reqId]
        
    def size(self):
        return len(self.stack)
    
    def add(self):
        while True:
            self.check_requests_for_dropoff()

            if not self.check_capacity():
                self.stack[uuid.uuid4()] = time.time()
                self.save()
                return True

            wait_time = self.calculate_wait()
            print(f"Waiting {wait_time:.2f} seconds for dropoff")
            time.sleep(wait_time)

    def check_requests_for_dropoff(self):
        current_time = time.time() 
        changed = False

        stack_contents = list(self.stack.items())

        for reqId, pushTime in stack_contents:
            time_on_stack = current_time - pushTime
            if time_on_stack > self.dropoff_time:
                self.pop(reqId)
                changed = True

        if changed:
            self.save()

    def check_capacity(self):
        return self.size() >= self.capacity
    
    def calculate_wait(self):
        earliest_time_on_stack = min(self.stack.values())
        time_to_wait = max(self.dropoff_time - (time.time() - earliest_time_on_stack), 0)
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

def wait_for_rate_limit(page_limit: int, dropoff_time:int = 60):
    get_shared_stack(page_limit, dropoff_time).add()

def save_shared_stack():
    if _shared_stack is not None:
        _shared_stack.save()

def handle_exit(signum: int, frame: Optional[FrameType]) -> None:
    save_shared_stack()
    raise KeyboardInterrupt

atexit.register(save_shared_stack)
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)
