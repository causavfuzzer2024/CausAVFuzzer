# CausAVFuzzer

**NOTE** The code in the [master branch](https://github.com/causavfuzzer2024/CausAVFuzzer/tree/master) of this repository is applicable to Apollo 7. To obtain code for Apollo 6, please refer to the [apollo6 branch](https://github.com/causavfuzzer2024/CausAVFuzzer/tree/apollo6).


## Prerequisites
1. A computer powerful enogh for running Apollo+LGSVL 2021.3. 
2. Ubuntu 20.04
3. Java
4. Python3
5. antlr4
6. [rtamt](https://github.com/nickovic/rtamt)
7. protobuf 3.19.4
8. shapely
9. [cyber_record](https://github.com/daohu527/cyber_record)
10. [record_msg](https://github.com/daohu527/record_msg)



## Settings

### Install antlr4 for CausAVFuzzer
Check whether java has been installed. 
```bash
java -version
```
If not, install java for antlr4. 
```bash
sudo apt update
sudo apt install default-jre
sudo apt install default-jdk
```

Make sure installation of version antlr-4.8(the latest version is not supported):
[Install By Package](https://www.antlr.org/download/antlr-4.8-complete.jar)
```bash
cd /usr/local/lib
sudo cp /path/to/antlr-4.8-complete.jar ./
export CLASSPATH=".:/usr/local/lib/antlr-4.8-complete.jar:$CLASSPATH"
alias antlr4='java -jar /usr/local/lib/antlr-4.8-complete.jar'
alias grun='java org.antlr4.v4.gui.TestRig'
```
Add the following statements to the `.bashrc` file: 
```bash
export CLASSPATH=".:/usr/local/lib/antlr-4.8-complete.jar:$CLASSPATH"
alias antlr4='java -jar /usr/local/lib/antlr-4.8-complete.jar'
alias grun='java org.antlr4.v4.gui.TestRig'
```

### Install RTAMT for CausAVFuzzer
Please refer to [the github page](https://github.com/nickovic/rtamt) for installation of RTAMT.

### Install `protobuf` for CDModel
Install `protobuf 3.19.4` for CausAVFuzzer, by the following command: 
```shell
pip3 install protobuf==3.19.4
```

### Install `shapely` for CDModel
Install `shapely` for CDModel, by the following command: 
```shell
pip3 install shapely
```

### Install `cyber_record` for CDModel
Install `cyber_record`, a cyber record file offline parse tool, by the following command: 
```shell
pip3 install cyber_record
```

### Install `record_msg` for CDModel
To avoid introducing too many dependencies, save messages by `record_msg`.
```shell
pip3 install record_msg -U
```



## Step by step

### Install SORA-SVL and LGSVL

Please refer to [the github page](https://github.com/YuqiHuai/SORA-SVL) to install SORA-AVL. 
You can download LGSVL 2021.3 [here](https://github.com/lgsvl/simulator/releases/tag/2021.3). 

### Run Apollo with LGSVL
Please refer to [the detailed documentation](https://unity-proj.github.io/lgsvl/apollo-master-instructions/) for co-simulation of Apollo with LGSVL.
Set the LGSVL to API-Only mode.

### Setup our bridge.
1. Download and go to the root. Note that the source code should be downloaded and set up on the computer running Apollo.
	```bash
	git clone https://github.com/causavfuzzer2024/CausAVFuzzer.git
	cd CausAVFuzzer/
	```
2. Install Python API support for LGSVL.
	```bash
	cd CausAVFuzzer/bridge/PythonAPImaster
	pip3 install --user -e .  
	# If "pip3 install --user -e ." fail, try the following command:
	python3 -m pip install -r requirements.txt --user .
	```

3. Connect our bridge to the LGSVL and Apollo:
	Go the bridge in the folder: `/CausAVFuzzer/bridge`
	```bash
	cd /root_of_CausAVFuzzer/bridge
	```
	Find file: [bridge.py](./bridge/bridge.py).
	There is class `Server` in [bridge.py](./bridge/bridge.py). 

	Modify the `SIMULATOR_HOST` and `SIMULATOR_PORT` of `Server` to your IP and port of LGSVL.
	Modify the `BRIDGE_HOST` and `BRIDGE_PORT` of `Server` to your IP and port of Apollo.
	
4. Test the parser:
	If the support for parser is properly installed, we can test it by running:
	```bash
	cd /root_of_CausAVFuzzer
	python3 monitor.py
	```
	If there is no errors and warnings, the parser is correct.

### Setup the recorder. 
1. In the `/apollo` directory, create a folder named `recordings`. Then, inside this folder, create another folder named `recording`.
   ```bash
   cd /root_of_apollo/
   mkdir ./recordings/
   cd /root_of_apollo/recordings/
   mkdir ./recording/
   ```
   
2. Copy the two shell scripts located in `scripts_for_apollo` within this project to the `/root_of_apollo/recordings/recording/` directory.
   ```bash
   cd /root_of_apollo/recordings/recording/
   cp /root_of-CausAVFuzzer/scripts_for_apollo/recorder.sh ./
   cp /root-of-CausAVFuzzer/scripts_for_apollo/stop_recorder.sh ./
   ```
   
3. In `GeneticAlgorithm.py`, change the variable `recording_path` to the directory where you store your recording files, for example, `/root_of_apollo/recordings/recording/`. 
   
4. In `/root_of_CausAVFuzzer/bridge/recorder.sh` and `/root-of-CausAVFuzzer/bridge/stop_recorder.sh`, modify the variable `DOCKER_ID` to match the name or ID of your Apollo container.

### Run our bridge.
Open a terminal on the computer running Apollo.
```bash
cd /root_of_CausAVFuzzer/bridge
python3 bridge.py
```
Keep it Running.

### Run the Fuzzing Algorithm.
Open another terminal on the computer running Apollo. 
Since reading and analyzing recording files is a very time-consuming task, we use a multi-process approach to handle this type of task.
```bash
cd /root_of_CausAVFuzzer/
python3 CausAVFuzzer_mp.py
```
If the brige is set properly, you will see the LGSVL and Apollo running. The results will be put into a folder: `The_Results/`.



## Troubleshooting

### `AttributeError: module 'rtamt' has no attribute 'STLDenseTimeSpecification'`

Add the following code to `/usr/local/lib/python3.8/dist-packages/rtamt/__init__.py`
```python
from rtamt.spec.stl.dense_time.specification import StlDenseTimeSpecification as STLDenseTimeSpecification
```