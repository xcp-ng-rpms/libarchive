%bcond_without check

Name:           libarchive
Version:        3.3.3
Release:        1%{?dist}
Summary:        A library for handling streaming archive formats

License:        BSD
URL:            http://www.libarchive.org/
Source0:        http://www.libarchive.org/downloads/%{name}-%{version}.tar.gz

Patch1:        libarchive-3.1.2-CVE-2019-1000019.patch
Patch2:        libarchive-3.1.2-CVE-2019-1000020.patch
Patch3:        libarchive-3.3.2-CVE-2018-1000878.patch
Patch4:        libarchive-3.3.2-CVE-2018-1000877.patch
Patch5:        fix-use-after-free-in-delayed-newc.patch
Patch6:        fix-few-obvious-resource-leaks-covscan.patch
Patch7:        libarchive-3.3.2-CVE-2019-18408.patch
Patch8:        libarchive-3.3.2-CVE-2019-19221.patch
# upstream reference
# https://github.com/libarchive/libarchive/commit/aaacc8762fd8ced8823350edd8ce2e46b565582b#diff-bc144884a8e634e16f247e0588a266ee
Patch9:        libarchive-3.3.3-fixed-zstd_test.patch


BuildRequires:  gcc
BuildRequires:  bison
BuildRequires:  sharutils
BuildRequires:  zlib-devel
BuildRequires:  bzip2-devel
BuildRequires:  xz-devel
BuildRequires:  lzo-devel
BuildRequires:  e2fsprogs-devel
BuildRequires:  libacl-devel
BuildRequires:  libattr-devel
BuildRequires:  openssl-devel
BuildRequires:  libxml2-devel
BuildRequires:  lz4-devel
BuildRequires:  automake
BuildRequires:  libzstd-devel


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
%configure --disable-static --disable-rpath
# remove rpaths
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool

make %{?_smp_mflags}


