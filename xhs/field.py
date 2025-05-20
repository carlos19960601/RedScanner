from enum import Enum


class SearchNoteType(Enum):
    """search note type"""

    # default
    ALL = 0
    # only video
    VIDEO = 1
    # only image
    IMAGE = 2


class SearchSortType(Enum):
    """search sort type"""

    # default
    GENERAL = "general"
    # most popular
    MOST_POPULAR = "popularity_descending"
    # Latest
    LATEST = "time_descending"
