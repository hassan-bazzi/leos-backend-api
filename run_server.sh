#!/bin/sh

gunicorn --chdir /app app -w 2 --threads 2 --reload -b 0.0.0.0:8000
