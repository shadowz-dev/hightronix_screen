import os
import sys
import logging
import argparse

from typing import Dict
from dotenv import load_dotenv
load_dotenv()

class ConfigManager:

    APPLICATION_NAME = "Hightronix Screen"
    DEFAULT_PORT = 5000
    VERSION_FILE = 'version.txt'

    def __init__(self, replacers: Dict):
        self._replacers = replacers
        self._CONFIG = {
            'application_name': self.APPLICATION_NAME,
            'version': None,
            'demo': False,
            'external_storage_mountpoint': '%application_dir%/var/run/storage',
            'port': self.DEFAULT_PORT,
            'bind': '0.0.0.0',
            'debug': False,
            'log_file': None,
            'log_level': 'INFO',
            'log_stdout': True,
            'secret_key': 'ANY_SECRET_KEY_HERE',
        }

        self.load_version()
        self.load_from_env()
        self.load_from_args()

        self._CONFIG['port'] = self._CONFIG['port'] if self._CONFIG['port'] else self.DEFAULT_PORT

        if self.map().get('debug'):
            logging.debug(self._CONFIG)

        self.apply_replacers()

    def map(self) -> dict:
        return self._CONFIG

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="Hightronix Screen")
        parser.add_argument('--debug', '-d', default=self._CONFIG['debug'], help='Debug mode')
        parser.add_argument('--port', '-p', default=self._CONFIG['port'], help='Application port')
        parser.add_argument('--bind', '-b', default=self._CONFIG['bind'], help='Application bind address')
        parser.add_argument('--secret-key', '-s', default=self._CONFIG['secret_key'], help='Application secret key (any random string)')
        parser.add_argument('--log-file', '-lf', default=self._CONFIG['log_file'], help='Log File path')
        parser.add_argument('--log-level', '-ll', default=self._CONFIG['log_level'], help='Log Level')
        parser.add_argument('--log-stdout', '-ls', default=self._CONFIG['log_stdout'], action='store_true', help='Log to standard output')
        parser.add_argument('--demo', '-o', default=self._CONFIG['demo'], help='Demo mode to showcase Hightronix Screen in a sandbox')
        parser.add_argument('--external-storage-mountpoint', '-e', default=self._CONFIG['external_storage_mountpoint'], help='Mountpoint directory of external storage')
        parser.add_argument('--version', '-v', default=None, action='store_true', help='Get version number')

        return parser.parse_args()

    def load_version(self) -> str:
        with open(self.VERSION_FILE, 'r') as file:
            self._CONFIG['version'] = file.read()

    def load_from_args(self) -> None:
        args = self.parse_arguments()

        if args.debug:
            self._CONFIG['debug'] = args.debug
        if args.demo:
            self._CONFIG['demo'] = args.demo
        if args.external_storage_mountpoint:
            self._CONFIG['external_storage_mountpoint'] = args.external_storage_mountpoint
        if args.log_file:
            self._CONFIG['log_file'] = args.log_file
        if args.secret_key:
            self._CONFIG['secret_key'] = args.secret_key
        if args.log_level:
            self._CONFIG['log_level'] = args.log_level
        if args.log_stdout:
            self._CONFIG['log_stdout'] = args.log_stdout
        if args.version:
            print("{} version v{} ()".format(self.APPLICATION_NAME, self._CONFIG['version']))
            sys.exit(0)

    def load_from_env(self) -> None:
        for key in self._CONFIG:
            if key.upper() in os.environ:
                value = os.environ[key.upper()]
                if value.lower() == 'false' or value == '0' or value == '':
                    value = False
                elif value.lower() == 'true' or value == '1':
                    value = True
                self._CONFIG[key.lower()] = value
                logging.info(f"Env var {key} has been found")

    def apply_replacers(self):
        for key, value in self._CONFIG.items():
            if isinstance(value, str):
                for replace_key, replace_value in self._replacers.items():
                    self._CONFIG[key] = value.replace("%{}%".format(replace_key), replace_value)
