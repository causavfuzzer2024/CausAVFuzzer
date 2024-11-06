# /apollo/recordings/recording/stop_recorder.sh
source /apollo/cyber/setup.bash
cyber_recorder_pid=$(ps -ef|grep cyber_recorder|grep -v grep|awk {'print$2'})
kill -2 $cyber_recorder_pid