#!/bin/bash
hg pull -u http://hg.afpy.org/gawel/alain
sudo supervisorctl restart alain
