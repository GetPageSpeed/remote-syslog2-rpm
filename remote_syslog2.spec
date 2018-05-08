# If any of the following macros should be set otherwise,
# you can wrap any of them with the following conditions:
# - %%if 0%%{centos} == 7
# - %%if 0%%{?rhel} == 7
# - %%if 0%%{?fedora} == 23
# Or just test for particular distribution:
# - %%if 0%%{centos}
# - %%if 0%%{?rhel}
# - %%if 0%%{?fedora}
#
# Be aware, on centos, both %%rhel and %%centos are set. If you want to test
# rhel specific macros, you can use %%if 0%%{?rhel} && 0%%{?centos} == 0 condition.
# (Don't forget to replace double percentage symbol with single one in order to apply a condition)

# Generate devel rpm
%global with_devel 0
# Build project from bundled dependencies
%global with_bundled 1
# Build with debug info rpm
%global with_debug 0
# Run tests in check section
%global with_check 1
# Generate unit-test rpm
%global with_unit_test 1

%if 0%{?with_debug}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package   %{nil}
%endif

%if ! 0%{?gobuild:1}
%define gobuild(o:) go build -ldflags "${LDFLAGS:-} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n')" -a -v -x %{?**};
%endif

# distribution specific definitions
%define use_systemd (0%{?fedora} && 0%{?fedora} >= 18) || (0%{?rhel} && 0%{?rhel} >= 7) || (0%{?suse_version} == 1315)

%global provider        github
%global provider_tld    com
%global project         papertrail
%global repo            remote_syslog2
# https://github.com/papertrail/remote_syslog2
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path     %{provider_prefix}

Name:           remote_syslog2
Version:        0.20
Release:        3%{?dist}
Summary:        Lightweight self-contained daemon for reading local files and emitting remote syslog (without using local syslog daemon)
# Detected licences
# - MIT/X11 (BSD like) at 'LICENSE'
License:        MIT License
URL:            https://%{provider_prefix}
Source0:        https://github.com/papertrail/%{repo}/archive/v%{version}.tar.gz#/%{repo}-%{version}.tar.gz
Source1:        remote_syslog.service

# e.g. el6 has ppc64 arch without gcc-go, so EA tag is required
ExclusiveArch:  %{?go_arches:%{go_arches}}%{!?go_arches:%{ix86} x86_64 aarch64 %{arm}}
# If go_compiler is not set to 1, there is no virtual provide. Use golang instead.
BuildRequires:  %{?go_compiler:compiler(go-compiler)}%{!?go_compiler:golang}

%if 0%{?rhel} == 6
Requires: initscripts >= 8.36
Requires(post): chkconfig
%endif

%if 0%{?rhel} == 7
%define epoch 1
Epoch: %{epoch}
Requires: systemd
# Required for _unitdir macro
BuildRequires: systemd
%endif 

%if ! 0%{?with_bundled}
# config.go
BuildRequires: golang(github.com/mitchellh/mapstructure)
BuildRequires: golang(github.com/spf13/pflag)
BuildRequires: golang(github.com/spf13/viper)

# remote_syslog.go
BuildRequires: golang(github.com/howbazaar/loggo)
BuildRequires: golang(github.com/papertrail/go-tail/follower)

# Remaining dependencies not included in main packages
BuildRequires: golang(github.com/VividCortex/godaemon)
BuildRequires: golang(github.com/nightlyone/lockfile)
%endif

%description
remote_syslog tails one or more log files and sends syslog messages to a remote central syslog server. 
It generates packets itself, ignoring the system syslog daemon, so its configuration doesn't affect system-wide logging.

%if 0%{?with_devel}
%package devel
Summary:       %{summary}
BuildArch:     noarch

%if 0%{?with_check} && ! 0%{?with_bundled}
BuildRequires: golang(github.com/VividCortex/godaemon)
BuildRequires: golang(github.com/nightlyone/lockfile)
%endif

Requires:      golang(github.com/VividCortex/godaemon)
Requires:      golang(github.com/nightlyone/lockfile)

Provides:      golang(%{import_path}/papertrail) = %{version}-%{release}
Provides:      golang(%{import_path}/syslog) = %{version}-%{release}
Provides:      golang(%{import_path}/utils) = %{version}-%{release}

%description devel
%{summary}

This package contains library source intended for
building other packages which use import path with
%{import_path} prefix.
%endif

%if 0%{?with_unit_test} && 0%{?with_devel}
%package unit-test-devel
Summary:         Unit tests for %{name} package
%if 0%{?with_check}
#Here comes all BuildRequires: PACKAGE the unit tests
#in %%check section need for running
%endif

# test subpackage tests code from devel subpackage
Requires:        %{name}-devel = %{version}-%{release}

%if 0%{?with_check} && ! 0%{?with_bundled}
BuildRequires: golang(github.com/stretchr/testify/assert)
%endif

Requires:      golang(github.com/stretchr/testify/assert)

%description unit-test-devel
%{summary}

This package contains unit tests for project
providing packages with %{import_path} prefix.
%endif

%prep
%autosetup 

%build
mkdir -p src/%{provider}.%{provider_tld}/%{project}
ln -s ../../../ src/%{import_path}

