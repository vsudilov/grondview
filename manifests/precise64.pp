stage { 'first': before  => Stage['main'] }
stage { 'last':  require => Stage['main'] }
stage { 'pre': before => Stage['first'] }

class {
      'apt_update':     stage => pre;
      'system':         stage => first;     
      'python_modules': stage => main;
      'ruby_modules':   stage => main;
      'post_python_modules': stage => last;
      'cronjobs':	stage => last;
      'sass-watch':	stage => last;
#      'coffee-watch': stage => last; #Doesnt work, bug in coffee --watch
      'celeryd-init': stage => last;
}

include postgresql::server
postgresql::db{ 'grondviewdb':
  user          => 'grondview',
  password      => 'grondview',
  grant         => 'all',
}

#user { "celery":
#  ensure => present,
#  shell => '/usr/sbin/nologin',
#  managehome => false;
#}


# Run apt-get update once on VM creation
# -----------------------------
class apt_update { 
  exec {
     "apt-get update":
        command => "/usr/bin/apt-get update && touch /root/apt-updated",
        creates => "/root/apt-updated";
       }
}

# System packages via apt
#------------------------------
class system{
  package {
      "build-essential":
          ensure => installed,
          provider => apt;
      "python":
          ensure => installed,
          provider => apt;
      "python-dev":
          ensure => installed,
          provider => apt;
      "python-pip":
          ensure => installed,
          provider => apt;
      "rubygems":
          ensure => installed,
          provider => apt;
      "libpq-dev":
          ensure => installed,
          provider => apt;
      "git":
          ensure => installed,
          provider => apt;
      "python-matplotlib":
          ensure => installed,
          provider => apt;
      "python-scipy":
          ensure => installed,
          provider => apt;
      "redis-server":
          ensure => installed,
          provider => apt;
      "coffeescript":
          ensure => installed,
          provider => apt;
      "libx11-dev":
          ensure => installed,
          provider => apt;
  }
}

# Python modules via pip
#------------------------------
class python_modules{
  package {
      "numpy":
          ensure => "1.6.1",
          provider => pip;
      "pyfits":
          ensure => "2.4.0",
          provider => pip;
      "django":
          ensure => "1.5",
          provider => pip;
      "d2to1":
          ensure => installed,
          provider => pip;

  }
}
class post_python_modules{
  package{
       "astLib":
          ensure => "0.6.1",
          provider => pip;

#      "astropy":
#          ensure => "0.1",
#          provider => pip;

      "psycopg2":
          ensure => "2.4.6",
          provider => pip;

     "celery-with-redis":
          ensure => installed,
          provider => pip;

     "django-celery":
          ensure => installed,
          provider => pip;

     "django-grappelli":
         ensure => installed,
         provider => pip;

     "pyraf":
         ensure => installed,
         provider => pip;

#     "stsci.distutils":
#         ensure => installed,
#         provider => pip;

#      "stscipython":
#          ensure => installed,
#          provider => pip;

        }
  

  exec {
     "mpl-rc":
        command => "/bin/mkdir /home/vagrant/.matplotlib && /bin/echo 'backend: agg' > /home/vagrant/.matplotlib/matplotlibrc",
        creates => "/home/vagrant/.matplotlib/matplotlibrc",
        user => vagrant;
       }


  file { 
    "/etc/profile.d/setenv.sh":
      source => "/home/vagrant/grondview/manifests/setenv.sh",
      owner => root,
      group => root,
      ensure => present;
        }
}



# cron jobs
#----------------------------
class cronjobs{
  cron { "purge_media":
           command => "/usr/bin/python /home/vagrant/grondview/utils/purge_media.py >~/grondview/logs/cron.log 2>&1",
           user => vagrant,
           ensure => present,
           minute => "*/5"
  }
}



# Ruby packages via gem
#------------------------------
class ruby_modules{
  package{
    "sass":
      ensure => installed,
      provider => gem;
  }
}

class sass-watch{
  exec {
   "sass-watch":
     command => "/usr/local/bin/sass --watch /home/vagrant/grondview/grondview/static/css/sass/style.scss:/home/vagrant/grondview/grondview/static/css/style.css >/dev/null &",
     user => vagrant;
       }
}


# Start up celeryd
#----------------------------
class celeryd-init {
  exec {
     "ln celeryd":
       command => "/bin/ln -fs /home/vagrant/grondview/etc/celeryd /etc/init.d/celeryd",
#         creates => "/etc/init.d/celeryd";
       }

  exec {
     "ln celeryd.conf":
       command => "/bin/ln -fs /home/vagrant/grondview/etc/celeryd.conf /etc/default/celeryd",
#         creates => "/etc/default/celeryd";
       }

  exec {
    "init /var/run/celery":
      command => "/bin/mkdir /var/run/celery/ && /bin/chgrp -R vagrant /var/run/celery && /bin/chmod -R g+rw /var/run/celery && /bin/chmod -R g+s /var/run/celery",
      creates => "/var/run/celery";
       }

  exec {
    "init /var/log/celery":
      command => "/bin/mkdir /var/log/celery/ && /bin/chgrp -R vagrant /var/log/celery && /bin/chmod -R g+rw /var/log/celery && /bin/chmod -R g+s /var/log/celery",
      creates => "/var/log/celery";
       }

  exec {        #Don't use service, it will break the cwd!
   "celeryd":
     command => "/etc/init.d/celeryd start",
     cwd => "/home/vagrant/grondview",
     user => "vagrant",
     environment => ['HOME=/home/vagrant'],
     require => [Exec['ln celeryd.conf'],Exec['init /var/run/celery'],Exec['init /var/log/celery'],Exec['ln celeryd'],Class['post_python_modules']];
  }
}


# Misc
#------
class coffee-watch{
  exec {
   "coffee-watch":
     command => "/usr/bin/coffee -o /home/vagrant/grondview/static/js/ -cw /home/vagrant/grondview/static/coffee/ &",
     user => vagrant;
       }
}
