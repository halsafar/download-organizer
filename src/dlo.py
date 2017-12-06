#!/usr/bin/env python
import argparse
import os
import json
import logging
import imp
import traceback
from collections import defaultdict

import PTN
import re

import shutil
from lockfile import LockFile, LockTimeout


# LOCK FILE
LOCK_FILE_PATH = "/tmp/dlo.lock.pid"


class DownloadOrganizer(object):
    """

    """
    def __init__(self, options, config_file):
        """
        Construct.
        :param options:
        :param config_file:
        """
        self._options = options
        self._config_file = config_file
        self._config = self._importConfig()

        logging.info("Dry Run: %s" % (not self._options.run))

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
        workloads = defaultdict(list)
        ignored = []
        logging.info("SearchDirs: %s" % self._config.SEARCH_DIRS)
        for scan_dir in self._config.SEARCH_DIRS:
            logging.info("== SCANNING %s ==" % scan_dir)
            for root, subdirs, files in os.walk(scan_dir):
                for filename in files:
                    name, file_extension = os.path.splitext(filename)
                    if file_extension in self._config.EXTENSIONS:
                        file_path = os.path.join(root, filename)
                        logging.debug("-[%s]" % file_path)

                        matches = self._findMatches(file_path)
                        logging.debug("Matches: %s" % matches)
                        if not matches:
                            ignored.append(filename)
                            continue
                        if len(matches) > 1:
                            logging.error("Multiple destinations found for %s" % filename)
                            ignored.append(filename)
                            continue

                        workloads[file_path].append((filename, matches[0]))
                    else:
                        ignored.append(filename)

        for ignore_path in ignored:
            logging.info("Ignoring file: %s" % ignore_path)

        return workloads

    def process(self, workloads):
        """
        Iterate work loads.  Prevent double moves or overwriting.
        :param workloads:
        :return:
        """
        failed = []
        for file_path, matches in workloads.iteritems():
            if len(matches) > 1:
                logging.error("Multiple destinations found for %s" % file_path)
                failed.append(file_path)
                continue

            for filename, dest in matches:
                logging.debug("Processing %s, (%s, %s)" % (file_path, filename, dest.dir))

                info = PTN.parse(filename)
                logging.debug("%s: " % json.dumps(info, indent=4))
                show_title = info['title']
                # episode_num = info['episode']
                season_num = info['season']

                destination_path = self._determineDestinationPath(show_title, season_num, dest)
                full_dest_path = os.path.join(destination_path, filename)
                if os.path.exists(full_dest_path):
                    logging.error("%s already exists at destination, not moving.", full_dest_path)
                    failed.append(file_path)
                    continue

                logging.info("Moving %s -> %s" % (file_path, full_dest_path))

                if not self._options.run:
                    continue

                shutil.move(file_path, full_dest_path)

        for failed_path in failed:
            logging.info("Failed to move: %s" % failed_path)

    def _determineDestinationPath(self, show_title, season_num, dest):
        """
        Determine if already existing dir is using season 1 otherwise default to leading 0
        :param show_title:
        :param season_num:
        :param dest:
        :return:
        """
        destination_dir = "%s/Season %d/" % (show_title, season_num)
        destination_path = os.path.join(dest.dir, destination_dir)
        if not os.path.exists(destination_path):
            # try leading zero
            destination_dir = "%s/Season %02d/" % (show_title, season_num)
            destination_path = os.path.join(dest.dir, destination_dir)

        return destination_path

    def _findMatches(self, filename):
        """
        Iterate the
        :param filename:
        :return:
        """
        matches = []
        for tree_item in self._config.REGEX_LIST:
            for regs, dest in tree_item.iteritems():
                for regex in regs:
                    pattern = re.compile(regex.regex)
                    match = pattern.match(filename)
                    if match:
                        matches.append(dest)
        return matches


def parseArgs():
    """
    CLI Arguments
    :return:
    """
    # process args
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', '-r',
                        help='Run, default is Dry Run (echo commands)',
                        action='store_true',
                        default=False)
    parser.add_argument('config',
                        help='Config File to use',
                        type=argparse.FileType('r')
                        )
    parser.add_argument("-v", "--verbose",
                        help="Increase output verbosity",
                        action="store_true")

    options = parser.parse_args()

    return options


def main():
    """
    Entry Point
    :return:
    """
    # setup logger
    logging.basicConfig(format='%(levelname)s:%(asctime)s:\t%(message)s', level=logging.INFO)

    # Create the lock file
    lock = LockFile(LOCK_FILE_PATH)

    try:
        # Lock file, prevent multiple runs, wait up to 5 seconds
        while not lock.i_am_locking():
            try:
                lock.acquire(timeout=5)
            except LockTimeout:
                print "Could not acquire lock file..."
                return -1

        options = parseArgs()
        if not options.config:
            print "No config file specified"
            return

        if options.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        dlo = DownloadOrganizer(options, options.config.name)
        workkloads = dlo.scan()
        dlo.process(workkloads)

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
