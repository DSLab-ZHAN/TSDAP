#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   files.py
@Time    :   2024/10/31 03:03:43
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   Provides some useful functions of file or directory
'''


import os


def get_file_folder_size(file_or_folder_path: str) -> int:
    total_size = 0

    if not os.path.exists(file_or_folder_path):
        return total_size

    if os.path.isfile(file_or_folder_path):
        total_size = os.path.getsize(file_or_folder_path)

        return total_size

    if os.path.isdir(file_or_folder_path):
        sub_entries = os.scandir(file_or_folder_path)

        for sub_entry in sub_entries:
            sub_entry_fullpath = os.path.join(file_or_folder_path, sub_entry.name)

            if sub_entry.is_dir():
                sub_folder_size = get_file_folder_size(sub_entry_fullpath)
                total_size += sub_folder_size

            elif sub_entry.is_file():
                sub_file_size = os.path.getsize(sub_entry_fullpath)
                total_size += sub_file_size

        return total_size


def covert_size_to_str(size_bytes: int) -> str:
    if (size_bytes < 0):
        raise ValueError("Size must be a non-negative integer.")

    units = ['B', 'KB', 'MB', 'GB']
    threshold = 1024.00

    for unit in units:
        if (size_bytes < threshold):
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= threshold

    return f"{size_bytes:.2f} TB"


def is_file_exists(file_path: str):
    return os.path.exists(file_path)
