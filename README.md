# yap - yet another pastebin with a pun in its name

## Run in dev-mode
```
$ pip install -e .
$ FLASK_APP=yap FLASK_ENV=development flask db upgrade
$ FLASK_APP=yap FLASK_ENV=development flask run
```

## Test
```
$ pip install -e .[test]
$ pytest
```

## Configuration
You can find an example configuration in [config.py.example](config.py.example). YAP looks
for the configuration file in the *instance* directory. Its location depends on the installation
type -- consult [flask docs](https://flask.palletsprojects.com/en/1.1.x/config/#instance-folders)
for details.

You have to set at least `SECRET_KEY` for the application to work with some default settings (that
include sqlite as database backend).

## DB Migrations
### Init / upgrade database schema to the latest version
```
$ FLASK_APP=yap flask db upgrade
```

### Introduce new migration
1. Make some changes to the models.
2. Call `FLASK_APP=yap flask db revision 'change description'`.
3. Make sure that the generated migration works. If not, then adjust it manually.
   In case of adding new fields that are not nullable consider splitting the upgrade step
   to 3 smaller ones: add nullable field, set proper values for all existing records, make
   it nullable.
4. Commit migration to the repo.
