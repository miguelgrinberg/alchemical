# flask-single-db

This example demonstrates how to manage a database in a Flask application using
Alchemical and Flask-Migrate.

## Usage

To try this example, install `alchemical`, `flask` and `flask-migrate`, and
then run the following commands:

```bash
$ flask db init                             # initialize a migration repository
$ flask db migrate -m "initial migration"   # create a database migration
$ flask db upgrade                          # apply the migration changes
$ flask add                                 # add a user to the database
$ flask run                                 # start the Flask application
```

Once the Flask application is running, open `http://localhost:5000` in your
web browser to see the contents of the database. You can invoke the `flask add`
command additional times to insert more users into the database.
