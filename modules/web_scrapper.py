"""
Scraps the steam community page for item price history
Save it as json to use in other modules
"""
import requests
from bs4 import BeautifulSoup
from datetime import date, datetime
import json
import os


TEAM_FORTRESS_KEY_PAGE_URL = 'https://steamcommunity.com/market/listings/440/Mann%20Co.%20Supply%20Crate%20Key'


def _month_as_number(month_name: str) -> int:
    """Little function to translate month names to numbers"""
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    month_dict = dict(zip(month_names, month_numbers))
    return month_dict[month_name]


class PageScrapper:
    """Call this class to scrap the item page and save it to the data folder
    It allows one file per day, and overwrites the last one if called more than once in a single day"""

    def __init__(self) -> None:
        page_content = self.__get_page()
        raw_data = self.__parse_page(page_content)
        data = self.__clean_raw_data(raw_data)
        self.__save_data(data)

    @staticmethod
    def __get_page() -> bytes:
        page_response = requests.get(TEAM_FORTRESS_KEY_PAGE_URL)
        return page_response.content

    @staticmethod
    def __parse_page(page_content: bytes) -> list:
        """The page contains a graph that displays the history of median sales prices by date
        We'll retrieve the argument given to the javascript function that draws this graph"""
        soup = BeautifulSoup(page_content, 'html.parser')
        javascript_texts = soup.find_all(type='text/javascript')
        info = javascript_texts[-1]  # It's the last one!

        # retrieving the argument
        left_split = info.string.rsplit('var line1=[[')
        right_split = left_split[1].rsplit(']];')
        graph_info_raw: str = right_split[0]
        graph_info_raw: list = graph_info_raw.split('],[')

        return graph_info_raw

    @staticmethod
    def __clean_raw_data(raw_data: list) -> list:
        """Now we have a list of strings, which one containing a median price and quantity sold in a given datetime
        It'd be nice to adjust it so that it becomes a nice and tidy list of dicts before we save it"""
        dataset: list = []
        dataset_row_model = {'datetime': str, 'mean_price': int, 'quantity': int}
        for item in raw_data:
            item = item.replace('"', '')
            time_info, price, quantity = item.split(',')
            dataset_row_model['quantity'] = int(quantity)
            dataset_row_model['mean_price'] = float(price)
            time_info = time_info.replace(': +0', '')
            month, day, year, hour = time_info.split()
            month = _month_as_number(month)
            time_info = datetime(int(year), month, int(day), hour=int(hour))
            dataset_row_model['datetime'] = time_info.isoformat()

            dataset.append(dataset_row_model)
            dataset_row_model = {'datetime': str, 'mean_price': int, 'quantity': int}

        return dataset

    @staticmethod
    def __save_data(dataset: list) -> None:
        """Saves dataset into json file"""
        today = date.today().isoformat()
        file_name = 'data_from_' + today
        file_path = os.path.join('data', file_name)
        with open(file_path, 'w') as file:
            json.dump(dataset, file, indent=4)


if __name__ == '__main__':
    print('Scrapping for price info fo today...')
    PageScrapper()
    print('Got info!')
