import os
import csv
import collections
import pandas as pd
import Levenshtein as lev
from aiohttp import ClientSession


def get_dirs(path: str) -> list:
    """Get directories within given path
    :param path: Path to find directories
    :return: Returned directories
    """
    dirs = [d for d in os.listdir(path) if os.path.isdir(get_path(path, d)) and not d.startswith(('.', '_'))]
    return dirs


async def fetch_html(url: str, session: ClientSession, **kwargs) -> str:
    """GET request wrapper to fetch page HTML.
    :param url: Url path to fetch
    :param session:
    :param kwargs: Passed to session.request()
    :return : html text response
    """
    resp = await session.request(method="GET", url=url, **kwargs)
    resp.raise_for_status()
    print("Got response [%s] for URL: %s", resp.status, url)
    html = await resp.text()
    return html


def dict2csv(d: (list, dict), file_path: str) -> None:
    """Write list of dicts to csv file, where headers are dict keys
    :param d: Dict to be written
    :param file_path: Path to csv file
    """
    if isinstance(d, dict):
        d = [d]

    keys = d[0].keys()

    with open(file_path, "w", newline='') as csv_file:
        writer = csv.DictWriter(csv_file, keys)
        writer.writeheader()
        writer.writerows(d)


def csv2pd(file_path: str) -> pd.DataFrame:
    """Read csv to pandas data frame
    :param file_path: Path to csv file
    :return: Data frame of returned data
    """
    # TODO: proper formatting of data (read numbers as numbers etc)
    return pd.read_csv(file_path)


def get_csv_data(file_path: str) -> list:
    """Read csv data to list
    :param file_path: Path to csv file
    :return: List of returned data
    """
    with open(file_path, 'r') as input_file:
        reader = csv.DictReader(input_file)
        data = []
        for row in reader:
            data.append(row)

    return data


def get_path(*paths: str, base_path: str = ''):
    """Join arbitrary number of path segments, with delimiter based on operating system
    :param paths: Path segments to be joined
    :param base_path: Needed?
    :return: Full path
    """
    paths = [path for path in (base_path, *paths) if path]
    path = os.path.sep.join(paths)
    return path


def get_url(*segments: str, base_url: str = ''):
    """Join arbitrary number of url path segments
    :param segments: Path segments to be joined
    :param base_url: Main url path eg. Google.com
    :return: Full url path
    """
    segments = [segment for segment in (base_url, *segments) if segment]
    url = "/".join(segments)
    return url


def sum_dict_list(data, only_keys: (list, tuple) = None, omit_keys: (list, tuple) = None) -> dict:
    """Sum list of dicts to single dict
    :param data: List of dicts
    :param only_keys: Option to only sum certain keys, only these will be present in returned dict
    :param omit_keys: Option to omit certain keys, will not be present in returned dict
    :return d: Dict of summed data
    """
    # TODO: Bit naive, assumes all dicts are formatted the same
    d = {}
    for k, v in data[0].items():

        if isinstance(v, (int, float)):
            if (only_keys is not None and k not in only_keys) or (omit_keys is not None and k in omit_keys):
                continue

            d[k] = sum([d[k] for d in data])

    return d


def flatten_dict(d, parent_key: str = '', delimiter: str = '_') -> dict:
    """Recursively flatten multi-level dict
    :param d: Multi-level dict
    :param parent_key: Key from upper level in recursive chain
    :param delimiter: Delimiter to join keys
    :return: Single level (flattened) dict
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + delimiter + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten_dict(v, new_key, delimiter=delimiter).items())
        else:
            items.append((new_key, v))
    return dict(items)


def flatten_list(lst: list) -> list:
    """Recursively flatten multi-level list
    :param lst: Multi-level list
    :return flat: Single level (flattened) list
    """
    flat = []
    for item in lst:
        if isinstance(item, list):
            flat.extend(flatten_list(item))
        else:
            flat.append(item)

    return flat


def fuzzy_string_match(str1: str, comp: list, tol: float = 0.95) -> (str, float):
    """Finding closest match of string within list of strings
    :param str1: string to search for
    :param comp: list of strings to search within
    :param tol: tolerance of acceptable match, below which user is warned
    :return match: closest matching string within comparison list
            ratio: comparison ratio between str1 and matched string
    """

    if str1 == comp:
        # Start off with direct comparison
        match = str1
        match_ratio = 1.0
    else:
        # Compare with all using Levenshtein comparison
        ratio = [lev.ratio(str1.lower(), s.lower()) for s in comp]
        match_ratio = max(ratio)
        match = comp[ratio.index(match_ratio)]

        if match_ratio < tol:
            message = "Ratio: {:.2f} less than tolerance: {:.2f}, matched '{}' with '{}'"
            print(message.format(match_ratio, tol, str1, match))

    return match, match_ratio


def str2num(data):
    """Recursive function for converting various data types to floating point or integer
    Lazily skips data that cannot be converted
    :param data: Data to be converted, accepted types are str, list, tuple, dict
    :return: Converted data
    """
    # TODO: Accept more type inputs etc.
    # If data is iterable, loop and re-enter function with each item
    if isinstance(data, (list, tuple)):

        for i, p in enumerate(data):
            data[i] = str2num(p)

    elif isinstance(data, dict):

        for k, v in data.items():
            data[k] = str2num(v)

    # Manual type conversion test
    else:
        try:
            data = float(data) if '.' in data else int(data)
        except ValueError:
            pass

    return data


if __name__ == "__main__":
    """For testing purposes"""
