"""Unit tests for BroadcastSystem in sse.py."""

import queue
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.dashboard.api.sse import BroadcastSystem


class TestBroadcastSystem:
    def test_broadcast_to_registered_client(self):
        system = BroadcastSystem()
        q = queue.Queue()
        system.register(q)
        system.broadcast("test_event", {"key": "value"})
        msg = q.get_nowait()
        assert msg["type"] == "test_event"
        assert msg["data"]["key"] == "value"

    def test_broadcast_to_multiple_clients(self):
        system = BroadcastSystem()
        q1, q2 = queue.Queue(), queue.Queue()
        system.register(q1)
        system.register(q2)
        system.broadcast("event", {"x": 1})
        assert q1.get_nowait()["type"] == "event"
        assert q2.get_nowait()["type"] == "event"

    def test_unregistered_client_gets_nothing(self):
        system = BroadcastSystem()
        q = queue.Queue()
        system.register(q)
        system.unregister(q)
        system.broadcast("event", {})
        assert q.empty()

    def test_no_clients_no_error(self):
        system = BroadcastSystem()
        system.broadcast("event", {})  # should not raise

    def test_isolated_instances(self):
        s1, s2 = BroadcastSystem(), BroadcastSystem()
        q1, q2 = queue.Queue(), queue.Queue()
        s1.register(q1)
        s2.register(q2)
        s1.broadcast("from_s1", {})
        assert q2.empty()
        assert not q1.empty()

    def test_unregister_nonexistent_client_no_error(self):
        system = BroadcastSystem()
        q = queue.Queue()
        system.unregister(q)  # should not raise

    def test_full_queue_client_removed(self):
        system = BroadcastSystem()
        q = queue.Queue(maxsize=1)
        system.register(q)
        # Fill the queue
        system.broadcast("event", {"n": 1})
        # Second broadcast should silently drop the dead client
        system.broadcast("event", {"n": 2})
        assert len(system._clients) == 0

    def test_broadcast_message_structure(self):
        system = BroadcastSystem()
        q = queue.Queue()
        system.register(q)
        system.broadcast("my_type", {"foo": "bar", "num": 42})
        msg = q.get_nowait()
        assert set(msg.keys()) == {"type", "data"}
        assert msg["data"] == {"foo": "bar", "num": 42}
