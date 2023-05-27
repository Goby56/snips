#!/bin/sh

gunicorn -w 2 -b 0.0.0.0:5001 main:flask_app 
