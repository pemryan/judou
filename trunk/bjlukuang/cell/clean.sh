cat *.txt > all.txt
iconv all.txt -f gb18030 -t utf8|sort|uniq|iconv -f utf8 -t gb18030  > userdic.txt
