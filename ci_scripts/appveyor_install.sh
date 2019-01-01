$CYGWIN/setup-x86_64.exe -qgnNdO -R C:/cygwin64 \
    -s http://cygwin.mirror.constant.com \
	-l C:/cygwin64/var/cache/setup \
	--packages=autotools,make,git,autoconf,automake,bison,yacc

git clone http://git.veripool.org/git/verilator
cd verilator
autoconf
./configure
make
make install