# AAPM library prototype

This is a proposal for a Checkmk-specific Robot Framework library which could be used to implement portable and platform independent application checks. 

## Prerequisites 

- Visual Studio Code with Addons: 
  - Pylance
  - Robot Framework Language Server
  - Robocorp Code 

## Starting the prototype tests

`tasks.robot` contains two small AAPM checks to monitor the availability and performance of *checkmk.com*. 

It imports the `Checkmk` keyword library which can be found in `./libraries` - later on this could be published on Pypi.
The variables defined in `checkmk_vars.py` contains all information which the user has entered on the Checkmk UI. The Robot bakery process then generates a handful of RF tests for them. 

- Open this folder in VS Code. 
- As soon as you open `tasks.robot` or `robot.yaml`, you should see `rcc` in the right bottom corner building up the environment for this Robot. It should not take too long. 
- After the environment has been created, open the Robocorp pane on the left bar. The first section "ROBOTS" should show the task `robotmk` which can be started with the ▶︎ icon. 

This Robot is runnable on any environment: 
- local machine (Mac, Windows, Linux)
- Checkmk Server
- local Docker/Kubernetes 
- Robocorp Cloud

There is a lot of improvement work ahead for the keyword parametrization to make checks for HTTP, DNS, Ping etc. more parametrizable and customizable. 