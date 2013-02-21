#Seemingly the coffee binary has a bug in --watch: It doesn't work reliably.
echo "Compiling coffeescript"
PROJECT_ROOT="/home/vagrant/grondview/"
/usr/bin/coffee --bare -o $PROJECT_ROOT/grondview/static/js/ -c $PROJECT_ROOT/grondview/static/coffee/
#/usr/bin/coffee -o $PROJECT_ROOT/grondview/static/js/ -c $PROJECT_ROOT/grondview/static/coffee/
