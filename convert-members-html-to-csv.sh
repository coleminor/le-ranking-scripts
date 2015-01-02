#!/bin/bash
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
d=$1
[ ! -d "$d" ] && {
  echo "expecting directory argument"
  exit 1
}
c=`pwd`
m2csv="$c/members2csv.pl"
n=`basename "$d"`
f="$c/$n.csv"
t="$c/m2csv$$.temp"
set -e
cd "$d"
for i in members*.htm; do
  [ ! -f "$i" ] && {
    echo "no member html files found in '$d'"
    exit 1
  }
  "$m2csv" "$i" >> "$t"
done
cd "$c"
mv "$t" "$f"
echo "wrote $f"
