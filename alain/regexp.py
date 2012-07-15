# -*- coding: utf-8 -*-
REGEXP = (
# syntaxe: (regexp, messages)
# messages peut-etre une liste, un tuple, ou une chaine

(r'^(lol|mdr)$',
     ('MDR', 'hihihi', 'HAHAHA', "mdr t'es con")),

(r'((^|.*\s)(faudrai.|faut|ca serait bien que)\s+qu.*)',
     'WARNING !!! YAKAFOKON DETECTED !!!!'),

(r'(.*\soffre.*emploi.*)',
    ('''Pour poster une offre d'emploi veuillez consulter:'''
     ' http://www.afpy.org/docs/faq.html'
     '#comment-puis-je-poster-une-offre-d-emloi')),

)
