# One notebook opening request 

1. edx sends URL over https like

    https://nbhosting.inria.fr/ipythonExercice/flotbioinfo/w1/en-w1-s07-c1-walking.ipynb/mary

2. nginx proxies to the django app, that creates if needed

  * Unix id, home dir for student mary
  * copy of that notebook in the student's homedir
  * docker instance: public port 8000 is bound to internal port 8888 (all docker instances run on 8888)

3. django then answers with a HTTP redirect like

    https://nbhosting.inria.fr/8000/w1/en-w1-s07-c1-walking.ipynb?token=flotbioinfo-x-mary 
 
4. browser complies with redirect, talks to nginx again

5. nginx figures it needs to proxy to local port 8000 (Set-cookie `docker_port=8000`)

6. jupyter serves raw notebook data that contains further hrefs to `/static/` and `/api/` and the like

7. browser asks for hrefs like `/static/` with cookie `docker_port=8000`

8. nginx forwards to right docker

9. answer to `/static/`  and similar
