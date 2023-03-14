import argparse
import json
import os
import re
from collections import namedtuple
from datetime import datetime
from enum import auto, Enum

import dbusnotify
from bs4 import BeautifulSoup, Tag


__version__ = '0.1.1'


media_items = namedtuple("media_dirs", "parent files")

HOME_DIR = os.path.expanduser("~")

XSPF_HEAD = '<?xml version="1.0" encoding="UTF-8"?>'

MEDIA_EXTENSIONS = ['ape', 'flac', 'mp3', "ogg", "wma"]


def log_it(level='info', src_name=None, text=None):
    import logging

    logging.basicConfig(level=logging.DEBUG)
    logger_name = src_name if src_name else __name__
    log_writer = logging.getLogger(logger_name)

    if level == 'info':
        log_writer.info(text)
    elif level == 'error':
        log_writer.error(text)
    elif level == 'warning':
        log_writer.warning(text)
    else:
        log_writer.debug(text)


class Result(Enum):
    PROCESSING = auto()
    FILE_DOES_NOT_EXIST = auto()
    NO_EXTENSION = auto()
    CANNOT_EXTRACT_TITLE = auto()
    TITLE_EMPTY = auto()
    BOOK_NOT_FOUND = auto()
    UNABLE_TO_ADD_BOOK = auto()
    CONVERSION_FAILED = auto()
    CONVERSION_ABANDONED_PDF = auto()
    CONVERSION_SUCCESSFUL = auto()
    FORMAT_IN_DB = auto()
    UNABLE_TO_ADD_FORMAT = auto()
    PROCESSED = auto()
    UNKNOWN = auto()


