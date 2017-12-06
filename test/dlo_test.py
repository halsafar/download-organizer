import logging

from mock import MagicMock

from src.dlo import DownloadOrganizer


class TestDownloadOrganizer:
    def setup(self):
        logging.basicConfig(format='%(levelname)s:%(asctime)s:\t%(message)s', level=logging.DEBUG)

    def teardown(self):
        pass

    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def testDlo(self):
        options = MagicMock()
        options.dry_run = True

        config_file = './config.py'

        dlo = DownloadOrganizer(options, config_file)
        workloads = dlo.scan()
        dlo.process(workloads)
