# Alain

`alain_afpy` est le bot du salon #afpy sur [Libera](https://libera.chat).

![](http://www.gawel.org/thumbnails/alain_at_rennes_blog.jpg)


## Tester

Pour tester localement, dans un venv, installez alain avec (ou pas)
ses dépendances de dev :

    $ python3 -m pip install -e .[dev]

Pour le lancer localement :

    $ irc3 alain-dev.ini

Avant de commit vous pouvez passer quelques tests via :

    $ tox -p all


## Déployer

Alain est déployé sur deb2.afpy.org via ansible
(cf. [alain.yml](https://github.com/AFPy/infra/blob/main/alain.yml)
et mis à jour automatiquement au push
(cf. [deploy.yml](https://github.com/AFPy/alain/blob/main/.github/workflows/deploy.yml).
