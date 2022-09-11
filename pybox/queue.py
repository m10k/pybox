"""
pybox.queue - Toolbox queue implementation for Python
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

import pybox.mutex as mutex
import pybox.sem as   sem

QUEUE_PATH = os.getenv("HOME") + "/.toolbox/queue"

def _get_path(queue):
    if queue.find("/") >= 0:
        return queue

    return f"{QUEUE_PATH}/{queue}"


def _get_sem(queue):
    return _get_path(queue) + "/sem"


def _get_mutex(queue):
    return _get_path(queue) + "/mutex"


def _get_data(queue):
    return _get_path(queue) + "/data"


def init(queue):
    """Create a new queue."""

    path = _get_path(queue)
    sema = _get_sem(queue)

    try:
        os.mkdir(path)
    except:
        return False

    if not sem.init(sema, 0):
        try:
            os.rmdir(path)
        except:
            pass

        return False

    return True


def destroy(queue):
    """Remove a queue."""

    path = _get_path(queue)
    sema = _get_sem(queue)

    if not sem.destroy(sema):
        return False

    try:
        shutil.rmtree(path, ignore_errors = True)
    except:
        return False

    return True


def _append(what, where):
    try:
        handle = open(where, "a+")
        handle.write(what)
        if not what.endswith("\n"):
            handle.write("\n")
        handle.close()
    except:
        return False

    return True


def put(queue, item):
    """Append data to a queue."""

    mtx = _get_mutex(queue)
    sema = _get_sem(queue)
    data = _get_data(queue)
    success = True

    mutex.lock(mtx)

    if not _append(item, data):
        success = False

    mutex.unlock(mtx)

    if success:
        success = sem.post(sema)

    return success


def _head(path):
    try:
        handle = open(path, "r")
        line = handle.readline()
        handle.close()
        return line.rstrip("\n")
    except:
        return None


def _remove_head(path):
    try:
        handle = open(path, "r")
        lines = handle.readlines()
        handle.close()

        handle = open(path, "w+")
        for line in lines[1:]:
            handle.write(line)
        handle.close()
    except:
        return False

    return True


def _lines(path):
    result = []

    try:
        handle = open(path, "r")
        lines = handle.readlines()
        handle.close()
        for line in lines:
            result += [ line.rstrip("\n") ]
    except:
        pass

    return result


def get(queue, timeout = -1):
    """Get an item from the head of a queue, waiting if necessary."""

    sema = _get_sem(queue)
    mtx = _get_mutex(queue)
    data = _get_data(queue)
    retval = None

    if sem.wait(sema, timeout):
        mutex.lock(mtx)

        head = _head(data)
        if head is not None:
            if _remove_head(data):
                retval = head

        mutex.unlock(mtx)

    return retval


def foreach(queue, func, *args):
    """Perform an action on each item in the queue."""

    data = _get_data(queue)
    mtx = _get_mutex(queue)
    result = True

    if not mutex.lock(mtx):
        return False

    for line in _lines(data):
        if not func(line, *args):
            result = False
            break

    mutex.unlock(mtx)

    return result
