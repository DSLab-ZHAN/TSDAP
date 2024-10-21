#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   test_RWLock.py
@Time    :   2024/10/21 07:25:34
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   Test file of RWLock
'''


import threading
import time

from TSDAP.utils.RWLock import WritePriorityReadWriteLock


class TestRWLock():
    # Test normal reading and writing conditions
    def test_read_write_lock(self):
        lock = WritePriorityReadWriteLock()

        # Write
        assert lock.acquire_write()
        time.sleep(0.1)  # Simulate write operation
        lock.release_write()

        # Read
        assert lock.acquire_read()
        time.sleep(0.1)  # Simulate read operation
        lock.release_read()

    # Test concurrent access from multiple readers
    def test_multiple_readers(self):
        lock = WritePriorityReadWriteLock()
        results = []

        def reader(id):
            assert lock.acquire_read()
            time.sleep(0.1)  # Simulate read operation
            results.append(id)
            lock.release_read()

        threads = [threading.Thread(target=reader, args=(i,)) for i in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(results) == 5  # Ensure that all readers have successfully read it

    # Test writer priority
    def test_writer_priority(self):
        lock = WritePriorityReadWriteLock()
        write_results = []

        def writer(id):
            assert lock.acquire_write()
            time.sleep(0.1)  # Simulate write operation
            write_results.append(id)
            lock.release_write()

        def reader(id):
            time.sleep(0.05)  # Ensure that readers start after the writer
            assert lock.acquire_read()
            time.sleep(0.1)  # Simulate read operation
            lock.release_read()

        # Create a writer thread
        writer_thread = threading.Thread(target=writer, args=(1,))

        # Create multiple reader threads
        reader_threads = [threading.Thread(target=reader, args=(i,)) for i in range(5)]

        writer_thread.start()
        for thread in reader_threads:
            thread.start()

        writer_thread.join()
        for thread in reader_threads:
            thread.join()

        assert len(write_results) == 1  # Ensure that only one writer successfully writes

    # Test timeout situation
    def test_acquire_read_timeout(self):
        lock = WritePriorityReadWriteLock()

        assert lock.acquire_write()  # Acquire write lock first

        result = lock.acquire_read(timeout=0.1)  # Try to acquire read lock with timeout
        assert not result  # Should return False due to timeout

        lock.release_write()  # Release write lock

    def test_acquire_write_timeout(self):
        lock = WritePriorityReadWriteLock()

        assert lock.acquire_write()  # Acquire write lock first

        # Start a reader in a separate thread
        def reader():
            lock.acquire_read()
            lock.release_read()

        reader_thread = threading.Thread(target=reader)
        reader_thread.start()

        # Try to acquire write lock with timeout
        result = lock.acquire_write(timeout=0.1)
        assert not result  # Should return False due to timeout

        lock.release_write()  # Release write lock
        reader_thread.join()  # Ensure reader thread finishes
