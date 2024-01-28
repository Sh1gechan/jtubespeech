import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
import json
import argparse
import sys
import os
import glob
from tqdm import tqdm


def get_video_info(video_id):
    """Get basic video information from YouTube."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    response = requests.get(url)
    if response.status_code != 200:
        return None

    # Parsing the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extracting the title
    title_tag = soup.find("meta", property="og:title")
    title = title_tag["content"] if title_tag else "No title found"

    # Attempting to extract channel name and channel ID
    channel_name, channel_id = None, None
    for script in soup.find_all("script"):
        if 'var ytInitialData =' in script.text:
            json_text = script.text.split(' = ')[1]
            json_text = json_text.rsplit(';', 1)[0]  # Removes the trailing semicolon

            try:
                data = json.loads(json_text)
                video_primary_info = data["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][0]["videoPrimaryInfoRenderer"]
                video_secondary_info = data["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][1]["videoSecondaryInfoRenderer"]

                # Extract channel name
                owner = video_secondary_info["owner"]["videoOwnerRenderer"]
                channel_name = owner["title"]["runs"][0]["text"]
                channel_id = owner["navigationEndpoint"]["browseEndpoint"]["browseId"]
            except (KeyError, IndexError, json.JSONDecodeError):
                pass  # Handle exceptions or log them as needed

    return {
        "video_id": video_id,
        "url": url,
        "title": title,
        "channel": channel_name,
        "channel_id": channel_id,
    }

def parse_args():
  parser = argparse.ArgumentParser(
    description="video_id_to_metadata_csv.py",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
  )
  parser.add_argument("lang",type=str, help="language code (ja, en, ...)")
  
  return parser.parse_args(sys.argv[1:])

if __name__ == "__main__":
    args = parse_args()

    # Ensure the directory structure exists or create it
    os.makedirs(f"meta_video/{args.lang}", exist_ok=True)

    # Find a .txt file in the specified directory
    txt_files = glob.glob(f"videoid/{args.lang}/*.txt")
    if not txt_files:
        print(f"No .txt files found in videoid/{args.lang}")
        sys.exit(1)

    filename = txt_files[0]  # Selects the first .txt file found
    try:
        with open(filename, "r", encoding="utf-8") as file:
            video_ids = [line.strip() for line in file]
    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
        sys.exit(1)

    videos_info = [get_video_info(video_id) for video_id in tqdm(video_ids) if video_id]

    videos_df = pd.DataFrame(videos_info)
    csv_filename = f"meta_video/{args.lang}/{args.lang}_metadata.csv"
    videos_df.to_csv(csv_filename, index=False)

    print(f"Saved {args.lang.upper()} video metadata to {csv_filename}.")