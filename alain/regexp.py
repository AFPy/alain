# -*- coding: utf-8 -*-
REGEXP = (
# syntaxe: (regexp, messages)
# messages peut-etre une liste, un tuple, ou une chaine

(r'((^|.*\s)(faudrai.|faut)\s+qu.*)', 'WARNING !!! YAKAFOKON DETECTED !!!!'),

(r'(.*\soffre.*emploi.*)',
    ('''Pour poster une offre d'emploi veuillez consulter:'''
     ' http://www.afpy.org/docs/faq.html#comment-puis-je-poster-une-offre-d-emloi')),

)
