#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: launcher.py
# Project: unmanic-launcher
# File Created: Sunday, 13th March 2022 8:25:09 pm
# Author: Josh Sunnex (jsunnex@gmail.com)
# -----
# Last Modified: Thursday, 5th May 2022 10:27:52 pm
# Modified By: Josh.5 (jsunnex@gmail.com)
###
import os
import webbrowser

import psutil
import requests

from pystray import MenuItem as item
import pystray
from PIL import Image

from . import common

os.environ['PATH'] += ';' + common.ffmpeg_path


class UnmanicLauncher:

    def __init__(self):
        self.unmanic_service = None
        self.icon = None
        self.unmanic_proc = None
        self.other_procs = []

    @staticmethod
    def __terminate_proc_tree(proc: psutil.Process):
        """
        Terminate the process tree (including grandchildren).
        Processes that fail to stop with SIGTERM will be sent a SIGKILL.

        :param proc:
        :return:
        """
        try:
            children = proc.children(recursive=True)
            children.append(proc)
        except psutil.NoSuchProcess:
            return
        for p in children:
            try:
                p.terminate()
            except psutil.NoSuchProcess:
                pass
        gone, alive = psutil.wait_procs(children, timeout=3)
        for p in alive:
            try:
                p.kill()
            except psutil.NoSuchProcess:
                pass
        psutil.wait_procs(alive, timeout=3)

    @staticmethod
    def pause_all_workers():
        """Pauses all workers"""
        requests.post('http://localhost:8888/unmanic/api/v2/workers/worker/pause/all', json={}, timeout=1)

    @staticmethod
    def resume_all_workers():
        """Resumes all workers"""
        requests.post('http://localhost:8888/unmanic/api/v2/workers/worker/resume/all', json={}, timeout=1)

    @staticmethod
    def trigger_library_scanner():
        """Triggers the library scanner"""
        requests.post('http://localhost:8888/unmanic/api/v2/pending/rescan', json={}, timeout=1)

    @staticmethod
    def launch_browser():
        """Opens the Unmanic frontend in the browser"""
        webbrowser.open_new("http://localhost:8888")

    def display_updater(self):
        """Display the updater window"""
        # TODO: Run without the subprocess and fetch the result
        update_command = [common.python_exe, '-m', 'launcher', '--updater']
        proc, sp = common.exec_process(update_command)
        self.other_procs.append(proc)
        # TODO: If an update was run, restart unmanic
        # while not sp.poll() is not None:
        #     time.sleep(.1)
        # self.stop_unmanic()
        # self.start_unmanic()

    def display_about(self):
        """Display the updater window"""
        pass

    def start_unmanic(self):
        """Start the main Unmanic service"""
        if self.unmanic_proc is not None:
            # Unmanic is already running
            return
        try:
            # Ensure the module is installed
            import unmanic
            # Run Unmanic as a subprocess
            subprocess_command = [common.python_exe, '-m', 'unmanic']
            self.unmanic_proc, sp = common.exec_process(subprocess_command)
        except ModuleNotFoundError:
            # Unmanic is not yet installed
            # Install it...
            self.display_updater()

    def stop_unmanic(self):
        """Terminate the main Unmanic process"""
        # Terminate Unmanic
        if self.unmanic_proc is not None and self.unmanic_proc.is_running():
            self.__terminate_proc_tree(self.unmanic_proc)
        self.unmanic_proc = None

    def restart_unmanic(self):
        """Stop and restart the Unmanic process"""
        self.stop_unmanic()
        self.start_unmanic()

    def stop_other_processes(self):
        """Terminate all other processes that may still be running"""
        for proc in self.other_procs:
            self.__terminate_proc_tree(proc)

    def action_exit(self):
        self.icon.visible = False
        self.icon.stop()

    def create_icon_menu(self):
        return pystray.Menu(
            item('Start/Stop Unmanic', pystray.Menu(
                item('Start Unmanic', self.start_unmanic),
                item('Stop Unmanic', self.stop_unmanic),
                item('Restart Unmanic', self.restart_unmanic),
            )),
            item('Workers', pystray.Menu(
                item('Pause All Workers', self.pause_all_workers),
                item('Resume All Workers', self.resume_all_workers),
            )),
            item('Scan Libraries', self.trigger_library_scanner),
            pystray.Menu.SEPARATOR,
            item('Launch Browser', self.launch_browser),
            item('Update', self.display_updater),
            # item('About', self.display_about),
            pystray.Menu.SEPARATOR,
            item('Exit', self.action_exit)
        )

    def create_icon(self):
        # When installed, the icon will be up a level
        image = None
        if os.path.exists(os.path.join(common.module_root, 'assets', 'icon.ico')):
            # When running from this script
            image = Image.open(os.path.join(common.module_root, 'assets', 'icon.ico'))
        menu = self.create_icon_menu()
        self.icon = pystray.Icon("Unmanic", image, "Unmanic", menu)

    def run(self):
        # Create icon
        self.create_icon()
        # Start Unmanic
        self.start_unmanic()
        # Create tray icon
        self.icon.run()
        # Stop Unmanic
        self.stop_unmanic()
        # Stop other subprocesses
        self.stop_other_processes()


def main():
    launcher = UnmanicLauncher()
    launcher.run()
