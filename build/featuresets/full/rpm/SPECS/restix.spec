Name:           ${PACKAGE_NAME}
Version:        ${VERSION}
Release:        1%{?dist}
Summary:        restic based backup and restore

License:        MIT
URL:            https://github.com/FrankSommer-64/restix
Source0:        ${PACKAGE_NAME}-${VERSION}.tar.gz
BuildArch:      noarch

Requires:       python >= 3.10


BuildRoot:      ${RPM_BUILD_ROOT}


%description
Backup and restore based on restic.\
Provides a GUI around restic.\
Uses distinct repositories for hosts, users and years.


%prep
%setup -q

%build
# empty

%install
cp -a * %{buildroot}

%clean
rm -rf * %{buildroot}

%post
if [ $1 == 1 ];then
  # install
  cd /opt/restix
  python3 -m venv .venv
  source .venv/bin/activate
  echo Installing needed Python dependencies. This will take a while...
  pip3 install ${WHEEL_FILE_NAME}
  deactivate
elif [ $1 == 2 ];then
  # upgrade
  cd /opt/restix
  source .venv/bin/activate
  pip3 install ${WHEEL_FILE_NAME} --upgrade
  deactivate
fi
rm ${WHEEL_FILE_NAME}
rm -f /usr/local/bin/restix
ln -s /opt/restix/restix /usr/local/bin/restix
rm -f /usr/local/bin/grestix
ln -s /opt/restix/grestix /usr/local/bin/grestix


%postun
if [ $1 == 0 ];then
  rm -f /usr/local/bin/restix
  rm -f /usr/local/bin/grestix
  rm -rf /opt/restix
  rm -f /usr/local/share/applications/grestix.desktop
fi


%files
/opt/restix/${WHEEL_FILE_NAME}
/opt/restix/restix
/opt/restix/grestix
/usr/local/share/applications/grestix.desktop


%changelog
* Sun May 04 2025 Frank Sommer
- Initial version
