# The Translation Game

## What is this?

The translation game is an idea by @lberrada who wished to train his spanish vocabulary. A dataset was built thanks to wiktionary's public dumps and a simple website allows the user to try to translate a french word in spanish and then see the correct results. 

## How does it work?

The website can be spun up with docker-compose, a working Traefik setup is assumed in this project. An nginx container serves the static files and a python server will provide an API for word fetching and results aggregation. Later, results should be kept in a database and used to provide the user with words targeted at his weaknesses to help him improve on the words he has had trouble with in the past. 
