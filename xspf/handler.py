"""
This module contains code to generate an xspf playlist compatible with VLC
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from enum import auto, Enum
from typing import NamedTuple
import logging

from bs4 import BeautifulSoup, Tag
from dbus_notifier.notifysender import NotifySender


__version__ = '0.1.7'


HOME_DIR = os.path.expanduser("~")

XSPF_HEAD = '<?xml version="1.0" encoding="UTF-8"?>'

MEDIA_EXTENSIONS = ['ape', 'flac', 'mp3', "ogg", "wma"]


class MediaItems(NamedTuple):
    """
    This class represents a media item.
    """
    parent: str
    files: list


def log_it(level='info', src_name=None, text=None):
    """
    Logger function
    :param level: String specifying the log level
    :param src_name: String containing the name of the logging module
    :param text: A string containing the log message
    :return: void
    """

    logging.basicConfig(level=logging.DEBUG)
    logger_name = src_name if src_name else __name__
    log_writer = logging.getLogger(logger_name)

    do_log = {
        "info": log_writer.info,
        "error": log_writer.error,
        "warning": log_writer.warning,
    }

    do_log.get(level, log_writer.debug)(text)


class Result(Enum):
    """
    This class represents an enumeration of status values
    """
    PROCESSING = auto()
    FILE_DOES_NOT_EXIST = auto()
    PLAYLIST_GENERATED = auto()
    PLAYLIST_SAVED = auto()
    PROCESSED = auto()
    UNKNOWN = auto()


class PlaylistHandler:
    """
    This class either creates a new XSPF playlist or extends an existing one
    by adding track files.
    """
    def __init__(self, source_dir="~/temp", start_file="", out_file=""):
        self._start_file = None
        self._source_dir = None
        self._directories = None
        self._out_file = None
        self._notifier = None

        self.source_dir = source_dir
        self.start_file = start_file
        self.out_file = out_file
        self.directories = tuple()
        messages = {
            Result.PROCESSING: f"Processing  {repr(self.start_file)} to generate playlist ..." if self.start_file
            else "Starting to generate playlist ...",
            Result.PLAYLIST_GENERATED: "Playlist ready",
            Result.PROCESSED: f"Playlist saved in {self.out_file}"
        }

        self.notifier = NotifySender(title="xspf-gen", messages=messages)

    @property
    def start_file(self):  # pylint: disable=missing-function-docstring
        return self._start_file

    @start_file.setter
    def start_file(self, in_file):
        self._start_file = in_file

    @property
    def out_file(self):  # pylint: disable=missing-function-docstring
        return self._out_file

    @out_file.setter
    def out_file(self, in_file):
        self._out_file = in_file if in_file else os.path.join(os.getenv('HOME'), "temp", "all.xspf")

    @property
    def source_dir(self):  # pylint: disable=missing-function-docstring
        return self._source_dir

    @source_dir.setter
    def source_dir(self, in_dir):
        self._source_dir = in_dir

    @property
    def directories(self):  # pylint: disable=missing-function-docstring
        return self._directories

    @directories.setter
    def directories(self, in_dirs):
        self._directories = in_dirs if isinstance(in_dirs, tuple) else ("", [])

    @staticmethod
    def is_subset(in_a, in_b):
        """
        Check if one of the two strings is a subset of the other
        :param in_a: String to check
        :param in_b: String to Check
        :return: True if on of the strings is a subset of the other, otherwise False
        """
        set_a = set(re.split(r'[:_. ,]+', in_a))
        set_b = set(re.split(r'[:_. ,]+', in_b))

        return set_a.issubset(set_b) or set_b.issubset(set_a)

    @staticmethod
    def has_media(abs_parent, dir_name):
        """
        Check if a directory contains media files.
        :param abs_parent: Absolute to parent directory
        :param dir_name: Name of the directory to check
        :return: True if the directory contains media files, otherwise False
        """
        dir_path = str(os.path.join(abs_parent, dir_name))

        for curr_dir, sub_dirs, files in os.walk(dir_path):
            _ = curr_dir
            _ = sub_dirs

            if not files:
                continue

            if next((file_name for file_name in files if str(file_name).rsplit(".", maxsplit=1)[-1] in
                    MEDIA_EXTENSIONS), []):
                return True

        return False

    def list_directories(self, in_dir=None):
        """
        List directories with media files in them
        :param in_dir: Directory for which to produce the listing
        :return: An instance of MediaItems listing the directory and the media files in it
        """
        if not in_dir:
            in_dir = self.source_dir

        work_dirs = work_files = []
        for curr_dir, sub_dirs, files in os.walk(in_dir):
            if curr_dir != in_dir:
                break

            work_dirs += list(sub_dirs)
            # Get media files, but only from the top directory
            work_files = [s_file for s_file in files if s_file.split(".")[-1] in MEDIA_EXTENSIONS]

        out_dirs = MediaItems(
            parent=in_dir,
            files=sorted(work_files) + sorted([w_dir for w_dir in work_dirs if self.has_media(in_dir, w_dir)])
        )

        return out_dirs

    @staticmethod
    def write_file(filename, file_data, dest_dir=None):
        """
        Write file to disk.
        :param filename: Name of the file to use
        :param file_data: The file contents to use
        :param dest_dir: Directory where to put the file
        :return: Always True
        """
        cur_dir = os.getcwd()

        if not dest_dir:
            dest_dir = cur_dir + '/../out/'

        if not os.path.isdir(dest_dir):
            os.mkdir(dest_dir)

        filepath = os.path.join(dest_dir, filename)

        if isinstance(file_data, dict):
            with open(filepath, 'w', encoding="UTF-8") as out:
                out.write(json.dumps(file_data, indent=4, sort_keys=True, ensure_ascii=False))
        elif isinstance(file_data, str):
            with open(filepath, 'w', encoding="UTF-8") as out:
                out.write(file_data)
        else:
            with open(filepath, 'wb', encoding="UTF-8") as out:
                out.write(file_data)

        return True

    @staticmethod
    def read_file(filepath):
        """
        Read file at the file path
        :param filepath: The file path and name
        :return: The contents of the file as a string on success, otherwise an empty string
        """
        try:
            with open(filepath, 'r', encoding="UTF-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"Missing: {filepath}")
            return ''

    @staticmethod
    def make_soup():   # pylint: disable=missing-function-docstring
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

    def get_soup(self):  # pylint: disable=missing-function-docstring
        if not self.start_file:
            return self.make_soup()

        return BeautifulSoup(self.read_file(self.start_file), "xml")

    def get_vlc_node_music(self, in_soup):  # pylint: disable=missing-function-docstring
        music_node = next(iter(in_soup.find_all(name="vlc:node", recursive=True, title="music")), None)

        if not music_node:
            return self.create_vlc_node_music(in_soup)

        return music_node

    @staticmethod
    def create_vlc_node_music(now_soup):  # pylint: disable=missing-function-docstring
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
    def build_track(now_soup, dir_name, last_id):  # pylint: disable=missing-function-docstring
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
    def get_last_id(in_soup):  # pylint: disable=missing-function-docstring
        tracklist = next(iter(in_soup.find_all(name="trackList", recursive=True, limit=1)), None)

        if not tracklist.contents:
            return -1

        return max(
            int(tag.text) for tag in in_soup.find_all(name="vlc:id", recursive=True) if isinstance(tag, Tag)
        )

    def build_playlist(self):  # pylint: disable=missing-function-docstring
        self.notifier.notify(select_key=Result.PROCESSING)
        self.directories = self.list_directories()
        soup = self.get_soup()
        tracklist = next(iter(soup.find_all(name="trackList", recursive=True, limit=1)), None)
        last_id = self.get_last_id(soup)
        music_node = self.get_vlc_node_music(soup)

        for dir_name in self.directories.files:
            encoded_dir = dir_name.replace(']', '%5D').replace('[', '%5B')
            new_track, last_id = self.build_track(soup, os.path.join(self.directories.parent, encoded_dir), last_id)
            tracklist.append(new_track)
            music_node.append(soup.new_tag(name="vlc:item", tid=f"{last_id}"))

        # self.notifier.notify(select_key=Result.PLAYLIST_GENERATED)
        return soup, last_id

    def save_playlist(self, in_soup):  # pylint: disable=missing-function-docstring
        output_file = os.path.basename(self.out_file)
        output_path = next(iter(self.out_file.split(output_file)), "")

        self.write_file(output_file, str(in_soup), output_path)
        self.notifier.notify(select_key=Result.PROCESSED)


def main():  # pylint: disable=missing-function-docstring
    start_time = datetime.now()
    parser = argparse.ArgumentParser(description="This program generates or updates an XSPF playlist by scanning a"
                                     "directory for subdirectories containing music files.")
    parser.add_argument("-d", "--directory", help="Full path to the directory from which to add tracks.",
                        type=str,
                        dest='source_dir',
                        default='/home/adam/Downloads/books/in-books',
                        required=False)
    parser.add_argument("-f", "--file", help="The name of the file to which to add tracks from the input"
                        "directory.",
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

    input_file_str = f"file {args.in_file}, " if args.in_file else ""
    log_it(level="info",
           text=f"Generated a playlist with {count} items from {input_file_str}directory {args.source_dir}, "
           f"run time={str(datetime.now() - start_time)}")

    sys.exit(0)


if __name__ == '__main__':
    main()
