%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2: %global __python2 /usr/bin/python2}
%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%global _pkg_name replugin
%global _src_name reworkeroutput

Name: re-worker-output
Summary: Output collector for Release Engine
Version: 0.0.2
Release: 1%{?dist}

Group: Applications/System
License: AGPLv3
Source0: %{_src_name}-%{version}.tar.gz
Url: https://github.com/rhinception/re-worker-output

BuildArch: noarch
BuildRequires: python2-devel, python-setuptools
Requires: re-worker

%if 0%{?rhel} && 0%{?rhel} <= 6
Requires: python-jinja2-26
%else
Requires: python-jinja2
%endif

%description
An output collector for Rease Engine which pulls messages from a queue
and writes them out to the proper files.

%prep
%setup -q -n %{_src_name}-%{version}

%build
%{__python2} setup.py build

%install
%{__python2} setup.py install -O1 --root=$RPM_BUILD_ROOT --record=re-worker-output-files.txt

%files -f re-worker-output-files.txt
%defattr(-, root, root)
%doc README.md LICENSE AUTHORS
%dir %{python2_sitelib}/%{_pkg_name}
%exclude %{python2_sitelib}/%{_pkg_name}/__init__.py*

%changelog
* Mon Oct  6 2014 Steve Milner <stevem@gnulinux.net> - 0.0.2-1
- String redaction in output added.

* Tue Jul  1 2014 Tim Bielawa <tbielawa@redhat.com> - 0.0.1-8
- Output with escaped new-line characters are now translated into real
  new-line characters

* Mon Jun 23 2014 Tim Bielawa <tbielawa@redhat.com> - 0.0.1-7
- Revert extra new-line. It was added after every line, not just
  'Finished' lines

* Fri Jun 20 2014 Tim Bielawa <tbielawa@redhat.com> - 0.0.1-6
- Include an empty separating line after each step result has been logged

* Fri Jun 20 2014 Ryan Cook <rcook@redhat.com> - 0.0.1-5
- Added exclude py*

* Fri Jun 20 2014 Ryan Cook <rcook@redhat.com> - 0.0.1-4
- Version bump.

* Fri Jun 20 2014 Steve Milner <stevem@gnulinux.net> - 0.0.1-3
- Fixed bug with reply_to.

* Wed Jun 18 2014 Steve Milner <stevem@gnulinux.net> - 0.0.1-2
- Defattr not being used in files section.

* Mon Jun 16 2014 Tim Bielawa <tbielawa@redhat.com> - 0.0.1-1
- First release
