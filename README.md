# bambulab-queue

A simple web interface designed to allow sharing bambulab 3D printers in a communal setting

```bash
Python 3.12.2
>>> from app import app, db
>>>
>>> with app.app_context():
...     db.create_all()
...
>>> exit()
```

```bash
$ flask create-admin
Enter admin username:
Enter admin email:
Enter admin ID number:
Enter admin password:
Admin user created successfully
```

```bash
$ python app.py
 * Serving Flask app 'app'
 * Debug mode: on
```
