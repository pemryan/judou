if [ -n "$1" ] ; then
    nm -D $1 | grep ICTCLAS_ | awk '{print $3}'
else
    echo 'Usage: command <so file>'
fi