class PlaylistHandler(object):
    """
    This class is dedicated to processing one book file at a time.
    Processing involves picking up the file from the designated directory,
    checking if it is in Calibre DB and if not adding it to Calibre and
    then converting it to mobi if the mobi format is not already in the DB.
    """
    def __init__(self, source_dir="~/temp", start_file="", out_file=""):
        self._start_file = None
        self._source_dir = None
        self._directories = None
        self._processed_path = None
        self._out_file = None

        self.source_dir = source_dir
        self.start_file = start_file
        self.out_file = out_file
        self.directories = self.list_directories()
        self.processed_path = os.path.join(os.getenv('HOME'), "temp")

    @property
    def start_file(self):
        return self._start_file

    @start_file.setter
    def start_file(self, in_file):
        self._start_file = in_file

    @property
    def out_file(self):
        return self._out_file

    @out_file.setter
    def out_file(self, in_file):
        self._out_file = in_file if in_file else os.path.join(os.getenv('HOME'), "temp", "all.xspf")

    @property
    def source_dir(self):
        return self._source_dir

    @source_dir.setter
    def source_dir(self, in_dir):
        self._source_dir = in_dir

    @property
    def directories(self):
        return self._directories

    @directories.setter
    def directories(self, in_dirs):
        self._directories = in_dirs if isinstance(in_dirs, tuple) else ("", list())

    @property
    def processed_path(self):
        return self._processed_path

    @processed_path.setter
    def processed_path(self, in_path):
        self._processed_path = in_path

    @staticmethod
    def is_subset(in_a, in_b):
        set_a = set(re.split(r'[:_. ,]+', in_a))
        set_b = set(re.split(r'[:_. ,]+', in_b))

        return set_a.issubset(set_b) or set_b.issubset(set_a)

    @staticmethod
    def _post_notification(in_summary="calibre_utils", in_description=""):
        icon_file = os.path.join(os.getcwd(), 'calibre-utils.png')
        dbusnotify.write(
            in_description,
            title=in_summary,
            icon=icon_file,  # On Windows .ico is required, on Linux - .png
        )

    def _notify(self, code=Result.UNKNOWN, alt_text=None):
        summary = "calibre-utils"

        notify_text = {
            Result.PROCESSING: f"playlist_generator: Processing  file {repr(self.start_file)} ...",
            Result.FILE_DOES_NOT_EXIST: f"The file {repr(self.start_file)} does not exist.",
            Result.PROCESSED:
                f"{repr(self.start_file)} is in Calibre and converted to mobi, moving it to {self.processed_path}",
        }

        if alt_text:
            self._post_notification(summary, alt_text)
            return

        if code not in notify_text:
            return

        self._post_notification(summary, notify_text[code])

    @staticmethod
    def has_media(abs_parent, dir_name):
        dir_path = os.path.join(abs_parent, dir_name)

        for curr_dir, sub_dirs, files in os.walk(dir_path):
            if not files:
                continue

            if next((file_name for file_name in files if str(file_name).split(".")[-1] in MEDIA_EXTENSIONS), []):
                return True

        return False

    def list_directories(self, in_dir=None):
        if not in_dir:
            in_dir = self.source_dir

        work_dirs = work_files = list()
        for curr_dir, sub_dirs, files in os.walk(in_dir):
            if curr_dir != in_dir:
                break

            work_dirs += [s_dir for s_dir in sub_dirs]

            # Get media files, but only from the top directory
            work_files = [s_file for s_file in files if s_file.split(".")[-1] in MEDIA_EXTENSIONS]

        out_dirs = media_items(
            parent=in_dir,
            files=sorted(work_files) + sorted([w_dir for w_dir in work_dirs if self.has_media(in_dir, w_dir)])
        )

        return out_dirs

    def list_dir_files(self, in_dir=None):
        if not in_dir:
            in_dir = self.source_dir

        work_list = list()
        for curr_dir, sub_dirs, files in os.walk(in_dir):
            if curr_dir != in_dir:
                break

            work_list += [s_file for s_file in files if s_file.split(".")[-1] in MEDIA_EXTENSIONS]

        return work_list

    @staticmethod
    def write_file(filename, file_data, dest_dir=None):
        cur_dir = os.getcwd()

        if not dest_dir:
            dest_dir = cur_dir + '/../out/'

        if not os.path.isdir(dest_dir):
            os.mkdir(dest_dir)

        filepath = os.path.join(dest_dir, filename)

        if isinstance(file_data, dict):
            with open(filepath, 'w') as out:
                out.write(json.dumps(file_data, indent=4, sort_keys=True, ensure_ascii=False))
        elif isinstance(file_data, str):
            with open(filepath, 'w') as out:
                out.write(file_data)
        else:
            with open(filepath, 'wb') as out:
                out.write(file_data)

        return True

    @staticmethod
    def read_file(filepath):
        try:
            with open(filepath, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"Missing: {filepath}")
            return ''

    @staticmethod
    def make_soup():
        soup = BeautifulSoup(XSPF_HEAD, "xml")
        playlist_tag = soup.new_tag(name="playlist")
        playlist_tag['xmlns'] = "http://xspf.org/ns/0/"
        playlist_tag['xmlns:vlc'] = "http://www.videolan.org/vlc/playlist/ns/0/"
        playlist_tag['version'] = "1"
        title_tag = soup.new_tag(name="title")
        title_tag.append("All")
        playlist_tag.insert(new_child=title_tag, position=0)
        playlist_tag.append(soup.new_tag(name="trackList"))
        soup.append(playlist_tag)

        return soup

    def get_soup(self):
        if not self.start_file:
            return self.make_soup()

        return BeautifulSoup(self.read_file(self.start_file), "xml")

    def get_vlc_node_music(self, in_soup):
        music_node = next(iter(in_soup.find_all(name="vlc:node", recursive=True, title="music")), None)

        if not music_node:
            return self.create_vlc_node_music(in_soup)

    @staticmethod
    def create_vlc_node_music(now_soup):
        result = now_soup.find_all(name="extension", recursive=True)
        result_tags = [res for res in result if isinstance(res, Tag)]

        try:
            extension_tag = result_tags[-1]
        except IndexError:
            extension_tag = None

        if not extension_tag:
            extension_tag = now_soup.new_tag(name="extension", application="http://www.videolan.org/vlc/playlist/0")
            now_soup.playlist.append(extension_tag)

        music_node_tag = now_soup.new_tag(name="vlc_node", title="music")
        extension_tag.append(music_node_tag)

        return music_node_tag

    @staticmethod
    def build_track(now_soup, dir_name, last_id):
        track_tag = now_soup.new_tag(name="track")
        location_tag = now_soup.new_tag(name="location")
        location_tag.append("file:///" + dir_name)
        extension_tag = now_soup.new_tag(name="extension", application="http://www.videolan.org/vlc/playlist/0")
        vlc_id_tag = now_soup.new_tag(name="vlc:id")
        last_id += 1
        vlc_id_tag.append(str(last_id))
        extension_tag.append(vlc_id_tag)
        track_tag.append(location_tag)
        track_tag.append(extension_tag)

        return track_tag, last_id

    @staticmethod
    def get_last_id(in_soup):
        tracklist = next(iter(in_soup.find_all(name="trackList", recursive=True, limit=1)), None)

        if not tracklist.contents:
            return -1

        return max([int(tag.text) for tag in in_soup.find_all(name="vlc:id", recursive=True) if isinstance(tag, Tag)])

    def build_playlist(self):
        soup = self.get_soup()
        tracklist = next(iter(soup.find_all(name="trackList", recursive=True, limit=1)), None)
        last_id = self.get_last_id(soup)
        music_node = self.get_vlc_node_music(soup)

        for ix, dir_name in enumerate(self.directories.files):
            encoded_dir = re.sub(r']', '%5D', re.sub(r'\[', '%5B', dir_name))
            new_track, last_id = self.build_track(soup, os.path.join(self.directories.parent, encoded_dir), last_id)
            tracklist.append(new_track)
            music_node.append(soup.new_tag(name="vlc:item", tid=f"{last_id}"))

        self._notify(alt_text=f"Playlist generated, contains {last_id} entries")
        return soup, last_id

    def save_playlist(self, in_soup):
        output_file = os.path.basename(self.out_file)
        output_path = next(iter(self.out_file.split(output_file)), "")

        self.write_file(output_file, str(in_soup), output_path)
        self._notify(alt_text=f"Playlist saved to {self.out_file}")


if __name__ == '__main__':
    start_time = datetime.now()
    parser = argparse.ArgumentParser(description="This program generates or updates an XSPF playlist by scanning a"
                                     "directory for subdirectories containing music files.")
    parser.add_argument("-d", "--directory", help="Full path to the directory from which to add tracks.",
                        type=str,
                        dest='source_dir',
                        default='/home/adam/Downloads/books/in-books',
                        required=False)
    parser.add_argument("-f", "--file", help="The name of the file to which to add tracks from the input directory.",
                        type=str,
                        dest='in_file',
                        default="",
                        required=False)
    parser.add_argument("-o", "--output_file", help="The path and name of the output file.",
                        type=str,
                        dest='out_file',
                        required=False)

    args = parser.parse_args()

    ph = PlaylistHandler(source_dir=args.source_dir, start_file=args.in_file, out_file=args.out_file)
    out_soup, count = ph.build_playlist()
    ph.save_playlist(out_soup)

    log_it(level="info",
           text=f"Generated a playlist with {count} items from file {args.in_file}, directory {args.source_dir}, "
           f"runtime={str(datetime.now() - start_time)}")

    exit(0)
