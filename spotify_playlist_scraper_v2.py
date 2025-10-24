from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep, time
import pandas as pd
from argparse import ArgumentParser
import sys
import os

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


service = Service()
driver = webdriver.Chrome(service=service)

# playlist_url = 'https://open.spotify.com/playlist/28gL1DIuNrVnPhduZpELC1' long playlist for testing
# playlist_url = 'https://open.spotify.com/playlist/1ziehylRaWn9NilHjTMf30' small playlist for testing
playlist_url = args.playlist
playlist_id = playlist_url.split('/')[-1]
driver.get(playlist_url)
sleep(2)
# This sleep is important to wait until everything loads cuz if you did the magical click and some new element pops up,
# , its effect id gone and you need to click it again.

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
# print(song_info)
# print()
# print(len(song_info))

# We have to turn the set into a list to be able to use indexing.
song_info_list = list(song_info)
for idx in range(len(song_info_list)):
    song_info_list[idx] = song_info_list[idx].split('\n')
    current_song_info = song_info_list[idx]
    # After the split, song_info_list[idx] is now a list itself
    
    # for idx2 in range(len(current_song_info)): #NOTE this line is dangerous cuz I'm changing the size of the loop while looping over it.
    #     if len(current_song_info[idx2]) == 1: # if the length of a splitted item = 1, it's probably noise.
    #         current_song_info.pop(idx2)

    current_song_info = [item for item in current_song_info if not item.isdigit() and len(item) > 1]
    song_info_list[idx] = current_song_info
# print(song_info_list)

df = pd.DataFrame(song_info_list, columns=['Song Name', 'Artist(s)', 'Album', 'Duration'])
# I need IANA timezone
csv_output_path = (__file__.split('.')[0]+
                   f"_id_{playlist_id}_time_{str(pd.Timestamp.now(tz='Africa/Cairo')).split('+')[0].replace(':','-').replace(' ', '_')}"
                   +'.csv')
# It's really smart to end the name with time and not with playlist_id.
# Make it a general convention; time is always at the end of the name.
# This way, csv files with same playlist_id would be on top of each other instead of having files of different playlists
# next to each other; in other words, we're clustering by id rather than time here.
df.to_csv(csv_output_path, index=False)