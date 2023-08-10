#! python3

from findArinaMsu import get_fac_links, get_students, save_to_hd
import requests, bs4, re, shelve, sys, pprint, os
import logging as l

l.basicConfig(level=l.DEBUG, format='    %(levelname)s %(message)s')
l.debug('Program starts')
#l.disable(l.DEBUG)

fac_links_sorted = get_fac_links()
student_data = get_students(fac_links_sorted[sys.argv[1]])
save_to_hd(student_data)

l.debug(f'Program {__file__} ends')