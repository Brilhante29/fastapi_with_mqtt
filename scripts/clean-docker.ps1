docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker volume rm $(docker volume ls -q)
docker system prune --all --force --volumes