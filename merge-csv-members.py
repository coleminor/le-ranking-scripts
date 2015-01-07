#!/usr/bin/env python3
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
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import sys
import sqlite3

def csv_rows(f):
    for l in f:
        if l.startswith('#'):
            continue
        t = l.split(',')
        assert len(t) == 4
        yield t

def get_member_dict(c):
    c.execute('''
        select id, name, forum_id, message_count
        from user
    ''')
    l = c.fetchall()
    m = {}
    for r in l:
        m[r['forum_id']] = r
    return m

def insert_users(c, l):
    if not l:
        return
    print('%d new forum users' % len(l))
    q = '''
    insert into user (
        forum_id,
        name,
        created_at,
        message_count
    ) values (?, ?, ?, ?)
    '''
    c.executemany(q, l)

def update_users(c, u):
    if not u:
        return
    print('%d users to update' % len(u))
    c.executemany('''
        update user
        set message_count = ?
        where forum_id = ?
    ''', u)

def read_users(f, m):
    l = []
    u = []
    for r in csv_rows(f):
        i, c = int(r[0]), int(r[3])
        if i not in m:
            l.append(r)
            continue
        o = m[i]
        if c != o['message_count']:
            u.append((c, i))
    return l, u

def merge_csv(c, p):
    m = get_member_dict(c)
    with open(p) as f:
        l, u = read_users(f, m)
    insert_users(c, l)
    update_users(c, u)
    return len(l) + len(u)

def main():
    a = sys.argv[1:]
    if len(a) < 2:
        p = sys.argv[0]
        print('usage: %s sqlite3.db members.csv' % p)
        return 1
    p = a[0]
    d = sqlite3.connect(p)
    d.row_factory = sqlite3.Row
    c = d.cursor()
    if merge_csv(c, a[1]):
        d.commit()
        print('wrote to database %s' % p)
    else:
        print('no changes needed')
    return 0

if __name__ == '__main__':
    sys.exit(main())
