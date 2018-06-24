# Alain

`alain_afpy` est le bot du salon #afpy sur freenode.

![](http://www.gawel.org/thumbnails/alain_at_rennes_blog.jpg)


## Tester

Pour tester localement, dans un venv, installez alain avec (ou pas)
ses dépendances de dev :

    $ python3 -m pip install -e .[dev]

Pour le lancer localement :

    $ irc3 alain-dev.ini

Avant de commit vous pouvez passer quelques tests via :

    $ detox


## Déployer

Alain est déployé dans la jail `alain` sur rainette, il est possible
de mettre à jour ce déploiement via :

    # jexec alain
    # su - alain
    $ cd ~/alain/
    $ git pull --ff-only
    $ python3.6 -m pip install --user --upgrade .
    $ exit
    # supervisorctl restart alain


Le `git pull --ff-only` passe trauqillement parce qu'alain a sa propre
clef SSH en clef de déploiement côté github, c.f. :
https://github.com/AFPy/alain/settings/keys.