#!/usr/bin/env python3
# areq.py

"""Asynchronously get links embedded in multiple pages' HMTL."""

import os
import asyncio
import logging
import re
import sys
import json
import pathlib
from aiohttp import ClientSession
from utils.gen import get_path, dict2csv, flatten_dict

logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("areq")
logging.getLogger("chardet.charsetprober").disabled = True

BASE_URL = 'https://understat.com/league'
JS_VARS = ("datesData", "playersData", "teamsData")
RE_STRING = r"{}\s*=\s*JSON.parse(.*?)\)"
OUT_FORMAT = 'csv'
HERE = pathlib.Path(__file__).parent


async def fetch_html(url: str, session: ClientSession, **kwargs) -> str:
    """GET request wrapper to fetch page HTML.
    kwargs are passed to `session.request()`.
    """

    resp = await session.request(method="GET", url=url, **kwargs)
    resp.raise_for_status()
    logger.info("Got response [%s] for URL: %s", resp.status, url)
    html = await resp.text()
    return html


async def parse(url: str, var, session: ClientSession, **kwargs):
    """Find HREFs in the HTML of `url`."""
    # TODO: MERGE WITH FETCH_HTML
    html = await fetch_html(url=url, session=session, **kwargs)

    re_var = re.compile(RE_STRING.format(var), flags=re.DOTALL)
    data = re_var.findall(html)
    data = var2dict(data)
    return data


async def write_one(url: str, var: str, path: str, **kwargs) -> None:
    """Write the found HREFs from `url` to `file`."""
    data = await parse(url, var, **kwargs)

    if not data:
        return None

    # Making variable name filename if no filename specified
    if '.' in path:
        full_path = path
        # Removing variable name from directory path
        path = os.path.sep.join(full_path.split(os.path.sep)[:-1])
    else:
        full_path = os.path.join(path, f"{var}.{OUT_FORMAT}")

    if not os.path.isdir(path):
        os.makedirs(path)

    if var == "teamsData":
        data = format_teams(data, path)

    out = []
    try:
        if isinstance(data, dict):
            data = [data]
        for row in data:
            out.append(flatten_dict(row))
    except Exception as e:
        print(e)

    await dict2csv(out, full_path)
    logger.info("Wrote results for source URL: %s", url)


async def bulk_crawl_and_write(urls: list, paths: list, js_vars: tuple, **kwargs) -> None:
    """Crawl & write concurrently to `file` for multiple `urls`."""
    async with ClientSession() as session:
        tasks = []
        for url, path in zip(urls, paths):
            for var in js_vars:
                tasks.append(
                    write_one(url=url, session=session, var=var, path=path, **kwargs)
                )
        await asyncio.gather(*tasks)


def format_teams(data, path):
    # TODO replace with analyse function?
    lst = []
    for _, val in data.items():
        lst.append(val)

    league = []
    for team in lst:
        p = os.path.join(path, team['title'].replace(" ", "_"))
        if not os.path.isdir(p):
            os.makedirs(p)

        hst = [flatten_dict(row) for row in team['history']]
        filename = f"team_data.{OUT_FORMAT}"
        dict2csv(hst, os.path.join(p, filename))

        try:
            rm = ['history']
            for key, val in hst[0].items():
                if isinstance(val, (int, float)):
                    team[key] = sum(item[key] for item in hst)
                else:
                    rm.append(key)

            for key in rm:
                team.pop(key, None)

            league.append(team)

        except Exception as e:
            print(e)

    return league


def get_urls(leagues: (list, int), years: (list, str)) -> list:
    # TODO: Replace with gen function
    if isinstance(leagues, str):
        leagues = [leagues]

    if isinstance(years, int):
        years = [years]

    url = []
    for league in leagues:
        for year in years:
            parts = (BASE_URL, league, str(year))
            url.append("/".join(parts))

    return url


def var2dict(data):
    """Function to parse javascript variable to dict format. Potentially specific to understat which uses json.parse and
    hex codes to generate data"""
    # Hack to get rid of brackets and leading apostrophe
    # Bigger hack to do this encoding nonsense
    # https://stackoverflow.com/questions/38763771/how-do-i-remove-double-back-slash-from-a-bytes-object
    formatted_data = json.loads(data[0][2:-1].encode().decode('unicode_escape').encode("raw_unicode_escape"))
    return formatted_data


def main():
    assert sys.version_info >= (3, 7), "Script requires Python 3.7+."

    leagues = ['EPL', 'La_liga']
    years = [2020, 2021]

    urls = get_urls(leagues, years)
    paths = []
    for league in leagues:
        for year in years:
            paths.append(get_path(league, str(year), base_path=BASE_URL))

    asyncio.run(bulk_crawl_and_write(urls=urls, paths=paths, js_vars=JS_VARS))


if __name__ == "__main__":
    main()
