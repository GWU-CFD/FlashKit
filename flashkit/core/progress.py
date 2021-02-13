
# type annotations
from __future__ import annotations
from typing import TYPE_CHECKING

# standard libraries
import sys
import time
from contextlib import contextmanager 
 
if TYPE_CHECKING:
    from typing import Optional

@contextmanager
def simple_bar(total: Optional[int] = None):
    """Provides a simple progress bar, for when alive_bar fails."""
    if total is None: return Progress.unknown()
    return Progress.definite(total)

class Progress:
    terminal: int = 36
    progress: int = 0
    sentinal: str = '█'
    blanking: str = ' '
    entrance: str = '    '
    cyclings: float = 5.0  
    total: Optional[int] = None
    start_time: Optional[float] = None
    
    def __init__(self):
        raise NotImplementedError('Cannot create a naked Progress instance!') 

    @classmethod
    def definite(cls, total):
        cls.total = total
        cls.start_time = time.time()
        yield cls.step_known
        cls.end_known()

    @classmethod
    def unknown(cls):
        cls.start_time = time.time()
        yield cls.step_unknown
        cls.end_unknown()

    @classmethod
    def step_known(cls):
        cls.progress += 1
        part = cls.progress
        total = cls.total
        done = int(min(1, part / total) * cls.terminal)
        togo = cls.terminal - done
        frac = part / total * 100.0
        last = time.time() - cls.start_time
        rate = part / last if last > 1.0 else 0.0
        done_str = cls.sentinal * done
        togo_str = cls.blanking * togo
        message = f'{cls.entrance}|{done_str}{togo_str}| {part}/{total} [{frac:.0f}%] in {last:.1f}s ({rate:.2f}/s)'
        print(message, end='\r')

    @classmethod
    def step_unknown(cls):
        cls.progress += 1
        part = cls.progress
        last = time.time() - cls.start_time
        rate = part / last if last > 1.0 else 0.0
        done = int((last % cls.cyclings) / cls.cyclings * cls.terminal)
        togo = cls.terminal - done
        done_str = cls.sentinal * done
        togo_str = cls.blanking * togo
        message = f'{cls.entrance}|{done_str}{togo_str}| {part} in {last:.1f}s ({rate:.2f}/s)'
        print(message, end='\r')

    @classmethod
    def end_known(cls):
        part = cls.progress
        last = time.time() - cls.start_time
        rate = part / last
        done_str = '█' * cls.terminal
        print(f'{cls.entrance}|{done_str}| {part}/{part} [{100.0:.0f}%] in {last:.1f}s ({rate:.2f}/s)'.ljust(120))
        cls.progress = 0
        cls.total = None
        cls.start_time = None

    @classmethod
    def end_unknown(cls):
        part = cls.progress
        last = time.time() - cls.start_time
        rate = part / last
        done_str = '█' * cls.terminal
        print(f'{cls.entrance}|{done_str}| {part} in {last:.1f}s ({rate:.2f}/s)'.ljust(120))
        cls.progress = 0
        cls.total = None
        cls.start_time = None
