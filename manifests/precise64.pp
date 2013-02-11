stage { 'first': before  => Stage['main'] }
stage { 'last':  require => Stage['main'] }

class {
      'system':         stage => first;     
      'python_modules': stage => main;
      'ruby_modules':   stage => main;
      'post_python_modules': stage => last;
}

include postgresql::server
postgresql::db{ 'grondviewdb':
  user          => 'grondview',
  password      => 'grondview',
  grant         => 'all',
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
          ensure => "1.4.3",
          provider => pip;

  }
}
class post_python_modules{
  package{
      "astropy":
          ensure => "0.1",
          provider => pip;
      "psycopg2":
          ensure => "2.4.6",
          provider => pip;
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

