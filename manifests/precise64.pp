stage { 'first': before  => Stage['main'] }
stage { 'last':  require => Stage['main'] }
stage { 'pre': before => Stage['first'] }

class {
      'setup_user':     stage => first;
      'apt_update':     stage => pre;
      'system':         stage => first;     
      'python_modules': stage => main;
      'ruby_modules':   stage => main;
      'post_python_modules': stage => last;
      'iraf': stage => last;
      'sextractor': stage => last;
      'cronjobs':	stage => last;
      'sass-watch':	stage => last;
      'run_webserver': stage => last;
      'celeryd-init': stage => last;
## committed in repo, dont download fresh
      'bootstrap_js':    stage => main;
      'collectstatic': stage => last;
      'patch_userena': stage => last;
}

include postgresql::server
postgresql::db{ 'grondviewdb':
  user          => 'grondview',
  password      => 'grondview',
  grant         => 'all',
}

# Set global paths
#Exec { path => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/", "/home/vagrant/grondview" ] }

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
      "libx11-dev":
          ensure => installed,
          provider => apt;
      "alien":
          ensure => installed,
          provider => apt;
      "unzip":
          ensure => installed,
          provider => apt;
      "nginx-full":
          ensure => installed,
          provider => apt;
  }


}


#bootstrap.js via .zip file on github
#------------------------------
class bootstrap_js {
  exec{
    "download_bootstrap":
      command => "/usr/bin/wget http://twitter.github.io/bootstrap/assets/bootstrap.zip -O /home/vagrant/bootstrap.zip",
      user => vagrant,
      creates => "/home/vagrant/bootstrap.zip";
  }
  exec {
    "unzip_and_move":
      cwd => "/home/vagrant/",
      command => "/usr/bin/unzip /home/vagrant/bootstrap.zip && /bin/mv /home/vagrant/bootstrap /home/vagrant/grondview/grondview/static/",
      user => vagrant,
      creates => "/home/vagrant/grondview/grondview/static/bootstrap",
      require => Exec["download_bootstrap"];
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
      "uwsgi":
          ensure => "1.9.10",
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

#     "django-grappelli":
#         ensure => installed,
#         provider => pip;

     "pyraf":
         ensure => installed,
         provider => pip;

     "stsci.numdisplay":
        ensure => installed,
        provider => pip;

     "django-userena":
         ensure => "1.2.1",
         provider => pip;

     "South":
         ensure => installed,
         provider => pip;


        }
  

  exec {
     "mpl-rc":
        command => "/bin/mkdir /home/vagrant/.matplotlib && /bin/echo 'backend: agg' > /home/vagrant/.matplotlib/matplotlibrc",
        creates => "/home/vagrant/.matplotlib/matplotlibrc",
        user => vagrant;
       }

}


class iraf {
    file { 
      "/etc/profile.d/setenv.sh": #Defines iraf, IRAFARCH environmental variables
        source => "/home/vagrant/grondview/manifests/setenv.sh",
        owner => root,
        group => root,
        ensure => present;
        }
    
    exec {
      "mkdir_iraf":
        command => '/bin/mkdir -p /usr/local/iraf/ && /usr/bin/touch /usr/local/iraf/.touch',
        creates => '/usr/local/iraf/.touch',
        user => root;
        }

    exec {
      "download_iraf":
        command => '/usr/bin/wget ftp://iraf.noao.edu/iraf/v216/PCIX/iraf.lnux.x86_64.tar.gz -O /usr/local/iraf/iraf.tar.gz',
        creates => '/usr/local/iraf/iraf.tar.gz',
        user => root,
        timeout => 3000,
        require => Exec['mkdir_iraf'];
        }

    exec {
      "untar_iraf":
        command => '/bin/tar -xvf /usr/local/iraf/iraf.tar.gz -C /usr/local/iraf/ && /usr/bin/touch /usr/local/iraf/.untar_complete',
        creates => '/usr/local/iraf/.untar_complete',
        user => root,
        timeout => 3000,
        require => Exec['download_iraf'];
         }

    exec {
      "link_irafh":
        command => '/bin/ln -s /usr/local/iraf/unix/hlib/libc/iraf.h /usr/include/iraf.h',
        creates => '/usr/include/iraf.h',
        user => root,
        require => Exec['untar_iraf'];
        }

    exec {
      "link_irafbin":
        command => '/bin/ln -s /usr/local/iraf/bin.linux64 /usr/local/iraf/bin.linux',
        creates => '/usr/local/iraf/bin.linux',
        user => root,
        require => Exec['untar_iraf'];
        }

     exec {
     "link_irafbin_noao":
        command => '/bin/ln -s /usr/local/iraf/noao/bin.linux64 /usr/local/iraf/noao/bin.linux',
        creates => '/usr/local/iraf/noao/bin.linux',
        user => root,
        require => Exec['untar_iraf'];
        }

