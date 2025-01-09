#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   console.py
@Time    :   2024/10/23 20:43:48
@Author  :   MuliMuri
@Version :   1.0
@Desc    :   Read-Eval-Print Console
'''


import argparse
import cmd
import os
import shlex

from runtime import RuntimeContext as ctx
from spider import SpiderManager


spider_manager: SpiderManager | None = None


class MainConsole(cmd.Cmd):
    prompt = "[TSDAP] > "

    def __init__(self) -> None:
        super().__init__("tab", None, None)
        global spider_manager

        self.spider_console = SpiderConsole()
        spider_manager = ctx.process_get_instance("SpiderManager")

    def cmdloop(self, intro=None):
        while True:
            try:
                return super().cmdloop(intro)
            except KeyboardInterrupt:
                print()
                self.do_exit()

    def do_spider(self, *args):
        self.spider_console.onecmd(*args)

    def complete_spider(self, text, line, begidx, endidx):
        spider_commands = [cmd[3:] for cmd in dir(self.spider_console) if cmd.startswith("do_")]
        if not text:
            return spider_commands
        else:
            return [cmd for cmd in spider_commands if cmd.startswith(text)]

    def help_spider(self):
        pass

    def do_clear(self, arg):
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def do_exit(self, *args):
        code = input("Are you sure to exit? Y/n: ")
        if (code in ['y', 'Y']):
            spider_manager.safety_exit()
            ctx.unload()
            exit()  # TODO: Redo exit, safety exit.

    def postcmd(self, stop: bool, line: str) -> bool:
        self.lastcmd = ''
        return super().postcmd(stop, line)


class SpiderConsole(cmd.Cmd):
    run_parser = argparse.ArgumentParser()
    run_parser.add_argument('--name', type=str, default=None,
                            help="Appoint a name to container.")
    run_parser.add_argument('--entry', type=str, default=None,
                            help="Appoint entry file.")
    run_parser.add_argument('-d', '--daemon', action='store_true', default=None,
                            help="Run in daemon mode.")
    run_parser.add_argument('-e', '--env', action='append', default=[],
                            help="Set environment variable in the format key=value.")
    run_parser.add_argument('--cron', type=str, default=None,
                            help="Configure the spider to start at a scheduled time, using the cron format string.")
    run_parser.add_argument('pkg_name_tag', type=str,
                            help="Specify name and tag in the format name:tag.")

    ps_parser = argparse.ArgumentParser()
    ps_parser.add_argument('-a', '--all', action='store_true', default=None,
                           help="List all spiders.")

    rm_parser = argparse.ArgumentParser()
    rm_parser.add_argument('-f', '--force', action='store_true', default=None,
                           help="Forced remove spider.")
    rm_parser.add_argument('spider_name_or_id', type=str,
                           help="Specify full name or partial ID.")

    def do_load(self, *args):
        pkg_filepath = args[0]
        spider_manager.load(pkg_filepath)

    def do_packages(self, *args):
        spider_manager.packages()

    def do_run(self, *args):
        try:
            args = self.run_parser.parse_args(shlex.split(args[0]))
        except SystemExit:
            return

        envs = {}
        for env in args.env:
            env: str
            key, value = env.split('=')
            envs[key] = value

        spider_manager.run(
            pkg_name_tag=args.pkg_name_tag,
            name=args.name,
            entry=args.entry,
            daemon=args.daemon,
            envs=envs,
            cron=args.cron
        )

    def do_ps(self, *args):
        try:
            args = self.ps_parser.parse_args(shlex.split(args[0]))
        except SystemExit:
            return

        spider_manager.ps(is_all=args.all)

    def do_start(self, *args):
        spider_name_or_id = args[0]
        spider_manager.start(spider_name_or_id)

    def do_stop(self, *args):
        spider_name_or_id = args[0]
        spider_manager.stop(spider_name_or_id)

    def do_restart(self, *args):
        spider_name_or_id = args[0]
        spider_manager.restart(spider_name_or_id)

    def do_rm(self, *args):
        try:
            args = self.rm_parser.parse_args(shlex.split(args[0]))
        except SystemExit:
            return

        spider_manager.rm(args.spider_name_or_id, is_force=args.force)

    def do_rmi(self, *args):
        pkg_name_tag = args[0]
        spider_manager.rmi(pkg_name_tag)

    def do_inspect(self, *args):
        pass

    def do_logs(self, *args):
        spider_name = args[0]
        spider_manager.logs(spider_name)

    def do_stats(self, *args):
        pass
