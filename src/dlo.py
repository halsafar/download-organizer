#!/usr/bin/env python
import argparse
import os
import json
import logging
import imp
import traceback

import PTN
from lockfile import LockFile, LockTimeout


# LOCK FILE
LOCK_FILE_PATH = "/tmp/dlo.lock.pid"


class DownloadOrganizer(object):
    def __init__(self, options, config_file):
        """
        Construct.
        :param options:
        :param config_file:
        """
        self._options = options
        self._config_file = config_file
        self._config = self._importConfig()

    def _importConfig(self):
        """
        Dynamically import config file for now as python code
        :return:
        """
        def importSource(name, source_file):
            """
            Import source from a file.
            :param name:
            :param source_file:
            :return:
            """
            logging.debug('Trying to load "%s" as "%s"' % (source_file, name))

            imp.acquire_lock()
            try:
                module = imp.load_source(name, source_file)
            except Exception as e:
                logging.error('Scanning app "%s": failed: %s' % (source_file, str(e)))
                tb_str = traceback.format_exc()
                logging.error(tb_str)
                raise
            finally:
                imp.release_lock()

            logging.debug('Loaded app module "%s"' % module)

            return module

        loaded_module = importSource("DownloadOrganizerConfig", self._config_file)
        config = loaded_module.DownloadOrganizerConfig()
        logging.debug("Loaded config instance: %s" % config)
        return config

    def scan(self):
        """
        Build up a list of work items to process
        :return:
        """
        logging.info("SearchDirs: %s" % self._config.SEARCH_DIRS)
        for scan_dir in self._config.SEARCH_DIRS:
            logging.info("== SCANNING %s ==" % scan_dir)
            for root, subdirs, files in os.walk(scan_dir):
                for filename in files:
                    filename, file_extension = os.path.splitext(filename)
                    if file_extension in self._config.EXTENSIONS:
                        file_path = os.path.join(root, filename)
                        logging.debug("-[%s]" % file_path)
                        info = PTN.parse(filename)
                        logging.debug("%s: " % json.dumps(info, indent=4))


def parseArgs():
    # process args
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', '-dr',
                        help='Dry Run (echo commands)',
                        action='store_true')
    options = parser.parse_args()

    return options


def main():
    # setup logger
    logging.basicConfig(format='%(levelname)s:%(asctime)s:\t%(message)s', level=logging.DEBUG)

    # Create the lock file
    lock = LockFile(LOCK_FILE_PATH)

    try:
        # Lock file, prevent multiple runs, wait up to 5 seconds
        while not lock.i_am_locking():
            try:
                lock.acquire(timeout=5)
            except LockTimeout:
                logging.info("Could not acquire lock file...")
                return -1

        options = parseArgs()

        dlo = DownloadOrganizer(options, None)
        dlo.scan()

        return
    except KeyboardInterrupt as e:
        logging.info("User terminated!")
        return -1
    finally:
        # DELETE LOCK FILE
        if lock.is_locked() and lock.i_am_locking():
            lock.release()


if __name__ == "__main__":
    main()