%install
make install DESTDIR=$RPM_BUILD_ROOT
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
    LD_LIBRARY_PATH=`pwd`/.libs make %{?_smp_mflags} check -j1 || {
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
* Thu Apr 30 2020 Ondrej Dubaj <odubaj@redhat.com> - 3.3.3-1
- Rebase to version 3.3.3

* Tue Mar 24 2020 Ondrej Dubaj <odubaj@redhat.com> - 3.3.2-9
- Fix out-of-bounds read (CVE-2019-19221) (#1803967)

* Wed Jan 15 2020 Patrik Novotný <panovotn@redhat.com> - 3.3.2-8
- Fix CVE-2019-18408: RAR use-after-free

* Mon May 27 2019 Ondrej Dubaj <odubaj@redhat.com> - 3.3.2-7
- fix use-after-free in delayed newc link processing (#1602575)
- fix a few obvious resource leaks and strcpy() misuses (#1602575)

* Tue Apr 30 2019 Ondrej Dubaj <odubaj@redhat.com> - 3.3.2-6
- fixed use after free in RAR decoder (#1700752)
- fixed double free in RAR decoder (#1700753)

* Tue Apr 02 2019 Ondrej Dubaj <odubaj@redhat.com> - 3.3.2-5
- release bump due to gating (#1680768)

* Fri Feb 22 2019 Pavel Raiskup <praiskup@redhat.com> - 3.3.2-4
- fix out-of-bounds read within lha_read_data_none() (CVE-2017-14503)
- fix crash on crafted 7zip archives (CVE-2019-1000019)
- fix infinite loop in ISO9660 (CVE-2019-1000020)

* Wed Jul 18 2018 Pavel Raiskup <praiskup@redhat.com> - 3.3.2-3
- drop use of %%ldconfig_scriptlets

* Fri Jul 13 2018 Fedora Release Engineering <releng@fedoraproject.org> - 3.3.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Thu Feb 08 2018 Pavel Raiskup <praiskup@redhat.com> - 3.3.2-1
- rebase to latest upstream release

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 3.3.1-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Sat Feb 03 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 3.3.1-4
- Switch to %%ldconfig_scriptlets

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.3.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.3.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Tue Apr 18 2017 Pavel Raiskup <praiskup@redhat.com> - 3.3.1-1
- the latest release, per release notes:
  https://groups.google.com/forum/#!topic/libarchive-discuss/jfc7lBfrvVg

* Mon Feb 20 2017 Pavel Raiskup <praiskup@redhat.com> - 3.2.2-3
- temporary work-around for FTBFS (rhbz#1423839)

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Fri Nov 11 2016 Pavel Raiskup <praiskup@redhat.com> - 3.2.2-2
- enable lz4 support, rhbz#1394038

* Tue Oct 25 2016 Pavel Raiskup <praiskup@redhat.com> - 3.2.2-1
- minor rebase to 3.2.2

* Tue Oct 11 2016 Tomáš Mráz <tmraz@redhat.com> - 3.2.1-5
- rebuild with OpenSSL 1.1.0

* Mon Sep 26 2016 Tomas Repik <trepik@redhat.com> - 3.2.1-4
- fix some stack and heap overflows
- resolves (rhbz#1378669, rhbz#1378668, rhbz#1378666)

* Mon Aug 08 2016 Tomas Repik <trepik@redhat.com> - 3.2.1-3
- bump release for upgradepath

* Mon Jul 18 2016 Pavel Raiskup <praiskup@redhat.com> - 3.2.1-2
- print more detailed logs for testsuite, even if testsuite succeeded

* Mon Jun 20 2016 Pavel Raiskup <praiskup@redhat.com> - 3.2.1-1
- rebase, several security issues fixed (rhbz#1348194)

* Mon May 16 2016 Pavel Raiskup <praiskup@redhat.com> - 3.2.0-3
- fix the manual pages for remaining issue (rhbz#1294252)

* Thu May 12 2016 Pavel Raiskup <praiskup@redhat.com> - 3.2.0-2
- fix manual pages to mention correctly spelled binary names (rhbz#1294252)

* Tue May 03 2016 Pavel Raiskup <praiskup@redhat.com> - 3.2.0-1
- new upstream release 3.2.0 (rhbz#1330345), per release notes:
  https://groups.google.com/d/msg/libarchive-discuss/qIzW7doKzxA/MVbUkjlNAAAJ

* Mon Mar 07 2016 Björn Esser <fedora@besser82.io> - 3.1.2-16
- removed %%defattr, BuildRoot and other ancient bits
- added arch'ed bits to all Requires

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 3.1.2-15
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Mon Dec 21 2015 Pavel Raiskup <praiskup@redhat.com> - 3.1.2-14
- fix 'Out of memory when creating mtree files' error (rhbz#1284162)
- use %%autosetup macro

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.2-13
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Wed Apr 29 2015 Pavel Raiskup <praiskup@redhat.com> - 3.1.2-12
- fix libarchive segfault for intentionally broken cpio archives (rhbz#1216892)

* Sat Feb 21 2015 Till Maas <opensource@till.name> - 3.1.2-11
- Rebuilt for Fedora 23 Change
  https://fedoraproject.org/wiki/Changes/Harden_all_packages_with_position-independent_code

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.2-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Thu Jul 17 2014 Tom Callaway <spot@fedoraproject.org> - 3.1.2-9
- fix license handling

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.2-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Thu Aug 08 2013 Jaromir Koncicky <jkoncick@redhat.com> - 3.1.2-7
- Fixed Bug 993048 - added #ifdef ACL_TYPE_NFS4 to code which requires
  NFS4 ACL support

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.2-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Mon Jul 22 2013 Pavel Raiskup <praiskup@redhat.com> - 3.1.2-5
- try to workaround racy testsuite fail

* Sun Jun 30 2013 Pavel Raiskup <praiskup@redhat.com> - 3.1.2-4
- enable testsuite in the %%check phase

* Mon Jun 24 2013 Pavel Raiskup <praiskup@redhat.com> - 3.1.2-3
- bsdtar/bsdcpio should require versioned libarchive

* Wed Apr  3 2013 Tomas Bzatek <tbzatek@redhat.com> - 3.1.2-2
- Remove libunistring-devel build require

* Thu Mar 28 2013 Tomas Bzatek <tbzatek@redhat.com> - 3.1.2-1
- Update to 3.1.2
- Fix CVE-2013-0211: read buffer overflow on 64-bit systems (#927105)

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Mon Jan 14 2013 Tomas Bzatek <tbzatek@redhat.com> - 3.1.1-1
- Update to 3.1.1
- NEWS seems to be valid UTF-8 nowadays

* Wed Oct 03 2012 Pavel Raiskup <praiskup@redhat.com> - 3.0.4-3
- better install manual pages for libarchive/bsdtar/bsdcpio (# ... )
- several fedora-review fixes ...:
- Source0 has moved to github.com
- remove trailing white spaces
- repair summary to better describe bsdtar/cpiotar utilities

* Thu Jul 19 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.0.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon May  7 2012 Tomas Bzatek <tbzatek@redhat.com> - 3.0.4-1
- Update to 3.0.4

* Wed Feb  1 2012 Tomas Bzatek <tbzatek@redhat.com> - 3.0.3-2
- Enable bsdtar and bsdcpio in separate subpackages (#786400)

* Fri Jan 13 2012 Tomas Bzatek <tbzatek@redhat.com> - 3.0.3-1
- Update to 3.0.3

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.0.0-0.3.a
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Nov 15 2011 Rex Dieter <rdieter@fedoraproject.org> 3.0.0-0.2.a
- track files/sonames closer, so abi bumps aren't a surprise
- tighten subpkg deps via %%_isa

* Mon Nov 14 2011 Tomas Bzatek <tbzatek@redhat.com> - 3.0.0-0.1.a
- Update to 3.0.0a (alpha release)

* Mon Sep  5 2011 Tomas Bzatek <tbzatek@redhat.com> - 2.8.5-1
- Update to 2.8.5

* Mon Feb 07 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.8.4-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Thu Jan 13 2011 Tomas Bzatek <tbzatek@redhat.com> - 2.8.4-2
- Rebuild for new xz-libs

* Wed Jun 30 2010 Tomas Bzatek <tbzatek@redhat.com> - 2.8.4-1
- Update to 2.8.4

* Fri Jun 25 2010 Tomas Bzatek <tbzatek@redhat.com> - 2.8.3-2
- Fix ISO9660 reader data type mismatches (#597243)

* Tue Mar 16 2010 Tomas Bzatek <tbzatek@redhat.com> - 2.8.3-1
- Update to 2.8.3

* Mon Mar  8 2010 Tomas Bzatek <tbzatek@redhat.com> - 2.8.1-1
- Update to 2.8.1

* Fri Feb  5 2010 Tomas Bzatek <tbzatek@redhat.com> - 2.8.0-1
- Update to 2.8.0

* Wed Jan  6 2010 Tomas Bzatek <tbzatek@redhat.com> - 2.7.902a-1
- Update to 2.7.902a

* Fri Aug 21 2009 Tomas Mraz <tmraz@redhat.com> - 2.7.1-2
- rebuilt with new openssl

* Fri Aug  7 2009 Tomas Bzatek <tbzatek@redhat.com> 2.7.1-1
- Update to 2.7.1
- Drop deprecated lzma dependency, libxz handles both formats

* Mon Jul 27 2009 Tomas Bzatek <tbzatek@redhat.com> 2.7.0-3
- Enable XZ compression format

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.7.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Tue May 12 2009 Tomas Bzatek <tbzatek@redhat.com> 2.7.0-1
- Update to 2.7.0

* Fri Mar  6 2009 Tomas Bzatek <tbzatek@redhat.com> 2.6.2-1
- Update to 2.6.2

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.6.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Mon Feb 16 2009 Tomas Bzatek <tbzatek@redhat.com> 2.6.1-1
- Update to 2.6.1

* Thu Jan  8 2009 Tomas Bzatek <tbzatek@redhat.com> 2.6.0-1
- Update to 2.6.0

* Mon Dec 15 2008 Tomas Bzatek <tbzatek@redhat.com> 2.5.904a-1
- Update to 2.5.904a

* Tue Dec  9 2008 Tomas Bzatek <tbzatek@redhat.com> 2.5.903a-2
- Add LZMA support

* Mon Dec  8 2008 Tomas Bzatek <tbzatek@redhat.com> 2.5.903a-1
- Update to 2.5.903a

* Tue Jul 22 2008 Tomas Bzatek <tbzatek@redhat.com> 2.5.5-1
- Update to 2.5.5

* Wed Apr  2 2008 Tomas Bzatek <tbzatek@redhat.com> 2.4.17-1
- Update to 2.4.17

* Wed Mar 19 2008 Tomas Bzatek <tbzatek@redhat.com> 2.4.14-1
- Initial packaging
