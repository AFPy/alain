# -*- coding: utf-8 -*-
from chut import sh


def restart(name):
    try:
        if name in ('alain', 'members'):
            supervisor = sh['/home/afpy/AfpySupervisor/bin/supervisorctl']
            for line in supervisor('restart', name, combine_stderr=True):
                yield line
        elif name == 'docs':
            pwd = sh.pwd()
            sh.cd('/home/afpy/AfpySphinx/docs')
            if not sh['hg']('pull -u'):
                yield 'Failed to update code'
            else:
                res = sh['make']('html').succeeded
                sh.cd(pwd)
                if res:
                    yield 'Docs build success'
                else:
                    yield 'Docs build failure'
        elif name == 'plone':
            plone = sh['/home/afpy/afpy2012/plone/zinstance/bin/plonectl']
            for line in plone('restart', combine_stderr=True):
                yield line
        else:
            yield 'moi pas connaitre %s' % name
    except OSError, e:
        yield repr(e)
