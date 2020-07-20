docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)
docker system prune -a
docker build --tag detailed_trainer_agent_image .
