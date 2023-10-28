# flask-multi-db

This example demonstrates how to manage multiple databases in a Flask
application using Alchemical and Flask-Migrate.

## Usage

To try this example, install `alchemical`, `flask` and `flask-migrate`, and
then run the following commands:

```bash
$ flask db init --multidb                   # initialize a migration repository
$ flask db migrate -m "initial migration"   # create a database migration
$ flask db upgrade                          # apply the migration changes
$ flask add                                 # add user and group to the db
$ flask run                                 # start the Flask application
```

Once the Flask application is running, open `http://localhost:5000` in your
web browser to see the contents of the database. You can invoke the `flask add`
command additional times to insert more users and groups into the database.
