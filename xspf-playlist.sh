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

activate_path="$HOME/scripts/xspf-gen/bin/activate"
python_pkg="$HOME/scripts/xspf-gen/xspf/handler.py"
music_path="$HOME/lanmount/music"
playlist_path="$HOME/Music/playlist"

# echo "activation path: $activate_path"

Usage() {
    echo "This script generates a VLC-compatible xspf playlist as a file."
    echo "Usage:"
    echo "    -c \"list configuration file for multi-list output \""
    echo "    -d \"input directory, directory to scan, default is $HOME/lanmount/music \""
    echo "    -e \"enviornment (DB) configuration file, a flat file of name-value pairs \""
    echo "    -f \"input file, playlist to include in output first\""
    echo "    -m \"flag indicating whether to generate multiple lists referenced in all.xspf (True) or a single all.xspf\""
    echo "    -o \"output file, default is $HOME/Music/playlist/all.xspf\""
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
        -c|--icfg)
            icfg="$2"
            shift
            ;;
        -d|--idir)
            idir="$2"
            shift
            ;;
        -e|--ienvcfg)
            ienvcfg="$2"
            shift
            ;;
        -f|--ifile)
            ifile="$2"
            shift
            ;;
        -m|--imulti)
            imulti="$2"
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

if [[ -z "$icfg" ]] || [[ ! -f "$icfg" ]]; then
    icfg=''
fi

if [[ -z "$ienvcfg" ]] || [[ ! -f "$ienvcfg" ]]; then
    ienvcfg=''
fi

if [[ -f "$ifile" ]] || [[ -f $playlist_path/$ifile ]]; then
    IFILEDIR=${ifile%/*}
    IFILENAME=${ifile##*/}
    source_file="$IFILENAME"
    
    if [[ -n $IFILEDIR ]] && [[ -n $IFILENAME ]] && [[ $IFILEDIR != "$IFILENAME" ]]; then
        f_option=(-f "$ifile")
    else
        f_option=(-f "$playlist_path"/"$source_file")
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
        output_file="$playlist_path/$OFILENAME"
    fi
else
    output_file="$playlist_path/all.xspf"
fi

if [[ -d "$idir" ]]; then
    input_dir="$idir"
else
    input_dir="$music_path"
fi

temp_output_file="$playlist_path"/unformatted.xspf

## Use path appropriate to the host system in the directive below:
# shellcheck source=/home/adam/scripts/xspf-gen/.venv/bin/activate
. "$activate_path" && python "$python_pkg" "${f_option[@]}" -d "$input_dir" -o "$output_file" -m "$imulti" -c "$icfg" -e "$ienvcfg" && deactivate

reformat_output() {
    export XMLLINT_INDENT="    "
    
    for output_file in "${ofile%/*}"/*.xspf; do
        mv "$output_file"  "$temp_output_file"

        xmllint -format -recover "$temp_output_file" > "$output_file"

        if [[ -f "$temp_output_file" ]]; then
            rm "$temp_output_file"
        fi
    done
}

reformat_output
