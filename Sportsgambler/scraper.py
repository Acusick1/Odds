import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from gen import get_url

# RE_SPAN = re.compile(r">([a-z]*)<")
RE_SPAN = re.compile(r">(.*?)<")
BASE_URL = "https://www.sportsgambler.com/lineups/football"
LEAGUES = ("england-premier-league/", "france-ligue-1/")
OUT = "test.csv"
# TODO: Chrome version issues


def strip(driver):

    # TODO: Get date
    current_date = None

    # Get table containing matches
    table = driver.find_elements_by_class_name('table-row-loneups')
    h_a = ('lineups-home', 'lineups-away')

    count = 0
    h = []
    a = []
    for row in table:

        try:
            home = row.find_element_by_class_name(h_a[0])
            away = row.find_element_by_class_name(h_a[1])
            teams = [t.get_attribute('innerHTML') for t in row.find_elements_by_class_name('fxs-team')]
            forms = [f.get_attribute('innerHTML') for f in row.find_elements_by_class_name('lineups-toggle-formation')]

            home_players = get_players(home)
            away_players = get_players(away)

            h.append({'team': teams[0], 'formation': forms[0], 'players': home_players})
            a.append({'team': teams[1], 'formation': forms[1], 'players': away_players})

        except NoSuchElementException:

            count += 1
            if count == 5:
                break

    return h, a


def get_players(team):

    lines = team.find_elements_by_class_name('players-line')
    # TODO: Not very clean way of getting rid of player numbers, get regex to find names only
    players = [RE_SPAN.findall(line.get_attribute('innerHTML'))[1::2] for line in lines]

    return players


def main():
    web = get_url(LEAGUES[0], base_url=BASE_URL)
    # path = 'C:/Users/andre/Downloads/chromedriver_win32/chromedriver'  # introduce your file's path inside

    options = Options()
    # options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    driver = webdriver.Chrome(
        options=options,
        executable_path='C:/Users/andre/Downloads/chromedriver_win32/chromedriver.exe')

    driver.get(web)
    time.sleep(0.5)
    h, a = strip(driver)

    return h, a


if __name__ == '__main__':

    main()
