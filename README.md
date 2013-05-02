grondview
=========

assumes a `vagrant up` precise64.box environment. Packages from apt+pypi

run `./runserver.sh` to start the development server (add a user account for the site when prompted!)

connect to http://localhost:8000 on host machine.

Pyraf tasks (ie, /forcedetect/) will fail until iraf/pyraf is installed manually. There is no automated way to install iraf/pyraf.
Install iraf package from ftp://iraf.noao.edu/iraf/v216/PCIX/iraf.lnux.x86_64.tar.gz , untar in its own directory and run $iraf/unix/hlib/install and follow instructions.
Install pyraf package from http://stsdas.stsci.edu/download/pyraf/pyraf-2.0.tar.gz, run setup.py and follow instructions.
