#!/usr/bin/env python
import argparse
import os
import json

import PTN
from lockfile import LockFile, LockTimeout


# LOCK FILE
LOCK_FILE_PATH = "/tmp/midgard.lock.pid"

# SRC Dir
walk_dir = "/storage/Torrents"

# Valid Extensions
EXTENSIONS = ['.mkv']


def prettyPrintInfo(info):
	pass

def main():
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

        # process args
        parser = argparse.ArgumentParser()
        parser.add_argument('--dry-run', '-dr',
                            help='Dry Run Rsync',
                            action='store_true')
        parser.add_argument('--test', '-t',
                            help='Show what commands will be run, ignore guards, ignore valid mounts',
                            action='store_true')

        options = parser.parse_args()

        # DO WORK & RETURN
        return_code = 0
        
        print "== SCANNING =="
        for root, subdirs, files in os.walk(walk_dir):
            for filename in files:
                filename, file_extension = os.path.splitext(filename)
                if file_extension in EXTENSIONS:
                    file_path = os.path.join(root, filename)
                    print "-[%s]" % file_path
                    info = PTN.parse(file_path)
                    print "%s: " % json.dumps(info, indent=4)

        return return_code
    except KeyboardInterrupt as e:
        print "User terminated!"
        return -1
    finally:
        # DELETE LOCK FILE
        if lock.is_locked() and lock.i_am_locking():
            lock.release()


if __name__ == "__main__":
    main()
