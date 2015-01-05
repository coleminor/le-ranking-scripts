#!/usr/bin/env python3
# coding: utf-8
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
import sqlite3
import requests
import re
from argparse import ArgumentParser
from time import sleep

base_url = 'http://jeu.landes-eternelles.com/~ale'
view_url = base_url + '/view_user.php'

def parse_base(s):
    i, j = s.split('/', 1)
    return int(j)

def parse_name(s):
    c = s[0].upper()
    return c + s[1:]

def parse_sex(s):
    return s[0].lower()

attributes = {
    'Force': 'a_phys',
    'Agilité': 'a_coor',
    'Intelligence': 'a_reas',
    'Volonté': 'a_will',
    'Instinct': 'a_inst',
    'Aura': 'a_vita',
}
skills = {
    'Attaque': 'l_att',
    'Défense': 'l_def',
    'Magie': 'l_mag',
    'Récolte': 'l_har',
    'Fabrication': 'l_man',
    'Alchimie': 'l_alc',
    'Potions': 'l_pot',
    'Nécromancie': 'l_sum',
    'Artisanat': 'l_cra',
}
player_fields = {
    'Race': ('race', parse_name),
    'Sexe': ('sex', parse_sex),
    'Notoriété': ('notoriety', int),
    'Religion': ('religion', parse_name),
    'Rang': ('piety', int),
}

def update_field(d, f, s):
    k = attributes.get(f)
    if k:
        d[k] = parse_base(s)
        return
    k = skills.get(f)
    if k:
        d[k] = parse_base(s)
        return
    t = player_fields.get(f)
    if t:
        k, p = t
        d[k] = p(s)
        return
    if f == 'Au total':
        i, j = s.split('/', 1)
        d['l_tot'] = int(j)
        d['pp_used'] = int(i)
        return
    #e = 'unknown field: "%s"' % f
    #raise RuntimeError(e)

row_pattern = re.compile(
    r'<td>\s*([^<]+)\s*:\s*</td>'
    r'<td>\s*([^<]+)\s*</td>'
)

def extract_pairs(s):
    d = {}
    p = row_pattern
    for m in p.finditer(s):
        g = m.groups()
        update_field(d, *g)
    return d

name_pattern = re.compile(
    r'<table[^>]*><tr[^>]*>'
    r'<td[^>]*><b>([^<]+)</b></td>'
)

def extract_name(s, d):
    m = name_pattern.search(s)
    if not m:
        return
    d['name'] = m.group(1).strip()

def insert_scan(c, m, s):
    i = m['user_id']
    c.execute('''
        insert into
        scan (user_id, status)
        values (?, ?)
    ''', (i, s))
    print('  inserted %s status' % s)
    return c.lastrowid

def insert_table_fields(c, t, k, m):
    v = [m[f] for f in k]
    q = 'insert into %s (' % t
    q += ','.join(k)
    q += ') values ('
    q += ','.join(len(v) * ('?',))
    q += ')'
    c.execute(q, v)

player_insert_fields = '''
    scan_id race sex
    notoriety religion piety
'''.split()

def insert_player(c, m):
    t = 'player'
    k = player_insert_fields
    insert_table_fields(c, t, k, m)

stats_insert_fields = '''
    scan_id a_phys a_coor
    a_reas a_will a_inst a_vita
    pp_used l_tot l_att l_def
    l_mag l_har l_man l_alc
    l_pot l_sum l_cra
'''.split()

def insert_stats(c, m):
    t = 'stats'
    k = stats_insert_fields
    insert_table_fields(c, t, k, m)

def insert_private_state(c, m):
    s = insert_scan(c, m, 'private')
    m['scan_id'] = s
    insert_player(c, m)

def insert_public_state(c, m):
    s = insert_scan(c, m, 'public')
    m['scan_id'] = s
    insert_player(c, m)
    insert_stats(c, m)
                
def process_fields(c, m):
    if 'race' not in m:
        insert_scan(c, m, 'fail')
    elif 'l_tot' not in m:
        insert_private_state(c, m)
    else:
        insert_public_state(c, m)

def check_user(cu, i, n):
    u = view_url
    p = {'user':n}
    r = requests.get(u, params=p)
    r.raise_for_status()
    c = r.content
    print('  got %d bytes of content' % len(c))
    t = c.decode(r.encoding)
    m = extract_pairs(t)
    extract_name(t, m)
    m['user_id'] = i
    process_fields(cu, m)

def get_unchecked_users(c):
    q = '''
    select id, name from user
    where message_count > 0
    and id not in (
        select user_id from scan
    )
    '''
    c.execute(q)
    l = c.fetchall()
    print('selected %d unchecked users' % len(l))
    return l

def get_stale_users(c, o):
    q = '''
    select id, name from user
    join (
        select user_id, status,
            max(scanned_at) as m
        from scan
        group by user_id
    ) on user_id = id
    where status != 'fail'
    and message_count > 0
    and julianday('now')
        - julianday(m) > ?
    '''
    c.execute(q, (o,))
    l = c.fetchall()
    print('selected %d existing users' % len(l))
    return l

def update_users(d, o, ci):
    c = d.cursor()
    a = []
    a += get_unchecked_users(c)
    a += get_stale_users(c, o)
    t = len(a)
    print('%d total users to check' % t)
    if ci > 0:
        print('will commit after every'
            ' %d insert(s)' % ci)
    elif ci < 1:
        print('data will be committed once'
            ' all scans are complete')
    cc = 0
    for e, r in enumerate(a):
        i, n = r
        print('[%d/%d] requesting scan of'
            ' user %d (%s)' % (e + 1, t, i, n))
        check_user(c, i, n)
        cc += 1
        if ci > 0 and cc >= ci:
            d.commit()
            cc = 0
        sleep(3)
    d.commit()

def main():
    p = ArgumentParser(
        description='Fetch and store LE user stats'
    )
    p.add_argument('database',
        help='The sqlite3 database file'
        ' containing the user stat tables.',
    )
    p.add_argument('-o', '--older-than',
        metavar='DAYS', default=7, type=int,
        help='Only scan users that have not'
        ' been scanned in this many days.',
    )
    p.add_argument('-c', '--commit-interval',
        metavar='N', default=10, type=int,
        help='Commit data to database every'
        ' N individual user scans.',
    )
    a = p.parse_args()
    d = sqlite3.connect(a.database)
    i = a.commit_interval
    update_users(d, a.older_than, i)

if __name__ == '__main__':
    main()
