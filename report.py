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
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import sqlite3
from argparse import ArgumentParser
from contextlib import contextmanager
from datetime import datetime
from locale import getlocale, setlocale, LC_TIME

skill_order = '''
    l_tot
    l_att
    l_def
    l_mag
    l_har
    l_man
    l_alc
    l_pot
    l_sum
    l_cra
'''.split()

skill_desc = {
    'l_tot': 'Aventuriers (au total)',
    'l_att': 'Guerriers (attaque)',
    'l_def': 'Défenseurs (défense)',
    'l_mag': 'Sorciers (magie)',
    'l_har': 'Récolteurs (récolte)',
    'l_man': 'Forgerons (fabrication)',
    'l_alc': 'Alchimistes (alchimie)',
    'l_pot': 'Apothicaires (potions)',
    'l_sum': 'Nécromanciens (nécromancie)',
    'l_cra': 'Artisans (artisanat)',
}

class Counts:
    def __init__(self, c, as_of_date=None):
        self.cursor = c
        self.as_of_date = as_of_date or 'now'
        self.count_forum_users()
        self.count_valid_users()
        self.count_status('public')
        self.count_status('private')
        self.count_status('fail')

    def count_forum_users(self):
        d = self.as_of_date
        c = self.cursor
        c.execute('''
            select count(*) from user
            where julianday(created_at)
                <= julianday(?)
        ''', (d,))
        v = c.fetchone()
        self.forum = v[0]

    def count_valid_users(self):
        d = self.as_of_date
        c = self.cursor
        c.execute('''
            select count(distinct user_id)
            from scan
            where julianday(scanned_at)
                <= julianday(?)
        ''', (d,))
        v = c.fetchone()
        self.valid = v[0]

    def count_status(self, s):
        d = self.as_of_date
        c = self.cursor
        q = '''
        select count(*) from (
            select user_id, status, max(scanned_at)
            from scan
            where julianday(scanned_at)
                <= julianday(?)
            group by user_id
        )
        where status = ?
        '''
        c.execute(q, (d, s))
        v = c.fetchone()
        setattr(self, s, v[0])

@contextmanager
def time_locale(l):
    c = LC_TIME
    o = getlocale(c)
    setlocale(c, l)
    yield
    setlocale(c, o)

def parse_date(s):
    c = (
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d %H:%M:%S',
    )
    for f in c:
        try:
            return datetime.strptime(s, f)
        except ValueError:
            continue
    e = 'could not parse date: ' + s
    raise ValueError(e)

def format_date(s):
    if s is None or s == 'now':
        d = datetime.utcnow()
    else:
        d = parse_date(s)
    with time_locale('fr_FR.UTF-8'):
        r = d.strftime('%-d %B %Y')
    return r

def print_title(d1, d2):
    t = 'Classement provisoire des joueurs'
    print(t)
    print('-' * len(t))
    print('  Dès le', format_date(d1))
    if d2:
        t = '  Avec changements (±) depuis le'
        print(t, format_date(d2))
    print('')

def print_count(m, k, n, o=None, t=None):
    nv = getattr(n, k)
    ov = getattr(o, k) if o else nv
    if t:
        tv = getattr(n, t)
        p = ' (%.2f%%)' % (100 * nv / tv)
    else:
        p = ''
    d = format_change(nv - ov)
    f = '%-28s %5d %-6s%s'
    s = f % (m, nv, d, p)
    print(s)

def print_counts(c, d1, d2):
    n = Counts(c, d1)
    o = Counts(c, d2) if d2 else None
    m = 'Utilisateurs du forum'
    print_count(m, 'forum', n, o)
    m = '  Joueurs sélectionnés'
    print_count(m, 'valid', n, o)
    m = '    Statistiques visibles'
    t = 'valid'
    print_count(m, 'public', n, o, t)
    m = '    En mode vie privée'
    print_count(m, 'private', n, o, t)
    m = '    Nom différent ou disparu'
    print_count(m, 'fail', n, o, t)
    print('')

def get_ranking(c, f, m, as_of_date=None):
    d = as_of_date or 'now'
    q = 'select name, %s as f' % f
    q += '''
    from user as u
    join (
        select id, user_id, max(scanned_at)
        from scan
        where julianday(scanned_at)
            <= julianday(?)
        group by user_id
    ) c on c.user_id = u.id
    join stats as s on s.scan_id = c.id
    order by f desc, created_at desc
    limit ?
    '''
    c.execute(q, (d, m))
    r = c.fetchall()
    return r

def make_old_ranking(c, f, m, d):
    o = {}
    if not d:
        return o
    r = get_ranking(c, f, m, d)
    for e, t in enumerate(r):
        n, v = t
        o[n] = e, v
    return o

def format_change(v):
    if v != 0:
        return '%+d' % v
    return ''

def print_ranking(r, f, o):
    d = skill_desc[f]
    m = len(r)
    print('Top %d %s:' % (m, d))
    a = []
    for i, t in enumerate(r):
        n, v = t
        if n in o:
            oi, ov = o[n]
            di = format_change(oi - i)
            dv = format_change(v - ov)
        else:
            di, dv = '', ''
        s = ' %3d. %-15s %-3s | %3d %-3s'
        a.append(s % (i + 1, n, di, v, dv))
    if m & 1:
        a.append('')
        m += 1
    h = m // 2
    for i in range(h):
        print(a[i] + 8*' ' + a[i + h])

def print_rankings(c, d1, d2, m):
    for f in skill_order:
        r = get_ranking(c, f, m, d1)
        o = make_old_ranking(c, f, m, d2)
        print_ranking(r, f, o)
        print('')

def main():
    p = ArgumentParser(
        description='Report player rankings'
    )
    p.add_argument('database',
        help='The sqlite3 database file'
        ' containing the user stat tables.',
    )
    p.add_argument('-d', '--date',
        metavar='YYYY-MM-DD', default='now',
        help='Display the ranking as of'
        ' this date.',
    )
    p.add_argument('-c', '--change',
        metavar='YYYY-MM-DD',
        help='Display changes since this'
        ' date.',
    )
    p.add_argument('-t', '--top',
        metavar='N', default=50,
        help='Display this many players in'
        ' each skill ranking list.',
    )
    a = p.parse_args()
    d = sqlite3.connect(a.database)
    c = d.cursor()
    d1, d2 = a.date, a.change
    print_title(d1, d2)
    print_counts(c, d1, d2)
    print_rankings(c, d1, d2, a.top)

if __name__ == '__main__':
    main()
