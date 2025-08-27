import csv
import requests
from datetime import date
from html import escape

class Video:
    def __init__(self, watch_link, name, pub_time, title):
        self.watch_link = watch_link
        self.name = name
        self.pub_time = pub_time
        # Trim title at first '#' if present
        self.title = title if '#' not in title else title[:title.index('#')]

class YouTuber:
    def __init__(self, url_string, name, video_label):
        self.url_string = url_string
        self.name = name
        self.video_label = video_label

def get_all_videos(url_string, name):
    videos_begin = '"title":"Videos"'
    title_search = '"title":{"runs":[{"text":"'
    watch_search = '/watch?v='
    pub_time_search = '"publishedTimeText":{"simpleText":"'
    
    all_videos = []

    try:
        response = requests.get(url_string)
        response.encoding = 'utf-8'
        page_content = response.text
    except requests.RequestException as e:
        print(f"Error fetching URL {url_string}: {e}")
        return all_videos

    # Find the section starting with 'title":"Videos'
    start_index = page_content.find(videos_begin)
    rest_string = page_content[start_index:] if start_index >= 0 else page_content

    while True:
        watch_index_pos = rest_string.find(watch_search)
        title_index_pos = rest_string.find(title_search)
        if watch_index_pos < 0 or title_index_pos < 0:
            break

        # Extract watch link (11 chars after /watch?v=)
        watch_link = rest_string[watch_index_pos:watch_index_pos + len(watch_search) + 11]

        # Extract title text
        title_start = title_index_pos + len(title_search)
        title_end = rest_string.find('"', title_start)
        label_string = rest_string[title_start:title_end]

        # Extract publication time text
        pub_time_pos = rest_string.find(pub_time_search)
        pub_time_string = "Vor Unbekannt"
        if pub_time_pos >= 0:
            pub_time_start = pub_time_pos + len(pub_time_search)
            pub_time_end = rest_string.find('"', pub_time_start)
            pub_time_string = rest_string[pub_time_start:pub_time_end]

        # Move rest_string forward for next iteration
        rest_string = rest_string[watch_index_pos + len(watch_search) + 11:]

        watch_index_pos = rest_string.find(watch_search)
        rest_string = rest_string[watch_index_pos + len(watch_search) + 11:]

        link = "https://www.youtube.com" + watch_link
        # Remove "Vor " prefix from pub_time_string
        pub_time_clean = pub_time_string[4:] if pub_time_string.startswith("Vor ") else pub_time_string

        all_videos.append(Video(link, name, pub_time_clean, label_string))
        seen_links = set()

    return all_videos

def convert_to_table(videos, table_name):
    html = f'<h2>{escape(table_name)}</h2>\n<table border="1">\n'
    html += "<tr><th>#</th><th>Name</th><th>Published Time</th><th>Title</th></tr>\n"
    for i, video in enumerate(videos, start=1):
        html += "<tr>"
        html += f"<td>{i}</td>"
        html += f"<td>{escape(video.name)}</td>"
        html += f"<td>{escape(video.pub_time)}</td>"
        html += f'<td><a href="{escape(video.watch_link)}">{escape(video.title)}</a></td>'
        html += "</tr>\n"
    html += "</table>\n"
    return html

def main():
    input_file = "youtubers.csv"
    result_file = "youtubers_" + str(date.today()) + ".html"

    you_tubers = []
    try:
        with open(input_file, encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) >= 3 and row[2] == "1":
                    #print(f"link: {row[1]}")
                    you_tubers.append(YouTuber(row[0], row[1], row[2]))
    except FileNotFoundError:
        print(input_file + " file not found.")
        return

    first_videos = []
    all_youtuber_videos = []
    seen_old_titles = set()

    for yt in you_tubers:
        all_videos = get_all_videos(yt.url_string, yt.name)
        if not all_videos:
            continue
        # Add only if there is at least one video
        first_video = all_videos[0]
        first_videos.append(first_video)
        print(yt.name, ": ", first_video.title)

        # Process remaining videos carefully
        for video in all_videos[1:]:
            if video.title not in seen_old_titles:
                all_youtuber_videos.append(video)
                seen_old_titles.add(video.title)

    try:
        with open(result_file, "w", encoding="utf-8") as writer:
            writer.write("<html><head><meta charset='UTF-8'></head><body>\n")
            writer.write(convert_to_table(first_videos, "New Videos"))
            writer.write(convert_to_table(all_youtuber_videos, "Old Videos"))
            writer.write("</body></html>\n")
    except IOError as e:
        print(f"Error writing to " + result_file + ": {e}")

if __name__ == "__main__":
    main()
