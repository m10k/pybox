"""
pybox.uipc.endpoint - Toolbox uipc endpoint implementation for Python
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

import io
import os
import sys
import time
import random
import shutil

from pybox      import queue
from pybox.uipc import msg

_ROOT        = "/var/lib/toolbox/uipc"
_GROUP       = "toolbox_ipc"
_PUBSUB_ROOT = _ROOT + "/pubsub"

def _write(what, where):
    try:
        handle = io.open(where, "w+")
        handle.write(what)
        if not what.endswith("\n"):
            handle.write("\n")
        handle.close()
    except:
        return False

    return True


def open(name = ""):
    """Create a new endpoint."""

    user = os.getenv("USER")

    if name == "":
        pid = os.getpid()
        script = sys.argv[0].split("/")[-1]
        date = int(time.time())
        suffix = random.randint(0, 65535)

        name = f"priv/{user}/{script}.{pid}.{date}.{suffix}"

    endpoint=f"{_ROOT}/{name}"

    if not os.path.exists(endpoint):
        try:
            os.mkdir(endpoint)
            os.mkdir(endpoint + "/subscriptions")
        except:
            print("Could not create endpoint")
            return None

        if (not queue.init(endpoint + "/queue") or
            not _write(str(user), endpoint + "/owner")):
            try:
                shutil.rmtree(endpoint, ignore_errors = True)
            except:
                pass

            return None

    return name


def get_subscriptions(endpoint):
    """Get topics that an endpoint is subscribed to."""

    subscription_dir = f"{_ROOT}/{endpoint}/subscriptions"
    subscriptions = []

    for sub in os.listdir(subscription_dir):
        if not os.path.islink(f"{subscription_dir}/{sub}"):
            continue
        subscriptions += [ sub.replace("_", "/") ]

    return subscriptions


def subscribe(endpoint, topic):
    """Subscribe an endpoint to a topic."""

    if not _topic_create(topic):
        return False

    return _topic_subscribe(endpoint, topic)


def unsubscribe(endpoint, topic):
    """Unsubscribe an endpoint from a topic."""

    sub = f"{_ROOT}/{endpoint}/subscriptions/" + topic.replace("/", "_")

    try:
        os.remove(sub)
    except:
        return False

    return True


def close(name):
    """Remove an endpoint."""

    endpoint = f"{_ROOT}/{name}"

    if not queue.destroy(endpoint + "/queue"):
        return False

    for subscription in get_subscriptions(name):
        unsubscribe(name, subscription)

    try:
        shutil.rmtree(endpoint, ignore_errors = True)
    except:
        return False

    return True


def _put(endpoint, message):
    msg_queue = f"{_ROOT}/{endpoint}/queue"

    return queue.put(msg_queue, message)


def _get(endpoint, timeout = -1):
    msg_queue = f"{_ROOT}/{endpoint}/queue"

    return queue.get(msg_queue, timeout)


def send(source, destination, data):
    """Send a message to an endpoint."""

    message = msg.new(source, destination, data)

    if not message:
        return False

    return _put(destination, message)


def recv(endpoint, timeout = -1):
    """Receive a message on the specified endpoint."""

    start = int(time.time())

    while True:
        remaining = timeout

        if timeout > 0:
            now = int(time.time())
            elapsed = now - start
            remaining = timeout - elapsed

            if remaining < 0:
                remaining = 0

        message = _get(endpoint, remaining)

        if message:
            return message

        if remaining == 0:
            break

    return None


def _topic_create(topic):
    try:
        os.mkdir(f"{_PUBSUB_ROOT}/{topic}")
    except:
        return False

    return True


def _topic_get_subscribers(topic):
    topicdir = f"{_PUBSUB_ROOT}/{topic}"
    subscribers = []

    for sub in os.listdir(topicdir):
        if not os.path.islink(f"{topicdir}/{sub}"):
            continue
        subscribers += [ sub.replace("_", "/") ]

    return subscribers


def _topic_subscribe(endpoint, topic):
    topicdir = f"{_PUBSUB_ROOT}/{topic}"
    subscription_name = endpoint.replace("/", "_")
    subscription = f"{topicdir}/{subscription_name}"
    subscription_addr = f"{_ROOT}/{endpoint}/subscriptions/{topic}"

    try:
        os.symlink(endpoint, subscription)
    except FileExistsError:
        # Already subscribed. This is not an error.
        pass
    except:
        return False

    try:
        os.symlink(topicdir, subscription_addr)
    except FileExistsError:
        # Already subscribed. This is not an error.
        pass
    except:
        shutil.rmtree(subscription, ignore_errors = True)
        return False

    return True


def publish(endpoint, topic, message):
    """Publish a message on a topic."""

    if not _topic_create(topic):
        return False

    for subscriber in _topic_get_subscribers(topic):
        send(endpoint, subscriber, message)

    return True
