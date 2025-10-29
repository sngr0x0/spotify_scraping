from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import pandas as pd
from argparse import ArgumentParser


def scrape(playlist_url: str) -> tuple[set, str]:
    """
    Scrapes songs info from spotify.com and return a list of unique songs metadata including:
        1. Artist Name
        2. Duration
        3. Song Name
        4. Album
    
    Parameters
    ----------
    playlist_url:   str
        the url of the playlist to scrape
    
    Returns
    -------
    tuple[set, str]
        A tuple containing the set of songs metadata at index 0 and the playlist id at index 1
    """
    service = Service()
    driver = webdriver.Chrome(service=service)
    playlist_id = playlist_url.split('/')[-1]
    driver.get(playlist_url)
    sleep(2)
    # This sleep is important to wait until everything loads cuz if you did the magical click and some new element pops up,
    # ,its effect is gone and you need to click it again.

    driver.implicitly_wait(10)
    actions = ActionChains(driver)

    # This click enables me to scroll with "PAGE_DOWN"
    scrolling_div = driver.find_element(By.XPATH, '//*[@id="main-view"]/div/div[2]/div[1]/div/main/section/div[2]/div[2]/div[1]/div')
    scrolling_div.click()

    song_info = set()
    equal_length_timeout = 0
    while True:
        set_old_length = len(song_info)

        song_info_elements = driver.find_elements(
            By.CSS_SELECTOR,
            '.UhOLa3blz2xoAxM2vRwz.vzvX6wzymW8rwI4hkYo0'
            )
        # print(len(song_info_elements))

        for element in song_info_elements:
            song_info.add(element.text)
        
        set_new_length = len(song_info)
        if set_old_length == set_new_length:
            if equal_length_timeout == 3:
                break
            else:
                equal_length_timeout += 1
                actions.send_keys(Keys.PAGE_DOWN).perform()
                sleep(1)
        else:
            equal_length_timeout = 0
            actions.send_keys(Keys.PAGE_DOWN).perform()
            sleep(1)
            actions.send_keys(Keys.PAGE_DOWN).perform()
            sleep(1)

    driver.quit()
    return song_info, playlist_id



def process_song_info(song_info_set: set, playlist_id: str) -> str:
    """
    Process songs' metadata and make them ready to be stored in a dataframe, and then stored in a csv file

    Parameters
    ----------
    song_info_set:  set
        the set returned from scrape() function
    playlist_id:   str
        the id of the scraped playlist; it's also returned by scrape() function
    
    Returns
    -------
    str
        the path of the csv file where processed clean playlist's data is stored.
    """
    song_info_list = list(song_info_set) # converting to a list cuz sets aren't indexed
    for idx in range(len(song_info_list)):
        current_song_info = song_info_list[idx].split('\n')
        current_song_info = [item for item in current_song_info if not item.isdigit() and len(item) > 1]
        song_info_list[idx] = current_song_info

    df = pd.DataFrame(song_info_list, columns=['Song Name', 'Artist(s)', 'Album', 'Duration'])
    # I need IANA timezone
    csv_output_path = (__file__.split('.')[0]+
                    f"_id_{playlist_id}_time_{str(pd.Timestamp.now(tz='Africa/Cairo')).split('+')[0].replace(':','-').replace(' ', '_')}"
                    +'.csv')
    df.to_csv(csv_output_path, index=False)
    return csv_output_path

if __name__ == '__main__':
    # Creating a parser
    parser = ArgumentParser(
        description=(
            "This script scrapes songs from spotify playlists and their information.\n"
            "Scraped information includes:\n"
            "1. Song Title\n"
            "2. Artist\n"
            "3. Album\n"
            "4. Duration\n"
        ),
        epilog=(
            "Usage Example:\n"
            "playlist_scraper.py --playlist https://open.spotify.com/playlist/<palylist_id>"
        )
    )

    parser.add_argument(
        "--playlist",
        required= True,
        help= "Playlist to scrape.",
        metavar= "https://open.spotify.com/playlist/<playlist_id>"
        )
    args = parser.parse_args()

    playlist_url = args.playlist
    # playlist_url = 'https://open.spotify.com/playlist/28gL1DIuNrVnPhduZpELC1' long playlist for testing
    # playlist_url = 'https://open.spotify.com/playlist/1ziehylRaWn9NilHjTMf30' small playlist for testing
    song_info_set, playlist_id = scrape(playlist_url)
    csv_output_path = process_song_info(song_info_set, playlist_id)
    if csv_output_path:
        print("Playlist scraped successfully!")
        print(f"Path: {csv_output_path}")