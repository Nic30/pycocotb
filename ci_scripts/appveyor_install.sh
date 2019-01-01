# otherwise no cywgin apps are in path
export PATH="/bin:$PATH"

# install base dependencies
DEPENDENCIES=autotools,patch,make,git,autoconf,automake,libtool,bison,flex,yacc,gcc,gcc-g++
/setup-x86_64.exe -qgnNdO -s http://cygwin.mirror.constant.com --packages=$DEPENDENCIES

# install verilator
git clone http://git.veripool.org/git/verilator
cd verilator
autoconf
./configure
make
make install