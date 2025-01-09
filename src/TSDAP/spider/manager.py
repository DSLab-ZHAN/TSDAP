#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   manager.py
@Time    :   2024/10/22 00:28:05
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   Spider manager
'''


import importlib
import importlib.util
import json
import logging
import os
import time
import shutil
import subprocess
import zipfile

from datetime import datetime
from hashlib import md5
from multiprocessing import Manager, Process
from tabulate import tabulate
from time import sleep
from threading import Lock, Thread
from typing import Any, Dict, List

from database import SQLite
from utils.crontab import cron_to_timer
from utils.dockerstyle import generate_unique_docker_style_name, human_readable_time_difference
from utils.files import get_file_folder_size, covert_size_to_str, is_file_exists
from runtime import RuntimeContext as ctx

from .context import context_main
from .common import ContainerStatus, SpiderCodes, SpiderShares


class SpiderManager():
    def __init__(self) -> None:
        self.pkg_root_dir: str = ctx.multiprocess_get_global("Spiders.PACKAGE_ROOT_DIR")
        self.container_root_dir: str = ctx.multiprocess_get_global("Spiders.CONTAINER_ROOT_DIR")

        self.spider_manager_db = SQLite(
            os.path.join(
                ctx.process_get_global("Runtimes.DB_ROOT_DIR"),
                "spider"
            )
        )

        self.spider_contexts: Dict[str, Dict[str, Any]] = {}
        self.spider_contexts_lock = Lock()

        # Initialize database
        self.__init_database()

        # Initialize monitor thread
        self.monitor_thread = Thread(target=self.__monitor_contexts,
                                     name="spider_monitor",
                                     daemon=True)
        self.monitor_thread.start()

    def __monitor_contexts(self):
        while True:
            dead_contexts = []
            with self.spider_contexts_lock:
                for container_id, context in self.spider_contexts.items():
                    process: Process = context['process']
                    if (process.is_alive()):
                        continue

                    # Process dead
                    dead_contexts.append((container_id, context))

            # Deal dead processes
            for (container_id, context) in dead_contexts:
                shares: SpiderShares = context['shares']
                ret_code = shares.ret_code.get()
                status = ContainerStatus.TERMINATED

                # Start cron timer
                if (ret_code == SpiderCodes.STATUS_SUCCESS and not shares.is_daemon):
                    # Set cron timer
                    cron = context['cron']
                    timer = cron_to_timer(cron, self.__cron_task, args=(container_id,))
                    status = ContainerStatus.TIMER_WAITING
                    timer.start()
                else:
                    with self.spider_contexts_lock:
                        self.spider_contexts.pop(container_id)

                # Write to continaers database
                self.spider_manager_db.switch_database("containers")
                self.spider_manager_db.update(
                    "runtimes",
                    {
                        'Status': status.value,
                        'RetCode': ret_code
                    }, f"WHERE ID='{container_id}'")

                # Clean resources
                context['manager'].shutdown()

            sleep(0.5)  # Surrender CPU

    def __init_database(self):
        if (not self.spider_manager_db.is_database_exists("packages")
                and not self.spider_manager_db.is_database_exists("containers")):

            # Init Packages
            self.spider_manager_db.create_database("packages")
            self.spider_manager_db.switch_database("packages")
            self.spider_manager_db.create_table("infos", {
                'Name': "name",
                'Tag': "1.0",
                'ID': "CFCD208495D565EF66E7DFF9F98764DA",
                'Created': "2020-20-20",
                'Size': 1024,
                'Author': "author",
                'Desc': "description"
            }.items())
            self.spider_manager_db.create_table("runtimes", {
                'ID': "CFCD208495D565EF66E7DFF9F98764DA",
                'Entry': "entry_file",
                'Daemon': False,
                'Envs': "{}",
                "Dependencies": "[]"
            }.items())
            self.spider_manager_db.create_table("schedules", {
                'ID': "CFCD208495D565EF66E7DFF9F98764DA",
                'Cron': "0 0 * * * *"
            }.items())

            # Init Containers
            self.spider_manager_db.create_database("containers")
            self.spider_manager_db.switch_database("containers")
            self.spider_manager_db.create_table("infos", {
                'ID': "CFCD208495D565EF66E7DFF9F98764DA",
                'Package': "package",
                'Created': "2020-20-20",
                'Name': "name"
            }.items())
            self.spider_manager_db.create_table("runtimes", {
                'ID': "CFCD208495D565EF66E7DFF9F98764DA",
                'Status': 0,
                'RetCode': 0,
                'Entry': "entry_file",
                'Daemon': False,
                'Envs': "{}"
            }.items())
            self.spider_manager_db.create_table("schedules", {
                'ID': "CFCD208495D565EF66E7DFF9F98764DA",
                'Cron': "0 0 * * * *"
            }.items())

    def __install_modules(self, module_names: List[str]) -> None:
        for module_name in module_names:
            if (importlib.util.find_spec(module_name) is not None):
                continue

            subprocess.check_call(["python", "-m", "pip", "install", module_name])

    def __set_container_status(self, container_id: str, status: ContainerStatus):
        self.spider_manager_db.switch_database("containers")
        self.spider_manager_db.update("runtimes", {
            'Status': status.value
        }, f"WHERE ID='{container_id}'")

    def __cron_task(self, container_id: str):
        self.start(container_id)

    def safety_exit(self):
        self.spider_manager_db.switch_database("containers")
        column_names, results = self.spider_manager_db.select(
            "runtimes",
            f"WHERE Status!={ContainerStatus.TERMINATED}"
        )

        if (len(results) == 0):
            return

        container_id_index = column_names.index("ID")

        # Send a stop signal to all running spiders
        for container in results:
            container_id = container[container_id_index]

            context_combine = self.spider_contexts[container_id]

            spider_shares: SpiderShares
            spider_shares = context_combine['shares']

            spider_shares.is_stop_event.set()

        # Waiting for the spiders to stop
        while not self.spider_contexts:
            sleep(0.5)  # Surrender CPU

    def load(self, pkg_file_path: str) -> None:
        if (not is_file_exists(pkg_file_path)):
            print(f"Package '{pkg_file_path}' not found.")
            return

        with open(pkg_file_path, 'rb') as fp:
            pkg_id = md5(fp.readline()).hexdigest()

        pkg_dir = os.path.join(self.pkg_root_dir, pkg_id)

        # Check package has been loaded.
        if (os.path.isdir(pkg_dir)):
            logging.warning(f"Spider package: {pkg_file_path} has been loaded.")
            return

        # Create package directory and extract it.
        os.mkdir(pkg_dir)
        with zipfile.ZipFile(pkg_file_path) as file:
            file.extractall(pkg_dir)

        # Decoder package `compose.json` and store it.
        with open(os.path.join(pkg_dir, "compose.json"), 'rb') as fp:
            compose = json.load(fp)

        compose_infos = compose['infos']
        compose_runtimes = compose['runtimes']
        compose_schedule = compose['schedules']

        self.spider_manager_db.switch_database("packages")
        self.spider_manager_db.insert("infos", {
            'Name': compose_infos['name'],
            'Tag': compose_infos['tag'],
            'ID': pkg_id,
            'Created': datetime.fromtimestamp(
                os.path.getctime(pkg_file_path)
            ).strftime("%Y-%m-%d"),

            'Size': get_file_folder_size(pkg_dir),
            'Author': compose_infos['author'],
            'Desc': compose_infos['desc'],
        })
        self.spider_manager_db.insert("runtimes", {
            'ID': pkg_id,
            'Entry': compose_runtimes['entry'],
            'Daemon': compose_runtimes['daemon'],
            'Envs': json.dumps(compose_runtimes['envs']),
            'Dependencies': json.dumps(compose_runtimes['dependencies'])
        })
        self.spider_manager_db.insert("schedules", {
            'ID': pkg_id,
            'Cron': compose_schedule['cron']
        })

    def packages(self) -> List:
        self.spider_manager_db.switch_database("packages")
        column_names, results = self.spider_manager_db.select("infos")

        id_index = column_names.index("ID")
        size_index = column_names.index("Size")

        for i, result in enumerate(results):
            result = list(result)
            result[id_index] = result[id_index][:12]
            result[size_index] = covert_size_to_str(result[size_index])

            results[i] = result

        print(tabulate(
            results,
            tuple(map(str.upper, column_names)),
            tablefmt='plain',
            disable_numparse=True
        ))

    def run(self,
            pkg_name_tag: str,
            name: str | None = None,
            entry: str | None = None,
            daemon: bool | None = None,
            envs: Dict[str, str] | None = None,
            cron: str | None = None) -> bool:

        combine = pkg_name_tag.split(':')
        if (len(combine) != 2):
            print(f"Unresolvable spider package name '{pkg_name_tag}'.")
            return False

        pkg_name, pkg_tag = combine

        # Read infos table
        self.spider_manager_db.switch_database("packages")
        column_names, results = self.spider_manager_db.select("infos", f"WHERE Name='{pkg_name}' AND Tag='{pkg_tag}'")
        if (len(results) == 0):
            print(f"Unable to find package '{pkg_name_tag}' locally.")
            return False

        id_index = column_names.index("ID")
        pkg_id = results[0][id_index]

        # Read runtimes table
        column_names, results = self.spider_manager_db.select("runtimes", f"WHERE ID='{pkg_id}'")
        entry_index = column_names.index("Entry")
        daemon_index = column_names.index("Daemon")
        envs_index = column_names.index("Envs")
        dependencies_index = column_names.index("Dependencies")
        default_entry = results[0][entry_index]
        default_daemon = results[0][daemon_index]
        default_envs = json.loads(results[0][envs_index])
        dependencies = json.loads(results[0][dependencies_index])

        # Read schedules table
        column_names, results = self.spider_manager_db.select("schedules", f"WHERE ID='{pkg_id}'")
        cron_index = column_names.index("Cron")
        default_cron = results[0][cron_index]

        # Install modules
        self.__install_modules(dependencies)

        # Generate container id
        self.spider_manager_db.switch_database("containers")
        container_id = md5(bytes(str(time.time()), encoding='utf-8')).hexdigest()

        # Generate container created
        container_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Generate container name
        container_name = name
        if (len(self.spider_manager_db.select("infos", f"WHERE Name='{name}'")[1]) == 0):
            container_name = generate_unique_docker_style_name()

        # Determine container configuration
        # Entry
        container_entry = entry
        if (entry is None):
            container_entry = default_entry

        # Daemon
        container_daemon = daemon
        if (daemon is None):
            container_daemon = default_daemon

        # Envs
        container_envs = envs
        if (envs is None):
            container_envs = default_envs

        # Cron
        container_cron = cron
        if (cron is None):
            container_cron = default_cron

        # Write configuration in database
        self.spider_manager_db.insert("infos", {
            'ID': container_id,
            'Package': pkg_name_tag,
            'Created': container_created,
            'Name': container_name
        })
        self.spider_manager_db.insert("runtimes", {
            'ID': container_id,
            'Entry': container_entry,
            'Daemon': container_daemon,
            'Envs': json.dumps(container_envs),
        })
        self.spider_manager_db.insert("schedules", {
            'ID': container_id,
            'Cron': container_cron
        })

        # Create container root directory
        container_directory = os.path.join(
            self.container_root_dir,
            container_id
        )
        os.mkdir(container_directory)

        # Initialize container database
        os.mkdir(os.path.join(container_directory, "db"))

        # Copy package code into container
        shutil.copytree(
            os.path.join(self.pkg_root_dir, pkg_id),
            os.path.join(container_directory, container_name)
        )

        self.__set_container_status(container_id, ContainerStatus.CREATED)

        # Start container
        self.start(container_id)

        # Print container id like Docker
        print(container_id)

    def start(self, spider_name_or_id: str):
        self.spider_manager_db.switch_database("containers")

        # Read infos table
        column_names, results = self.spider_manager_db.select(
            "infos",
            f"WHERE ID LIKE '%{spider_name_or_id}%' OR Name='{spider_name_or_id}'"
        )

        if (len(results) == 0):
            print(f"Unable to find spider '{spider_name_or_id}' locally.")
            return

        container_id_index = column_names.index("ID")
        container_name_index = column_names.index("Name")

        container_id = results[0][container_id_index]
        container_name = results[0][container_name_index]

        # Read runtimes table
        column_names, results = self.spider_manager_db.select(
            "runtimes",
            f"WHERE ID='{container_id}'"
        )

        container_entry_index = column_names.index("Entry")
        container_daemon_index = column_names.index("Daemon")
        container_envs_index = column_names.index("Envs")

        container_entry = results[0][container_entry_index]
        container_daemon = results[0][container_daemon_index]
        container_envs = json.loads(results[0][container_envs_index])

        # Read schedules table
        column_names, results = self.spider_manager_db.select(
            "schedules",
            f"WHERE ID='{container_id}'"
        )

        container_cron_index = column_names.index("Cron")
        container_cron = results[0][container_cron_index]

        # Locate entry file full path
        entry_path = os.path.join(
            self.container_root_dir,
            container_id,
            container_name,
            f"{container_entry}.py"
        )
        db_path = os.path.join(
            self.container_root_dir,
            container_id,
            "db"
        )

        process_manager = Manager()
        spider_shares = SpiderShares(process_manager)
        spider_shares.is_daemon.set(container_daemon)
        spider_shares.spider_db_dir.set(db_path)

        process = Process(target=context_main,
                          name=f"spider_<{container_id}>_context",
                          args=(
                              entry_path,
                              container_envs,
                              ctx._multiprocess_globals,
                              spider_shares),
                          daemon=True
                          )

        with self.spider_contexts_lock:
            self.spider_contexts[container_id] = {
                'cron': container_cron,
                'manager': process_manager,
                'shares': spider_shares,
                'process': process,
            }

        process.start()

        self.__set_container_status(container_id, ContainerStatus.RUNNING)

    def stop(self, spider_name_or_id: str):
        self.spider_manager_db.switch_database("containers")

        # Read infos table
        column_names, results = self.spider_manager_db.select(
            "infos",
            f"WHERE ID LIKE '%{spider_name_or_id}%' OR Name='{spider_name_or_id}'"
        )

        if (len(results) == 0):
            print(f"Unable to find spider '{spider_name_or_id}' locally.")
            return

        container_id_index = column_names.index("ID")
        container_id = results[0][container_id_index]

        context_combine = self.spider_contexts[container_id]

        spider_shares: SpiderShares
        spider_shares = context_combine['shares']

        spider_shares.is_stop_event.set()

    def restart(self, spider_name_or_id: str):
        self.spider_manager_db.switch_database("containers")

        # Read infos table
        column_names, results = self.spider_manager_db.select(
            "infos",
            f"WHERE ID LIKE '%{spider_name_or_id}%' OR Name='{spider_name_or_id}'"
        )

        if (len(results) == 0):
            print(f"Unable to find spider '{spider_name_or_id}' locally.")
            return

        container_id_index = column_names.index("ID")
        container_id = results[0][container_id_index]

        # Read runtimes table
        column_names, results = self.spider_manager_db.select(
            "runtimes",
            f"WHERE ID='{container_id}'"
        )

        status_index = column_names.index("Status")
        status = ContainerStatus(results[0][status_index])

        if (status != ContainerStatus.TERMINATED):
            self.stop(spider_name_or_id)

        self.start(spider_name_or_id)

    def rm(self, spider_name_or_id: str, is_force: bool = False):
        self.spider_manager_db.switch_database("containers")

        # Read infos table
        column_names, results = self.spider_manager_db.select(
            "infos",
            f"WHERE ID LIKE '%{spider_name_or_id}%' OR Name='{spider_name_or_id}'"
        )

        if (len(results) == 0):
            print(f"Unable to find spider '{spider_name_or_id}' locally.")
            return

        container_id_index = column_names.index("ID")
        container_id = results[0][container_id_index]

        # Read runtimes table
        column_names, results = self.spider_manager_db.select(
            "runtimes",
            f"WHERE ID='{container_id}'"
        )

        status_index = column_names.index("Status")
        status = ContainerStatus(results[0][status_index])

        if (status != ContainerStatus.TERMINATED and not is_force):
            print("This spider is currently running, if you confirm to delete it, please use the '-f --force' parameter.")
            return

        # Remove infos table
        self.spider_manager_db.delete(
            "infos",
            f"WHERE ID='{container_id}'"
        )

        # Remove runtimes table
        self.spider_manager_db.delete(
            "runtimes",
            f"WHERE ID='{container_id}'"
        )

        # Remove schedules table
        self.spider_manager_db.delete(
            "schedules",
            f"WHERE ID='{container_id}'"
        )

        # Remove container folder and files
        container_directory = os.path.join(
            self.container_root_dir,
            container_id
        )
        shutil.rmtree(container_directory, ignore_errors=True)

    def rmi(self, pkg_name_tag: str):
        self.spider_manager_db.switch_database("packages")

        combine = pkg_name_tag.split(':')
        if (len(combine) != 2):
            print(f"Unresolvable spider package name '{pkg_name_tag}'.")
            return False

        pkg_name, pkg_tag = combine

        # Read infos table
        self.spider_manager_db.switch_database("packages")
        column_names, results = self.spider_manager_db.select("infos", f"WHERE Name='{pkg_name}' AND Tag='{pkg_tag}'")
        if (len(results) == 0):
            print(f"Unable to find package '{pkg_name_tag}' locally.")
            return False

        id_index = column_names.index("ID")
        pkg_id = results[0][id_index]

        # Remove package folder
        pkg_directory = os.path.join(
            self.pkg_root_dir,
            pkg_id
        )
        shutil.rmtree(pkg_directory, ignore_errors=True)

        # Remove infos table
        self.spider_manager_db.delete(
            "infos",
            f"WHERE Name='{pkg_name}' AND Tag='{pkg_tag}'"
        )

        # Remove runtimes table
        self.spider_manager_db.delete(
            "runtimes",
            f"WHERE ID='{pkg_id}'"
        )

        # Remove schedules table
        self.spider_manager_db.delete(
            "schedules",
            f"WHERE ID='{pkg_id}'"
        )

    def ps(self, is_all: bool = False) -> List:
        self.spider_manager_db.switch_database("containers")

        # Read join table
        column_names, results = self.spider_manager_db.select("infos", "JOIN runtimes ON infos.ID = runtimes.ID")
        join_list = [dict(zip(column_names, row)) for row in results]

        ps_list = []
        columns = ["Container ID", "Package", "Entry", "Created", "Status", "Names"]

        for item in join_list:
            if (item["Status"] == ContainerStatus.TERMINATED and not is_all):
                continue

            ps_list.append((
                item["ID"][:12],
                item["Package"],
                item["Entry"],
                human_readable_time_difference(datetime.strptime(item["Created"], "%Y-%m-%d %H:%M:%S")),

                ContainerStatus(item["Status"]).name
                if item["Status"] != ContainerStatus.TERMINATED
                else f"{ContainerStatus(item['Status']).name}({SpiderCodes(item['RetCode']).name})",

                item["Name"]
            ))

        print(tabulate(
            ps_list,
            tuple(map(str.upper, columns)),
            tablefmt='plain',
            disable_numparse=True
        ))

    def logs(self, spider_name_or_id: str) -> None:
        self.spider_manager_db.switch_database("containers")

        # Read infos table
        column_names, results = self.spider_manager_db.select(
            "infos",
            f"WHERE ID LIKE '%{spider_name_or_id}%' OR Name='{spider_name_or_id}'"
        )

        if (len(results) == 0):
            print(f"Unable to find spider '{spider_name_or_id}' locally.")
            return

        id_index = column_names.index("ID")
        container_id = results[0][id_index]

        # Read runtimes table
        column_names, results = self.spider_manager_db.select(
            "runtimes",
            f"WHERE ID='{container_id}'"
        )

        status_index = column_names.index("Status")
        entry_index = column_names.index("Entry")
        status = ContainerStatus(results[0][status_index])
        entry = results[0][entry_index]

        if (status == ContainerStatus.RUNNING):
            # By invoke to process
            with self.spider_contexts_lock:
                context_combine = self.spider_contexts[container_id]

            spider_shares: SpiderShares
            spider_shares = context_combine['shares']

            spider_shares.is_logs.set(True)
            while spider_shares.is_logs.get():
                time.sleep(0.5)
                continue

            print(spider_shares.logs.get())

        db_path = os.path.join(
            self.container_root_dir,
            container_id,
            "db"
        )

        spider_db = SQLite(db_path)
        spider_db.switch_database(entry)

        column_names, results = spider_db.select("logs")

        message_index = column_names.index("MESSAGE")
        for result in results:
            print(result[message_index])
