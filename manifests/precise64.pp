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
    "postgresql":
	ensure => installed,
        provider => apt;
}

package {
    "django":
        ensure => "1.4.3",
        provider => pip
}

service {
    "postgresql":
         ensure => running
}
