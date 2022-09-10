"""
pybox.wmutex - Toolbox weak mutex implementation for Python
Copyright (C) 2022 Matthias Kruk

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import time

def trylock(mutex):
    """Attempt to lock a wmutex once."""

    pid = str(os.getpid())

    try:
        os.symlink(pid, mutex)
    except:
        return False

    return True


def lock(mutex, timeout = -1):
    """Lock a mutex, with timeout."""

    while not trylock(mutex):
        timeout -= 1

        if timeout == 0:
            return False

        time.sleep(1)

    return True


def unlock(mutex):
    """Unlock a mutex."""

    try:
        os.remove(mutex)
    except:
        return False

    return True
