flaskr
======

This is the "Flaskr" application from the tutorial section of the Flask
documentation, adapted to work with Alchemical for its database.

Install
-------
```bash
# clone the repository
$ git clone https://github.com/miguelgrinberg/alchemical
$ cd alchemical/examples/flaskr
```

Create a virtualenv and activate it:

```bash
$ python3 -m venv venv
$ . venv/bin/activate
```

Or on Windows cmd:

```text
$ py -3 -m venv venv
$ venv\Scripts\activate.bat
```

Install the requirements

```bash
$ pip install -r requirements.txt
```

Run
---

```bash
flask init-db
flask run
```

Open http://127.0.0.1:5000 in a browser.

Test
----

```bash
$ pip install pytest
$ python -m pytest
```

Run with coverage report:

```bash
$ pip install pytest-cov
$ python -m pytest --cov=flaskr --cov-branch --cov-report=term-missing
```
