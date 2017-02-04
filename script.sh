#!/bin/sh

# FIXME: hardcoded path
cd /srv/git/linux

test $# -gt 0 || set invalid

cmd=$1
shift

case $cmd in
    list-tags)
        git tag |
        sed 's/$/.0/' |
        sort -V |
        sed 's/\.0$//'
        ;;

    get-blob)
        git cat-file blob $1
        ;;

    get-dir)
        git ls-tree -l "v$1:$2" |
        awk '{print $2" "$5" "$4}' |
        grep -v ' \.' |
        sort -t ' ' -k 1,1r -k 2,2
        ;;

    list-blobs)
        if [ "$1" = '-p' ]; then
            format='\1 \2'
            shift
        elif [ "$1" = '-f' ]; then
            format='\1 \4'
            shift
        else
            format='\1'
        fi

        git ls-tree -r "v$1" |
        sed -r "s/^\S* blob (\S*)\t(([^/]*\/)*(.*))$/$format/"
        ;;

    tokenize-blob)
        git cat-file blob $1 |
        tr '\n<>' '\1\2\3' |
        sed 's/\/\*/</g' |
        sed 's/\*\//>/g' |
        sed -r 's/(\W*)(<[^>]*>)?(\w*)/\1\2\n\3\n/g'
        ;;

    untokenize)
        tr -d '\n' |
        sed 's/>/\*\//g' |
        sed 's/</\/\*/g' |
        tr '\1\2\3' '\n<>'
        ;;

    parse-defs)
        tmp=`mktemp -d`
        git cat-file blob "$1" > $tmp/$2
        ctags -x $tmp/$2 | awk '{print $1" "$2" "$3}'
        rm $tmp/$2
        rmdir $tmp
        ;;

    *)
        echo "Usage: $0 [list-tags | get-blob | get-dir | list-blobs | tokenize-blob | parse-defs]"
        exit 1
esac
