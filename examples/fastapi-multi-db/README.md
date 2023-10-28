# fastapi-multi-db

This example demonstrates how to manage multiple databases in a FastAPI
application using Alchemical.

## Usage

To try this example, install `alchemical` and `uvicorn`, and then run the
following commands:

```bash
$ python app.py init                        # initialize the database
$ python app.py add                         # add user and group to the db
$ uvicorn --port 5000 app:app               # start the fastapi application
```

Once the FastAPI application is running, open `http://localhost:5000` in your
web browser to see the contents of the database. You can invoke the `add`
command additional times to insert more users and groups into the database.
