# xspf-gen #

This is a utility program that creates a VLC-compatible XSPF playlist.
The playlist can be consumed by other media players, for example Audacious.

The program scans a user-specified directory, where subdirectories contain music files and creates <track> elements, 
one per sub-directory.

If an input file (a pre-existing playlist) is provided, the program adds the
music items to <tracklist> and adds and populates <vlc:node title="music"> under <extension
application="http://www.videolan.org/vlc/playlist/0">.

If <trackList> or <vlc:node title="music"> (or the parent element of <vlc:node title="music">) do not exist, they 
are created.

## Usage

Run as a Python 3 script in the terminal, specifying the command-line options as appropriate (details below). 

The Python script takes the following arguments:

* -d The full path and name of the directory from which to add tracks (parent directory, where subdirectory contain music 
    tracks)
* -f The full path and name of the file to extend (if not provided, a new playlist file is created)
* -o The full path and name of the file to which to save the new/updated playlist (defaults to /home/{user}/temp/all.xspf)

Example with all the command-line parameters specified -- the program adds music
tracks to the structure in radio.xspf and saves the output to all.xspf in the
temp directory
```
python $HOME/scripts/xspf-gen/main.py -f $HOME/Music/playlists/radio.xspf -d $HOME/lanmount/music -o $HOME/temp/all.xspf
```
Example with no input file -- the program creates a new playlist structe and adds music
tracks to it, then saves the output to all.xspf in the temp directory
```
python $HOME/scripts/xspf-gen/main.py -f $HOME/Music/playlists/radio.xspf -d $HOME/lanmount/music -o $HOME/temp/all.xspf
```

## Dependencies

Please see `requirements.txt`.

Note that the dbug-notifier package needs to be installed as follows (this is for version 0,1.6):
```commandline
pip install -i https://test.pypi.org/simple/ dbus-notifier==0.1.6
```

## Status

October 2023, tested locally on Manjaro Linux and VLC media player 3.0.18, Python 3.11.

## Copyright

Copyright Adam Bukolt

Note that the copyright refers to the code and scripts in this repository and
expressly not to any third-party dependencies.

## License

MIT

Icons included with this program were created by and are the sole property of the copyright holder.

Note that separate licenses apply to third-party dependencies.
