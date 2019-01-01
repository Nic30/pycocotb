lynx -source rawgit.com/transcode-open/apt-cyg/master/apt-cyg > apt-cyg
install apt-cyg /bin
apt-cyg install autotools

git clone http://git.veripool.org/git/verilator
cd verilator
autoconf
./configure
make
make install