--
--  Copyright (C) 2015 Cole Minor
--  This file is part of le-ranking-scripts
--
--  le-ranking-scripts is free software: you can redistribute it and/or modify
--  it under the terms of the GNU General Public License as published by
--  the Free Software Foundation, either version 3 of the License, or
--  (at your option) any later version.
--
--  le-ranking-scripts is distributed in the hope that it will be useful,
--  but WITHOUT ANY WARRANTY; without even the implied warranty of
--  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
--  GNU General Public License for more details.
--
--  You should have received a copy of the GNU General Public License
--  along with this program.  If not, see <http:#www.gnu.org/licenses/>.
--
create table user (
  id integer primary key,
  name text not null unique collate nocase,
  forum_id integer not null,
  created_at timestamp not null,
  message_count integer not null,
  last_visit timestamp
);

create table scan (
  id integer primary key,
  user_id integer not null,
  -- NB current_timestamp is in UTC
  scanned_at timestamp default current_timestamp,
  status text not null
);

create table player (
  id integer primary key,
  scan_id integer not null,
  race text not null,
  sex text not null,
  notoriety integer not null,
  religion text not null,
  piety integer not null
);

create table stats (
  id integer primary key,
  scan_id integer not null,
  a_phys integer not null,
  a_coor integer not null,
  a_reas integer not null,
  a_will integer not null,
  a_inst integer not null,
  a_vita integer not null,
  pp_used integer not null,
  l_tot integer not null,
  l_att integer not null,
  l_def integer not null,
  l_mag integer not null,
  l_har integer not null,
  l_man integer not null,
  l_alc integer not null,
  l_pot integer not null,
  l_sum integer not null,
  l_cra integer not null
);
