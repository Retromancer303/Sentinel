import unittest
from unittest.mock import patch

from app.db import repository


class TestRepository(unittest.TestCase):
    def test_save_chat_message_uses_redis_when_available(self):
        class FakeRedis:
            def __init__(self):
                self.store = {}

            def rpush(self, key, value):
                self.store.setdefault(key, []).append(value)

            def ltrim(self, key, start, end):
                items = self.store.get(key, [])
                # Redis ltrim is inclusive on both ends; Python slice is exclusive on end
                if end == -1:
                    self.store[key] = items[start:]
                else:
                    self.store[key] = items[start:end + 1]

            def lrange(self, key, start, end):
                items = self.store.get(key, [])
                if end == -1:
                    return items[start:]
                return items[start:end + 1]

        fake_client = FakeRedis()
        repository._in_memory_chat_store.clear()

        with patch("app.db.repository._get_redis_client", return_value=fake_client):
            repository.save_chat_message(None, "demo", "user", "Hello")
            repository.save_chat_message(None, "demo", "assistant", "Hi there")
            history = repository.get_recent_chat_history(None, "demo", limit=2)

        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["content"], "Hi there")


if __name__ == "__main__":
    unittest.main()
