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
use HTML::TableExtract qw(tree);
use Encode qw(decode);
use utf8;
binmode STDOUT, ":encoding(UTF-8)";

sub get_text {
  my ($e) = @_;
  my $t = $e->as_text;
  $t =~ s/\xa0//g;
  my $u = decode('UTF-8', $t);
  return $u;
}

my @months = qw(
  Jan Fév Mars Avr Mai Juin Juil Août Sep Oct Nov Déc
);
my %month_number = map {
  $months[$_] => $_ + 1
} 0 .. $#months;

sub parse_date {
  my ($s) = @_;
  die "could not parse date '$s'"
    unless $s =~ /(\d+) (\S+) (\d+), (\d+):(\d+)/;
  my ($d, $m, $y, $h, $i) = ($1, $2, $3, $4, $5);
  my $n = $month_number{$m};
  die "unrecognized month '$m'" unless defined $n;
  $n = "0$n" if $n < 10;
  return "$y-$n-$d $h:$i";
}

sub parse_forum_user_id {
  my ($u, $n) = @_;
  die "forum user id not found for user '$n'"
    unless $u =~ /&u=(\d+)$/;
  my $i = $1;
  return $i;
}

sub main {
  @_ = @ARGV;
  my $f = shift or die "html file required";
  die "no such file: $f\n" unless -f $f;
  my $t = HTML::TableExtract->new(
    headers => [qw(Nom Inscrit Message)],
  );
  print STDERR "parsing $f\n";
  $t->parse_file($f);
  for my $r ($t->rows) {
    my $l = $r->[0];
    next unless ref($l) =~ /Element/;
    my $e = $l->look_down(_tag => 'a');
    my $u = $e->attr('href');
    my ($n, $d, $m) = map { get_text($_) } @$r;
    my $i = parse_forum_user_id $u, $n;
    my $s = parse_date $d;
    print "$i,$n,$s,$m\n";
  }
}

main;
