#!/usr/bin/perl
#
#  Copyright (C) 2015 Cole Minor
#  This file is part of le-ranking-scripts
#
#  le-ranking-scripts is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  le-ranking-scripts is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http:#www.gnu.org/licenses/>.
#
use warnings;
use strict;
use WWW::Mechanize;
use POSIX qw(strftime);
use File::Spec::Functions;
use File::Path qw(make_path);
use utf8;

$|++;
my $m = WWW::Mechanize->new();
push @{ $m->requests_redirectable }, 'POST';
$m->agent_alias('Linux Mozilla');
my $base = 'http://landes-eternelles.com/phpBB';
my $wait_seconds = 5;
my $members_per_list = 50;
my $sdir = strftime('members-%Y%m%d', localtime);

sub pause {
  my ($w) = @_;
  $w ||= $wait_seconds;
  print "  sleeping for $w seconds\n";
  sleep $w;
}

sub check_result {
  my $r = $m->res;
  my $s = $r->status_line;
  print "$s\n";
  die unless $m->success;
}

sub get {
  my ($u) = @_;
  print "GET $u ... ";
  $m->get($u);
  check_result;
}

sub login {
  my ($n, $p) = @_;
  my $u = "$base/ucp.php?mode=login";
  get $u;
  pause;
  print "logging in as $n ... ";
  $m->submit_form(
    with_fields => {
      username => $n,
      password => $p,
    },
    button => 'login',
  );
  check_result;
  my $c = $m->content;
  unless ($c =~ /Vous êtes à présent connecté/) {
    die "login failed";
  }
  print "login succeeded\n";
  pause;
}

sub get_member_count {
  my $u = "$base/memberlist.php";
  get $u;
  my $h = $m->content;
  unless ($h =~ /\[ (\d+) utilisateurs \]/) {
    die "did not find member count";
  }
  my $c = $1;
  print "found $c members\n";
  return $c;
}

sub get_member_lists {
  my ($c) = @_;
  unless (-d $sdir) {
    make_path $sdir;
    print "created directory $sdir\n";
  }
  my $p = $members_per_list;
  my $n = int($c / $p);
  print "getting $n member lists ($p members per page)\n";
  for my $i (0 .. $n) {
    my $h = sprintf 'members%04d.htm', $i;
    my $f = catfile($sdir, $h);
    my $s = $p * $i;
    if (-f $f) {
      print "skipping start=$s, file $f exists\n";
      next;
    }
    my $t = "$base/memberlist.php?start=$s";
    get $t;
    $m->save_content($f);
    my $b = -s $f;
    die "no data saved" unless $b;
    print "  $b bytes saved to $f\n";
    pause;
  }
}

sub main {
  @_ = @ARGV;
  my $u = shift or die "username required\n";
  my $p = shift or die "password required\n";
  login $u, $p;
  my $c = get_member_count;
  get_member_lists $c;
}

main;
