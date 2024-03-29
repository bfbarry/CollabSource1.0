# CollabSource

## Set up

Note: as the website migrates to a React frontend, some things have changed. To view the Flask only portion, cd into `/backend`
### **Packages**
Set up virtual environment + install packages,
```shell
$ cd backend
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

### **Elasticsearch (search engine)**
https://www.elastic.co/guide/en/elasticsearch/reference/8.5/targz.html


### **Running flask**
For set up (or put in .flaskenv)
```shell
$ export FLASK_APP=collabsource.py
$ export FLASK_DEBUG=1 # this can also be in your .bash_rc or .bash_profile to automatically set this at start up
``` 
To start server (make sure venv is active):
```shell
$ flask run
```

To start frontend server on port 3000
```shell
yarn start
```

```
yarn start-api
```


ranks:
<br>in flask shell:
```python
Rank.insert_ranks()
Role.insert_roles()
```

# TODO
Backend
- separate routes from controllers


### API commands
GET
```bash
curl -X GET -H "Content-Type: application/json" http://127.0.0.1:5000/api/users/1
```
PUT
```bash
curl -X PUT -H "Content-Type: application/json" http://127.0.0.1:5000/api/test/put --data '{"name":"mochi"}'
```
POST
```bash
curl -X POST -H "Content-Type: application/json" http://127.0.0.1:5000/api/project/create --data '{"creators":[1,2], "name":"creator_map","category":"learning","skill_level":"skilz","setting":"set","descr":"asd","language":"phold","pace":"g","learning_category":"l1","subject":"0","resource":"mc"}'
```

### **Handy VSCode Extensions**
- SQLite (allows you to look at database structure by right clicking app.db)

### **Resources**
progress_doc.md is where I try to record step by step how I build this website as I follow [this tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)
