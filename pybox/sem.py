"""
pybox.sem - Toolbox semaphore implementation for Python
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
import shutil

import pybox.mutex  as mutex
import pybox.wmutex as wmutex

SEM_PATH = os.getenv("HOME") + "/.toolbox/sem"

def _get_path(sem):
    if sem.find("/") >= 0:
        return sem

    return f"{SEM_PATH}/{sem}"


def _get_waitlock(sem):
    return _get_path(sem) + "/waitlock"


def _get_countlock(sem):
    return _get_path(sem) + "/countlock"


def _get_owner(sem):
    return _get_path(sem) + "/owner"


def _get_counter(sem):
    return _get_path(sem) + "/counter"


def _read(path):
    try:
        handle = open(path, "r")
        data = handle.read()
        handle.close()
    except:
        data = ""

    return data


def _write(data, path):
    try:
        handle = open(path, "w+")
        handle.write(data)
        if not data.endswith("\n"):
            handle.write("\n")
        handle.close()
    except:
        return False

    return True


def _counter_inc(counter):
    value = _read(counter)

    if not value:
        return False

    value = int(value) + 1

    if not _write(str(value), counter):
        return False

    return True


def _counter_dec(counter):
    value = _read(counter)

    if not value:
        return False

    value = int(value) - 1

    if not _write(str(value), counter):
        return False

    return True


def init(name, value):
    """Create and initialize a semaphore."""

    sem = _get_path(name)
    waitlock = _get_waitlock(name)
    countlock = _get_countlock(name)
    counter = _get_counter(name)
    owner = _get_owner(name)
    status = False

    if not isinstance(value, int):
        return False

    try:
        os.mkdir(sem)
    except:
        print(f"Could not create {sem}")
        return False

    if not mutex.trylock(countlock):
        # Could not acquire countlock
        print(f"Could not acquire {countlock}")

    else:
        if not mutex.trylock(owner):
            print(f"Could not acquire {owner}")
            # Could not acquire owner mutex"

        elif (value == 0 and
              not wmutex.trylock(waitlock)):
            print(f"Could not acquire {waitlock}")
            # Could not acquire waitlock

        elif not _write(str(value), counter):
            print(f"Could not write {counter}")
            # Could not write counter

        else:
            status = True

        mutex.unlock(countlock)

    if not status:
        try:
            shutil.rmtree(sem, ignore_errors = True)
        except:
            # Could not remove sem
            pass

    return status


def destroy(name):
    """Remove a semaphore."""

    sem = _get_path(name)
    owner = _get_owner(name)

    if not mutex.unlock(owner):
        # Not my sem?
        return False

    try:
        shutil.rmtree(sem, ignore_errors = True)
    except:
        return False

    return True


def wait(name, timeout = -1):
    """Pass a semaphore, waiting as needed."""

    waitlock = _get_waitlock(name)
    countlock = _get_countlock(name)
    counter = _get_counter(name)
    err = False

    if not wmutex.lock(waitlock, timeout):
        return False

    if mutex.lock(countlock):
        _counter_dec(counter)
        count = int(_read(counter))

        if count > 0:
            wmutex.unlock(waitlock)

        mutex.unlock(countlock)
        err = True

    return err


def trywait(name):
    """Pass a semaphore immediately or fail."""

    waitlock = _get_waitlock(name)
    countlock = _get_countlock(name)
    counter = _get_counter(name)
    err = False

    if not wmutex.trylock(waitlock):
        return False

    if mutex.lock(countlock):
        _counter_dec(counter)
        mutex.unlock(countlock)
        err = True

    return err


def post(name):
    """Let a processes waiting on a semaphore pass."""

    waitlock = _get_waitlock(name)
    countlock = _get_countlock(name)
    counter = _get_counter(name)
    err = False

    if mutex.lock(countlock):
        _counter_inc(counter)
        mutex.unlock(countlock)

        if os.path.islink(waitlock):
            wmutex.unlock(waitlock)

        err = True

    return err


def peek(name):
    """Get the semaphore count without modifying it."""

    countlock = _get_countlock(name)
    counter = _get_counter(name)
    err = 1

    if mutex.lock(countlock):
        value = _read(counter)

        if value:
            err = 0

        mutex.unlock(countlock)

    if err == 0:
        return value

    return ""
