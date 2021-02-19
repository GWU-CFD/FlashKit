"""Povides progress bar support for FlashKit library."""

# type annotations
from __future__ import annotations
from typing import TYPE_CHECKING

# standard libraries
import time
import threading
import pkg_resources
from contextlib import nullcontext

# internal libraries
from .parallel import is_parallel
from ..resources import CONFIG

# static analysis
if TYPE_CHECKING:
    from typing import Callable, Optional, Union
    from contextlib import AbstractContextManager
    Bar = Callable[..., AbstractContextManager]

# define public interface
__all__ = ['NULL_BAR', 'SimpleBar', 'get_bar', ]

# define default constants
BLANKING = CONFIG['core']['progress']['blanking']
CYCLINGS = CONFIG['core']['progress']['cyclings']
ENTRANCE = CONFIG['core']['progress']['entrance']
PROGRESS = CONFIG['core']['progress']['progress']
SENTINAL = CONFIG['core']['progress']['sentinal']
TERMINAL = CONFIG['core']['progress']['terminal']
UPDATING = CONFIG['core']['progress']['updating']

# Default context manager for progress bar
NULL_BAR: Bar = lambda *_: nullcontext(lambda *_: None) 

class SimpleBar(threading.Thread):
    """Implements a simple, threaded, context manager for a progress bar."""
    progress: int = PROGRESS
    terminal: int = TERMINAL
    sentinal: str = SENTINAL
    blanking: str = BLANKING
    entrance: str = ENTRANCE
    cyclings: float = CYCLINGS 
    
    def __enter__(self) -> Callable[[], None]:
        self.start()
        return self.update

    def __exit__(self, *args, **kwargs) -> None:
        self.calculate()
        self.flush(self.final())
        self.stop_event.set()

    def __init__(self, total: Optional[int] = None, *, fps: float  = UPDATING):
        threading.Thread.__init__(self, name='Progress')
        self.stop_event = threading.Event()
        self.sleep = 1.0 / fps 
        if total is not None:
            self.known = True
            self.total = total
        else:
            self.known = False
            self.total = 1
        self.write = self.write_known if self.known else self.write_unknown
        self.final = self.final_known if self.known else self.final_unknown
        self.clock = time.time()
        self.click = 0

    def calculate(self) -> None:
        self.last = time.time() - self.clock
        self.rate = self.click / self.last if self.last > 1.0 else 0.0
        self.frac = self.click / self.total * 100
        if self.known:
            done = int(min(1, self.click / self.total) * self.progress)
        else:
            done = int((self.last %  self.cyclings) / self.cyclings * self.progress)
        self.done = self.sentinal * done 
        self.left = self.blanking * (self.progress - done)

    def final_known(self) -> str:
        return f'{self.entrance}|{self.done}| {self.click}/{self.total} [{100.0:.0f}%] in {self.last:.1f}s ({self.rate:.2f}/s)\n'

    def final_unknown(self) -> str:
        done = self.sentinal * self.progress
        return f'{self.entrance}|{done}| {self.click} in {self.last:.1f}s ({self.rate:.2f}/s)\n'

    def flush(self, message: str) -> None:
        print(message.ljust(self.terminal), end='\r')
    
    def update(self) -> None:
        self.click += 1

    def run(self) -> None:
        while not self.stop_event.is_set():
            time.sleep(self.sleep)
            self.calculate()
            self.flush(self.write())
   
    def write_known(self) -> str:
        return f'{self.entrance}|{self.done}{self.left}| {self.click}/{self.total} [{self.frac:.0f}%] in {self.last:.1f}s ({self.rate:.2f}/s)'
               
    def write_unknown(self) -> str:
        return f'{self.entrance}|{self.done}{self.left}| {self.click} in {self.last:.1f}s ({self.rate:.2f}/s)'

def get_bar() -> Bar:
    """Retrives the best supported progress bar at runtime."""
    if is_parallel(): return SimpleBar
    try:
        pkg_resources.get_distribution('alive_progress')
        from alive_progress import alive_bar, config_handler # type: ignore
        config_handler.set_global(theme='smooth', unknown='horizontal')
        return alive_bar
    except pkg_resources.DistributionNotFound:
        return SimpleBar
