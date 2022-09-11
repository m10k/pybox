"""
pybox.uipc.msg - Toolbox uipc message implementation for Python
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

import time
import os
import base64
import json

_UIPC_VERSION = 1

def _encode(decoded):
    return base64.b64encode(decoded.encode("utf-8")).decode("utf-8")


def _decode(encoded):
    return base64.b64decode(encoded.encode("utf-8")).decode("utf-8")


def get(msg, field):
    """Get a field from a message."""

    msg_dict = json.loads(_decode(msg))
    return msg_dict[field]


def version_supported(msg):
    """Check if a message's version is supported."""

    return get(msg, "version") == _UIPC_VERSION


def new(source, destination, data):
    """Create a new UIPC message."""

    encoded_data = _encode(data)
    timestamp = int(time.time())
    user = os.getenv("USER")

    message = {
        "version": _UIPC_VERSION,
        "source": source,
        "destination": destination,
        "user": user,
        "timestamp": timestamp,
        "data": encoded_data
    }

    return _encode(json.dumps(message))


def get_version(msg):
    """Get a message's version."""

    return get(msg, "version")


def get_source(msg):
    """Get a message's source address."""

    return get(msg, "source")


def get_destination(msg):
    """Get a message's destination address."""

    return get(msg, "destination")


def get_user(msg):
    """Get a message's sender's name."""

    return get(msg, "user")


def get_timestamp(msg):
    """Get a message's timestamp."""

    return get(msg, "timestamp")


def get_data(msg):
    """Get a message's payload."""

    return _decode(get(msg, "data"))
