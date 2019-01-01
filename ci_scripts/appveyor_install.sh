# otherwise no cywgin apps are in path
export PATH="/bin:/usr/bin:/usr/local/bin:$PATH"

# install base dependencies
DEPENDENCIES=autotools,patch,make,git,autoconf,automake,libtool,bison,flex,yacc,gcc,gcc-g++
/setup-x86_64.exe -qgnNdO -s http://cygwin.mirror.constant.com --packages=$DEPENDENCIES

# install verilator
git clone http://git.veripool.org/git/verilator
cd verilator
git config user.email "fake@example.com"
git config user.name "fake name"

# disable newline modifing otherwise patches will not apply
git config core.autocrlf false
git checkout .
# appply patches
git am ../verilator_patches_tmp/*.patch
# configure and build
autoconf --version
autoconf
echo "autoconf exited with $?"
ls
./configure
make
make MKINSTALLDIRS="mkdir -p" install