%if ! 0%{?with_bundled}
export GOPATH=$(pwd):%{gopath}
%else
# No dependency directories so far
export GOPATH=$(pwd):%{gopath}
%endif

%gobuild -o bin/remote_syslog %{import_path}/

%install
install -d -p %{buildroot}%{_bindir}
install -p -m 0755 bin/remote_syslog %{buildroot}%{_bindir}/remote_syslog
install -d -p %{buildroot}%{_sysconfdir}
install -p -m 0644 examples/log_files.yml.example %{buildroot}%{_sysconfdir}/log_files.yml
%if %{use_systemd}
# install systemd-specific files
%{__mkdir} -p $RPM_BUILD_ROOT%{_unitdir}
install -p -m 0644 %SOURCE1 $RPM_BUILD_ROOT%{_unitdir}/remote_syslog.service
%else
# install SYSV init stuff
%{__mkdir} -p $RPM_BUILD_ROOT%{_initrddir}
%{__install} -m755 examples/remote_syslog.init.d $RPM_BUILD_ROOT%{_initrddir}/remote_syslog
%endif

# source codes for building projects
%if 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
echo "%%dir %%{gopath}/src/%%{import_path}/." >> devel.file-list
# find all *.go but no *_test.go files and generate devel.file-list
for file in $(find . \( -iname "*.go" -or -iname "*.s" \) \! -iname "*_test.go" | grep -v "vendor") ; do
    dirprefix=$(dirname $file)
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$dirprefix
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> devel.file-list

    while [ "$dirprefix" != "." ]; do
        echo "%%dir %%{gopath}/src/%%{import_path}/$dirprefix" >> devel.file-list
        dirprefix=$(dirname $dirprefix)
    done
done
%endif

# testing files for this project
%if 0%{?with_unit_test} && 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
# find all *_test.go files and generate unit-test-devel.file-list
for file in $(find . -iname "*_test.go" | grep -v "vendor") ; do
    dirprefix=$(dirname $file)
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$dirprefix
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> unit-test-devel.file-list

    while [ "$dirprefix" != "." ]; do
        echo "%%dir %%{gopath}/src/%%{import_path}/$dirprefix" >> devel.file-list
        dirprefix=$(dirname $dirprefix)
    done
done
%endif

%if 0%{?with_devel}
sort -u -o devel.file-list devel.file-list
%endif

%check
%if 0%{?with_check} && 0%{?with_unit_test} && 0%{?with_devel}
%if ! 0%{?with_bundled}
export GOPATH=%{buildroot}/%{gopath}:%{gopath}
%else
# Since we aren't packaging up the vendor directory we need to link
# back to it somehow. Hack it up so that we can add the vendor
# directory from BUILD dir as a gopath to be searched when executing
# tests from the BUILDROOT dir.
ln -s ./ ./vendor/src # ./vendor/src -> ./vendor

export GOPATH=%{buildroot}/%{gopath}:$(pwd)/vendor:%{gopath}
%endif

%if ! 0%{?gotest:1}
%global gotest go test
%endif

%gotest %{import_path}
%gotest %{import_path}/papertrail
%gotest %{import_path}/syslog
%endif

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

%files
%license LICENSE
%doc README.md
%config(noreplace) %{_sysconfdir}/log_files.yml
%{_bindir}/remote_syslog
%if %{use_systemd}
%{_unitdir}/remote_syslog.service
%else
%{_initrddir}/remote_syslog
%endif

%if 0%{?with_devel}
%files devel -f devel.file-list
%license LICENSE
%doc README.md
%dir %{gopath}/src/%{provider}.%{provider_tld}/%{project}
%endif

%if 0%{?with_unit_test} && 0%{?with_devel}
%files unit-test-devel -f unit-test-devel.file-list
%license LICENSE
%doc README.md
%endif

%post
# Register the remote_syslog service
if [ $1 -eq 1 ]; then
%if %{use_systemd}
    /usr/bin/systemctl preset remote_syslog.service >/dev/null 2>&1 ||:
%else
    /sbin/chkconfig --add remote_syslog
%endif
    # print site info
    cat <<BANNER
----------------------------------------------------------------------

Thanks for using remote_syslog2!

Please find the official documentation for remote_syslog2 here:
* https://github.com/papertrail/remote_syslog2

----------------------------------------------------------------------
BANNER
fi

%preun
if [ $1 -eq 0 ]; then
%if %use_systemd
    /usr/bin/systemctl --no-reload disable remote_syslog.service >/dev/null 2>&1 ||:
%else
    /sbin/service remote_syslog stop > /dev/null 2>&1
    /sbin/chkconfig --del remote_syslog
%endif
fi

%postun
%if %use_systemd
/usr/bin/systemctl daemon-reload >/dev/null 2>&1 ||:
%endif
if [ $1 -ge 1 ]; then
    /sbin/service remote_syslog status  >/dev/null 2>&1 || exit 0
    /sbin/service remote_syslog upgrade >/dev/null 2>&1 || echo \
        "Binary upgrade failed"
fi

%changelog
* Tue May 8 2018 Danila Vershinin <info@getpagespeed.com> - 0.20-3
- First package for EPEL 7

