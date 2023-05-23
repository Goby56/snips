### Order of precedence: top to bottom

## NGINX Web Server
[NGINX-gunicorn](https://docs.gunicorn.org/en/stable/deploy.html)
[NGINX-flask](https://flask.palletsprojects.com/en/2.3.x/deploying/nginx/)
Run from docker image?
Communicate with gunicorn -> flask

## phpMyAdmin page
[phpMyAdmin](https://docs.phpmyadmin.net/en/latest/require.html)
Install phpMyAdmin files into NGINX web server

## Switch registrar
[Cloudflare](https://developers.cloudflare.com/dns/zone-setups/full-setup/setup/)
Godaddy -> Cloudflare

## Split up app
[Flask blueprints](https://stackoverflow.com/questions/11994325/how-to-divide-flask-app-into-multiple-py-files)

## Static files
Move app.py to src and reconfigure static and template folder location