     exec {
       "mkiraf_dir":
          command => '/bin/mkdir /home/vagrant/iraf',
          creates => '/home/vagrant/iraf',
          user => vagrant;
        }

     file {
      "/home/vagrant/iraf/login.cl": #Defines iraf, IRAFARCH environmental variables
        source => "/home/vagrant/grondview/etc/login.cl",
        owner => vagrant,
        group => vagrant,
        ensure => present,
        require => Exec['mkiraf_dir'];
        }
      

    

  }

# Patch userena to send activation email to admin instead of users
class patch_userena {
  exec {
    "patch":
      command => "/bin/bash /home/vagrant/grondview/manifests/patch_userena.sh",
      user => root,
      require => Class['post_python_modules'];
  }
}

class collectstatic {
#Can't get manage.py to work!
#   exec {
#     "manage.py_collect":
#       command => 'manage.py collectstatic --noinput --pythonpath /home/vagrant/grondview --settings="grondview.settings"',
#       user => vagrant,
#       cwd => "/home/vagrant/grondview";
#       }
  exec {
    "cs":
      command => "/bin/cp -r /home/vagrant/grondview/grondview/static/* /home/vagrant/grondview/static/",
      user => vagrant;
  }
}



class sextractor {
  exec {
      "wget_sex_rpm":
        command => "/usr/bin/wget http://www.astromatic.net/download/sextractor/sextractor-2.8.6-1.x86_64.rpm -O /home/vagrant/sextractor_x64.rpm",
        user => vagrant,
        creates => "/home/vagrant/sextractor_x64.rpm";
    }

  exec {
      "alien_install":
        command => "/usr/bin/alien -di /home/vagrant/sextractor_x64.rpm",
        user => root,
        creates => "/usr/bin/sex",
        require => Exec['wget_sex_rpm'];
  }
}

# cron jobs
#----------------------------
class cronjobs{
  cron { "purge_media":
           command => "/usr/bin/python /home/vagrant/grondview/utils/purge_media.py >~/grondview/logs/cron.log 2>&1",
           user => vagrant,
           ensure => present,
           minute => "*/10"
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

class setup_user {
  user {"vagrant":
    ensure => present,
    shell => '/bin/bash',
    home => '/home/vagrant';
    #groups => ['sudo','vagrant','www-data'];
  }

  #user {"root":
    #groups => ['root','www-data'];
  #}

  
}


class run_webserver {
  exec {
    "ln_nginxconf":
      command => "/bin/ln -fs /home/vagrant/grondview/manifests/nginx.conf /etc/nginx/sites-enabled/",
      user => root,
      #creates => "/etc/nginx/sites-enabled/nginx.conf";
  }

  exec {
    "ln_django_ini":
      command => "/bin/ln -fs /home/vagrant/grondview/manifests/django_uwsgi.ini /etc/uwsgi/vassals/",
      user => root,
      #creates => "/etc/uwsgi/vassals/django_uwsgi.ini",
      require => Exec['mk_etc_uwsgi'];
  }

  exec {
    "nginx_restart":
      command => "/etc/init.d/nginx restart",
      user => root,
      require => [Exec['ln_nginxconf'],Exec['nginx_changeuser'],Exec['kill_uwsgi']];
  }
  
  exec {
    "nginx_re_restart":
      command => "/etc/init.d/nginx restart",
      user => root,
      require => Exec['uwsgi_restart'];
  }

  exec {
    "nginx_changeuser":
      command => "/bin/sed -i 's/user www-data;/user vagrant;/g' /etc/nginx/nginx.conf",
      user => root;
  }

  exec {
    "mk_etc_uwsgi":
      command => '/bin/mkdir -p /etc/uwsgi/vassals/',
      user => root,
      creates => '/etc/uwsgi/vassals/';
  }

  exec {
    "mk_uwsgi_logdir":
      command => '/bin/mkdir -p /var/log/uwsgi/',
      user => root,
      creates => '/var/log/uwsgi/';
  }

  exec {
    "kill_uwsgi":
       command => "/usr/bin/killall -9 uwsgi",
       user => root;
  }
       

  exec {
    "uwsgi_restart":
      command => "/usr/local/bin/uwsgi --emperor /etc/uwsgi/vassals --uid vagrant --gid vagrant --master --daemonize /home/vagrant/grondview/logs/uwsgi.log",
      user => vagrant,
      environment => ['USER=vagrant','HOME=/home/vagrant','iraf=/usr/local/iraf/','IRAFARCH=linux'],
      require => [Exec['ln_django_ini'],Exec['mk_uwsgi_logdir'],Exec['nginx_restart'],Exec['kill_uwsgi']];
  }

}
