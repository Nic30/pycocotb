git clone https://github.com/transcode-open/apt-cyg
cd apt-cyg
install apt-cyg /bin
cd ..

apt-cyg install autotools

git clone http://git.veripool.org/git/verilator
cd verilator
autoconf
./configure
make
make install