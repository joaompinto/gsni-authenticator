%define name gsni-authenticator
%define version 0.8.4
%define unmangled_version 0.8.4
%define release 1

Summary: GSNI Authenticator Applet
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
License: UNKNOWN
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: BMI
requires: python-inotify, gnome-python2-gnomekeyring, python2-pyxdg

%description
This application will automatically athenticate you to a GSNI server
when you connect to the BMI Network.

%prep
%setup -n %{name}-%{unmangled_version}

%build
python setup.py build

%install
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
