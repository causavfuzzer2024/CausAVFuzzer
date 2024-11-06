# /apollo/recordings/recording/recorder.sh
source /apollo/cyber/setup.bash
cyber_recorder record -ao /apollo/recordings/recording/$1.record # & PID=$!
