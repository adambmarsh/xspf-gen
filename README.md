# xspf-gen #

This is a utility program that creates a VLC-compatible XSPF playlist.
It can create one flat playlist or multiple playlists, one per music genre, with
the genre-specific playlists referenced by a top-level playlists.

The single flat playlist can be consumed by VLC and other media players, for example Audacious.
The multiple playlists can be used by VLC.

The program scans a user-specified directory, where subdirectories contain music files and creates <track> elements, 
one per sub-directory.

If an input file (a pre-existing playlist) is provided, the program adds the
music items to <tracklist> and adds and populates <vlc:node title="music"> under <extension
application="http://www.videolan.org/vlc/playlist/0">.

If <trackList> or <vlc:node title="music"> (or the parent element of <vlc:node title="music">) do not exist, they 
are created.

To build the per-genre playlists, the program scans the audio files by
default. This can take several minutes, depending on the size of the music
collection and whether it is held locally (faster access) or on the network
(slow). As an alternative, the program can retrieve the directory (album) and
genre information from a PostreSQL database, which is very fast -- the program
tries to access the database first, if that is unavailable, it reverts to the
default scan of the audio files. 

## Usage

Run as a Python 3 script in the terminal, specifying the command-line options as appropriate (details below). 

The Python script takes the following arguments:

* -c The full path and name of the per-genre playlist specification, a YAML file
    -- it shows the names (titles) of the genre-specific playlists and the
    genre(s) they should include 
* -d The full path and name of the directory from which to add tracks (parent directory, where subdirectory contain music 
    tracks)
* -e The full path and name of a file containing the details required to access
    the PostgreSQL database (host IP address, port number, DB name, user name, user password) 
* -f The full path and name of the file to extend (if not provided, a new playlist file is created)
* -o The full path and name of the file to which to save the new/updated flat
    playlist (defaults to /home/{user}/temp/all.xspf) or the name of the top-level
    playlist file which references each of the genre-specific playlists

Example with all the command-line parameters specified -- the program adds music
tracks to the structure in radio.xspf and saves the output as a flat playlist to all.xspf in the
temp directory. 
```
python $HOME/scripts/xspf-gen/main.py -f $HOME/Music/playlists/radio.xspf -d $HOME/lanmount/music -o $HOME/temp/all.xspf
```
Example with no input file -- the program creates a new playlist structe and adds music
tracks to it, then saves the output to all.xspf in the temp directory
```
python $HOME/scripts/xspf-gen/main.py -f $HOME/Music/playlists/radio.xspf -d $HOME/lanmount/music -o $HOME/temp/all.xspf
```

Example to generate multiple playlists:
```
python $HOME/scripts/xspf-gen/main.py -f $HOME/Music/playlists/radio.xspf -d \
$HOME/lanmount/music -o $HOME/temp/all.xspf -m True -e $HOME/Music/db_config.cfg \
-c $HOME/music/list.yml
```

An example of db_config.cfg (see also the Database section for the structure of
the PSQL database):

```
DB_USER=my_db_user
DB_PASS=my_db_password
DB_NAME=my_audio
DB_PORT=5432
DB_HOST=<www.xxx.yyy.zzz

```

An example of list.yml:

``` YAML
---
Classical: !!set
  ? Chant
  ? Choral
  ? Classical
  ? Gregorian Chant
  ? Opera
Jazz_Blues: !!set
  ? Jazz
  ? Blues
Pop_etc: !!set
  ? Chanson
  ? Country
  ? Electronic
  ? Flamenco
  ? Folk
  ? Funk
  ? Klezmer
  ? Pop
  ? Reggae
  ? Rock
  ? Rock & Roll
  ? Rhythm and Blues
  ? Singer Songwriter
  ? Ska
  ? Soul
  ? Soundtrack
  ? Trip-Hop
  ? World
Christmas: !!set
  ? Christmas
Spoken_Word: !!set
  ? audio book

```

## Database

``` JSON
# DB table:
Album = {
    "title": "",
    "artist": "",
    "date": datetime.now(),
    "comment": "",
    "label": "",
    "path": "",
    "id": None
}


# DB table:
Song = {
    "title": "",
    "track_id": -1,
    "genre": "",
    "artist": "",
    "composer": "",
    "performer": "",
    "date": datetime.now(),
    "file": "",
    "comment": "",
    "album_id": -1,
    "id": -1
}

```

Note that the field `album_id` holds the `id` of the corresponding `Album` row.

## Dependencies

Please see `requirements.txt`.

Note that the dbug-notifier package needs to be installed as follows (this is for version 0.1.9):
```commandline
pip install -i https://test.pypi.org/simple/ dbus-notifier==0.1.9
```

## Status

October 2025, tested locally on Manjaro Linux and VLC media player 3.0.18, Python 3.13.

## Copyright

Copyright Adam Bukolt

Note that the copyright refers to the code and scripts in this repository and
expressly not to any third-party dependencies.

## License

MIT

Icons included with this program were created by and are the sole property of the copyright holder.

Note that separate licenses apply to third-party dependencies.
