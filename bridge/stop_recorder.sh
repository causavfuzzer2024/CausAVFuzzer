DOCKER_ID=<your_docker_name>  # ATTENTION: Modify it to your docker name
docker exec -d $DOCKER_ID /bin/bash -c 'sh /apollo/recordings/recording/stop_recorder.sh '$1
