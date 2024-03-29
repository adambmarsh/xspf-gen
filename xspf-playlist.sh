#!/bin/bash

## This script has been verified with `schellcheck`
##
## Make generating xspf playlist easier:
## - Adjust paths on lines 32-35
## - Adjust `source=` on line 107
## - Create a symbolic link to this script file, e.g.;
##   ```
##   sudo ln -s /home/user/scripts/xspf-gen/xspf-playlist.sh /home/user/scripts/xspf-playlist
##   ```

# me="${0##*/}"
# echo "$me called"
# echo
# echo "# received arguments ------->  ${@}     "
# echo "# \$1 ----------------------->  $1       "
# echo "# \$2 ----------------------->  $2       "
# echo "# \$3 ----------------------->  $3       "
# echo "# \$4 ----------------------->  $4       "
# echo "# path to me --------------->  ${0}     "
# echo "# parent path -------------->  ${0%/*}  "
# echo "# my name ------------------>  ${0##*/} "
# echo

idir=""
ifile=""
ofile=""

## Set paths as appropriate to your system:

activate_path="$HOME/.virtualenvs/generate-vlc-playlist/bin/activate"
python_pkg="$HOME/scripts/xspf-gen/xspf/handler.py"
music_path="$HOME/lanmount/music"
playlists_path="$HOME/Music/playlists"

# echo "activation path: $activate_path"

Usage() {
    echo "This script generates a VLC-compatible xspf playlist as a file."
    echo "Usage:"
    echo "    -d \"input directory, directory to scan, default is $HOME/lanmount/music \""
    echo "    -f \"input file, playlist to include in output first\""
    echo "    -o \"output file, default is $HOME/Music/playlists/all.xspf\""
    echo "    --help"
}

if [[ $# -lt 1 ]]; then
    echo "Insufficient arguments ... "
    echo ""
    Usage
    exit 1
fi


while [[ $# -gt 0 ]];
do
    case "$1" in
        -d|--idir)
            idir="$2"
            shift
            ;;
        -f|--ifile)
            ifile="$2"
            shift
            ;;
        -o|--ofile)
            ofile="$2"
            shift
            ;;
        --help|*)
            Usage
            exit 1
            ;;
    esac
    shift
done

if [[ -f "$ifile" ]] || [[ -f $playlists_path/$ifile ]]; then
    IFILEDIR=${ifile%/*}
    IFILENAME=${ifile##*/}
    source_file="$IFILENAME"
    
    if [[ -n $IFILEDIR ]] && [[ -n $IFILENAME ]] && [[ $IFILEDIR != "$IFILENAME" ]]; then
        f_option=(-f "$ifile")
    else
        f_option=(-f "$playlists_path"/"$source_file")
    fi
else
    f_option=()
fi

if [[ -n "$ofile" ]]; then
    OFILEDIR=${ofile%/*}
    OFILENAME=${ofile##*/}

    if [[ -n "$OFILEDIR" ]] && [[ "$OFILEDIR" != "$OFILENAME" ]] && [[ -d "$OFILEDIR" ]]; then
        output_file="$ofile"
    else
        output_file="$playlists_path/$OFILENAME"
    fi
else
    output_file="$playlists_path/all.xspf"
fi

if [[ -d "$idir" ]]; then
    input_dir="$idir"
else
    input_dir="$music_path"
fi

temp_output_file="$playlists_path"/unformatted.xspf

## Use path appropriate to the host system in the directive below:
# shellcheck source=/home/adam/.virtualenvs/generate-vlc-playlist/bin/activate
source "$activate_path" && python "$python_pkg" "${f_option[@]}" -d "$input_dir" -o "$output_file" && deactivate

reformat_output() {
    export XMLLINT_INDENT="    "

    mv "$output_file"  "$temp_output_file"

    xmllint -format -recover "$temp_output_file" > "$output_file"

    if [[ -f "$temp_output_file" ]]; then
        rm "$temp_output_file"
    fi
}

reformat_output
