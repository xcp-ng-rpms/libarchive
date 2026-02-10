%global package_speccommit f0e0af7bd025fb2d56f1f6a53b704b5913fea927
%global usver 3.6.1
%global xsver 2
%global xsrel %{xsver}%{?xscount}%{?xshash}
%bcond_without check

Name:           libarchive
Version:        3.6.1
Release: %{?xsrel}%{?dist}
Summary:        A library for handling streaming archive formats

License:        BSD
URL:            https://www.libarchive.org/
Source0: libarchive-3.6.1.tar.gz
Patch0: 0001-Drop-rmd160-from-OpenSSL.patch
Patch1: libarchive-3.6.1-Fix-CVE-2022-36227.patch
## Source0:        https://libarchive.org/downloads/%%{name}-%%{version}.tar.gz

BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  bison
BuildRequires:  bzip2-devel
BuildRequires:  e2fsprogs-devel
BuildRequires:  gcc
BuildRequires:  libacl-devel
BuildRequires:  libattr-devel
BuildRequires:  libtool
BuildRequires:  libxml2-devel
BuildRequires:  libzstd-devel
BuildRequires:  lz4-devel
# According to libarchive maintainer, linking against liblzo violates
# LZO license.
# See https://github.com/libarchive/libarchive/releases/tag/v3.3.0
#BuildRequires:  lzo-devel
BuildRequires:  openssl-devel
BuildRequires:  sharutils
BuildRequires:  xz-devel
BuildRequires:  zlib-devel
BuildRequires: make

%description
Libarchive is a programming library that can create and read several different
streaming archive formats, including most popular tar variants, several cpio
formats, and both BSD and GNU ar variants. It can also write shar archives and
read ISO9660 CDROM images and ZIP archives.


%package devel
Summary:        Development files for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
The %{name}-devel package contains libraries and header files for
developing applications that use %{name}.


%package -n bsdtar
Summary:        Manipulate tape archives
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description -n bsdtar
The bsdtar package contains standalone bsdtar utility split off regular
libarchive packages.


%package -n bsdcpio
Summary:        Copy files to and from archives
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description -n bsdcpio
The bsdcpio package contains standalone bsdcpio utility split off regular
libarchive packages.


%package -n bsdcat
Summary:        Expand files to standard output
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description -n bsdcat
The bsdcat program typically takes a filename as an argument or reads standard
input when used in a pipe.  In both cases decompressed data it written to
standard output.


%prep
%autosetup -p1


%build
autoreconf -ifv
%configure --disable-static LT_SYS_LIBRARY_PATH=%_libdir
%make_build


%install
%make_install
find $RPM_BUILD_ROOT -name '*.la' -exec rm -f {} ';'

# rhbz#1294252
replace ()
{
    filename=$1
    file=`basename "$filename"`
    binary=${file%%.*}
    pattern=${binary##bsd}

    awk "
        # replace the topic
        /^.Dt ${pattern^^} 1/ {
            print \".Dt ${binary^^} 1\";
            next;
        }
        # replace the first occurence of \"$pattern\" by \"$binary\"
        !stop && /^.Nm $pattern/ {
            print \".Nm $binary\" ;
            stop = 1 ;
            next;
        }
        # print remaining lines
        1;
    " "$filename" > "$filename.new"
    mv "$filename".new "$filename"
}

for manpage in bsdtar.1 bsdcpio.1
do
    installed_manpage=`find "$RPM_BUILD_ROOT" -name "$manpage"`
    replace "$installed_manpage"
done


%check
%if %{with check}
logfiles ()
{
    find -name '*_test.log' -or -name test-suite.log
}

tempdirs ()
{
    cat `logfiles` \
        | awk "match(\$0, /[^[:space:]]*`date -I`[^[:space:]]*/) { print substr(\$0, RSTART, RLENGTH); }" \
        | sort | uniq
}

cat_logs ()
{
    for i in `logfiles`
    do
        echo "=== $i ==="
        cat "$i"
    done
}

run_testsuite ()
{
    rc=0
    %make_build check -j1 || {
        # error happened - try to extract in koji as much info as possible
        cat_logs

        for i in `tempdirs`; do
            if test -d "$i" ; then
                find $i -printf "%p\n    ~> a: %a\n    ~> c: %c\n    ~> t: %t\n    ~> %s B\n"
                cat $i/*.log
            fi
        done
        return 1
    }
    cat_logs
}

# On a ppc/ppc64 is some race condition causing 'make check' fail on ppc
# when both 32 and 64 builds are done in parallel on the same machine in
# koji.  Try to run once again if failed.
%ifarch ppc
run_testsuite || run_testsuite
%else
run_testsuite
%endif
%endif


%files
%{!?_licensedir:%global license %%doc}
%license COPYING
%doc NEWS README.md
%{_libdir}/libarchive.so.13*
%{_mandir}/*/cpio.*
%{_mandir}/*/mtree.*
%{_mandir}/*/tar.*

%files devel
%{_includedir}/*.h
%{_mandir}/*/archive*
%{_mandir}/*/libarchive*
%{_libdir}/libarchive.so
%{_libdir}/pkgconfig/libarchive.pc

%files -n bsdtar
%{!?_licensedir:%global license %%doc}
%license COPYING
%doc NEWS README.md
%{_bindir}/bsdtar
%{_mandir}/*/bsdtar*

%files -n bsdcpio
%{!?_licensedir:%global license %%doc}
%license COPYING
%doc NEWS README.md
%{_bindir}/bsdcpio
%{_mandir}/*/bsdcpio*

%files -n bsdcat
%{!?_licensedir:%global license %%doc}
%license COPYING
%doc NEWS README.md
%{_bindir}/bsdcat
%{_mandir}/*/bsdcat*



%changelog
* Thu Jan 16 2025 XenServer Rebuild <rebuild@xenserver.com> - 3.6.1-2
- CP-53241: XenServer 9 rebuild

* Tue Sep 19 2023 Fei Su <fei.su@citrix.com> - 3.6.1-1
- First imported release

