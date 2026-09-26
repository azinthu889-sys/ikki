# -*- coding: utf-8 -*-
"""Production worker start guards (2026-09-26).

1. IKKI_SEED / IKKI_GFX_ALIAS are test-only: the production loop must refuse
   to start with either present (any value), so a forgotten A/B env can never
   pin every customer job to one seed.
2. Only one worker: a second process on this Mac must fail the flock, and a
   worker that another host is actively polling for must refuse -- because
   start-up calls /api/w/reclaim, which would requeue the other's running job.
"""
import os, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "worker"))
sys.path.insert(0, os.path.join(ROOT, "core"))
import run as W          # noqa: E402


class EnvGuard(unittest.TestCase):

    def test_refuses_seed(self):
        with self.assertRaises(SystemExit):
            W._guard_env({"IKKI_SEED": "j_x"})

    def test_refuses_alias_even_zero(self):
        with self.assertRaises(SystemExit):
            W._guard_env({"IKKI_GFX_ALIAS": "0"})

    def test_clean_env_passes(self):
        W._guard_env({"IKKI_API": "x", "IKKI_BIG": "/tmp"})


class LockGuard(unittest.TestCase):

    def test_second_holder_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "w.lock")
            fd = W._guard_lock(p)
            try:
                # a second open file description on the same path must fail
                import fcntl
                fd2 = os.open(p, os.O_RDWR)
                with self.assertRaises(OSError):
                    fcntl.flock(fd2, fcntl.LOCK_EX | fcntl.LOCK_NB)
                os.close(fd2)
                with self.assertRaises(SystemExit):
                    # simulate another process: drop our global, lock again
                    W._LOCK_FD = None
                    W._guard_lock(p)
            finally:
                os.close(fd)


class RemoteGuard(unittest.TestCase):

    def seq(self, *vals):
        it = iter(vals)
        return lambda: next(it)

    def test_live_other_worker_refused(self):
        with self.assertRaises(SystemExit):
            W._guard_remote(health=self.seq(2.0, 3.1), sleep=lambda s: None, poll=6)

    def test_just_killed_predecessor_passes(self):
        # first read sees the dead worker's last poll, second read has aged out
        W._guard_remote(health=self.seq(2.0, 17.0), sleep=lambda s: None, poll=6)

    def test_idle_passes_without_waiting(self):
        waited = []
        W._guard_remote(health=self.seq(40.0), sleep=waited.append, poll=6)
        self.assertEqual(waited, [])

    def test_api_down_does_not_block(self):
        def boom(): raise OSError("down")
        W._guard_remote(health=boom, sleep=lambda s: None, poll=6)


if __name__ == "__main__":
    unittest.main()
