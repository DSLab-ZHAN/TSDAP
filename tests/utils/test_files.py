#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   test_files.py
@Time    :   2024/11/04 14:57:20
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   Test file of files
'''


import pytest
from TSDAP.utils.files import covert_size_to_str, get_file_folder_size


class TestFiles():
    def test_covert_size_to_str_bytes(self):
        assert covert_size_to_str(500) == "500.00 B"

    def test_covert_size_to_str_kilobytes(self):
        assert covert_size_to_str(2048) == "2.00 KB"

    def test_covert_size_to_str_megabytes(self):
        assert covert_size_to_str(1048576) == "1.00 MB"

    def test_covert_size_to_str_gigabytes(self):
        assert covert_size_to_str(1073741824) == "1.00 GB"

    def test_covert_size_to_str_terabytes(self):
        assert covert_size_to_str(1099511627776) == "1.00 TB"

    def test_covert_size_to_str_negative_value(self):
        with pytest.raises(ValueError, match="Size must be a non-negative integer."):
            covert_size_to_str(-1)

    def test_get_file_folder_size_nonexistent_path(self):
        assert get_file_folder_size("nonexistent_path") == 0

    def test_get_file_folder_size_file(self, tmp_path):
        file = tmp_path / "test_file.txt"
        file.write_text("test content")
        assert get_file_folder_size(str(file)) == len("test content")

    def test_get_file_folder_size_empty_folder(self, tmp_path):
        assert get_file_folder_size(str(tmp_path)) == 0

    def test_get_file_folder_size_folder_with_files(self, tmp_path):
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")
        file2 = tmp_path / "file2.txt"
        file2.write_text("content2")
        expected_size = len("content1") + len("content2")
        assert get_file_folder_size(str(tmp_path)) == expected_size

    def test_get_file_folder_size_nested_folders(self, tmp_path):
        folder1 = tmp_path / "folder1"
        folder1.mkdir()
        file1 = folder1 / "file1.txt"
        file1.write_text("content1")
        folder2 = folder1 / "folder2"
        folder2.mkdir()
        file2 = folder2 / "file2.txt"
        file2.write_text("content2")
        expected_size = len("content1") + len("content2")
        assert get_file_folder_size(str(tmp_path)) == expected_size
