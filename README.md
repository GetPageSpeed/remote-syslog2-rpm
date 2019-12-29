# RPM build of remote_syslog2 (CentOS/RHEL 6+)

Purpose: keep track and *automatically* build [PaperTrail](https://www.getpagespeed.com/recommends/papertrail)'s [remote_syslog2](https://github.com/papertrail/remote_syslog2).
Yes, the RPM build is automated and you always get the recent version!!!

[![CircleCI](https://circleci.com/gh/GetPageSpeed/remote-syslog2-rpm.svg?style=svg)](https://circleci.com/gh/GetPageSpeed/remote-syslog2-rpm)

Install from our YUM repository:

    sudo yum install https://extras.getpagespeed.com/release-el$(rpm -E %{rhel})-latest.rpm
    sudo yum install remote_syslog2
