
# Wasteful Fellas - Source code

This repository contains all source code, data and data processing for the Bachelor project of The Fan Club!

## Instructions to test game
### While the server is running
it is enough to simply download the appropriate build for your system under releases. (You can check if the server is running [here](https://wastefulfellas-dkdsd4bkhrepf8ec.swedencentral-01.azurewebsites.net), if it is running, the site will reply with "Hello from Azure")

### After the server has been shut down
(Since logs are uploaded directly to this GitHub, Logging will not work unless the function "end_convo" in [main.py](models/main.py) is rewritten. This does not affect gameplay.)

#### Requirements
- Python 3.10+ (older versions may work) with requirements from "[requirements](models/requirements.txt)"
- Godot v4 (or newer)
- OS environment variable for hugging face api with permission to run "smolagents" agents, under the name "HF_API_TOKEN"

#### Steps
- Download the repository
- Open the godot project "wasteful-fellas"
- Inside "[send_message.gd](wasteful-fellas/scripts/send_message.gd)", rename "base_url" to default localhost url.
- Run "[main.py](models/main.py)"
- Run Godot project or export appropriate installation and run output file.


## Structure
Repository is split into 4 sections each containing a part of the project.

### DataAnalysis
Contains logs collected during gameplay and experiments

#### experiment_1
In this experiment, all log files are annotated by several annotators, including an LLM. And appropriate graphs are created using the resulting data, looking at consistency of specific models and prompts

Experiment 1 contains code from [Inter-Annotator Agreement (IAA)](https://medium.com/data-science/inter-annotator-agreement-2f46c6d37bf3) for calculation of Fleiss' kappa score, and code based on equations from [Krippendorff's alpha coefficient](https://github.com/jmgirard/mReliability/wiki/Krippendorff%27s-alpha-coefficient) for calculation of Krippendorf's alpha

#### experiment_2
This experiment compares the same results to a questionaire, the results for wich are available in [Wasteful Fellas](DataAnalysis/experiment_2/Wasteful%20Fellas.csv).

### Game Output
Contains the final outputs of the game in different formats

### models
Contains the server section of the game.
[main.py](models/main.py) runs the server itself and handles communication between the game and [app.py](models/local_agent/app.py).
[app.py](models/local_agent/app.py) handles conversations with the agents and their avaiable tools.

### wasteful-fellas
This contains the godot project. 

#### art 
Art for characters, backgrounds and ui elements

#### scripts
Contains source code for the game along with scenes and sound effects.


# Authors
- Asger N. S. Pedersen
- Natali N. S. Rwotto
- Franja S. Høgdall
