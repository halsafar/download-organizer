

class DownloadRegex(object):
    def __init__(self, regex):
        self.regex = regex


class Destination(object):
    def __init__(self, dest):
        self.dir = dest


class DownloadOrganizerBaseConfig(object):
    # Directories to search
    SEARCH_DIRS = None

    # Valid Extensions
    EXTENSIONS = None

    # Regex list
    REGEX_LIST = None

