from src.base_config import DownloadOrganizerBaseConfig, DownloadRegex, Destination


class DownloadOrganizerConfig(DownloadOrganizerBaseConfig):
    # Directories to search
    SEARCH_DIRS = [
        './fake_downloads'
    ]

    # Valid Extensions
    EXTENSIONS = ['.mkv']

    # Regex list
    REGEX_LIST = [
        {(DownloadRegex('.*Favorite.*'),
          DownloadRegex('.*Hated.*'),
          ): Destination('/foo/bar')},
    ]
