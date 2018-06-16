# Alain

`alain_afpy` est le bot du salon #afpy sur freenode.


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
    $ exit
    # supervisorctl restart alain
