# AAPM library prototype

This is a proposal for a Checkmk-specific Robot Framework library which could be used to implement portable and platform independent application checks (AAPM). 

Apart from the use in checkmk, these keywords should also be able to be used in pure robot tests. 

## Prerequisites 

- Visual Studio Code with Addons: 
  - Pylance
  - Robot Framework Language Server
  - Robocorp Code 

## Usage scenarios

There are two `robot` files for demonstration purposes: 

- `tasks-kw.robot` - usage in pure Robot Framework tests
- `tasks-aapm.robot` - usage in AAPM tests

Both are explained in the next sections.

### usage in pure Robot Framework tests

Robot file: `tasks-kw.robot`

`CheckmkLibrary` is imported normally. The Keyword `Check Http` can be parametrized like any other keyword. 

### usage in AAPM tests

Robot file: `tasks-aapm.robot`

The **library imports** in the `Settings`  section are exclusively and meant to show different scenarios 1-5. Just uncomment the lines. 

An AAPM Robot always contains the full spectrum of tasks in the **tasks** section (check_http, check_dns, check_ftp, ...). Each task has a tag with the same name. For each AAPM Robot, the `.robot` file looks exactly the same. 

Mind the missing keyword arguments. They are coming from the JSON file which is given the library during the import tinme (`checkmk_vars.json`). This file contains argument data for all tests which should be executed in the Robot. 

## Running the tests

```bash
# Runing pure keyword based tests
rcc run -t kw
# Runing AAPM tests
rcc run -t aapm
```

`-t` specifies the task to run. Tasks are specified in `robot.yaml`. Mind that inside this file, Python calls Robot Framework with `-i check_http` to only execute the HTTP check. 

`tasks.robot` contains two small AAPM checks to monitor the availability and performance of *checkmk.com*. 

### Demo scenarios

- `tasks-kw.robot` - shows the HTTP keyword checking google.de
- `tasks-aapm.robot` - parametrized by Checkmk
  - `checkmk_vars-1.json` - OK, with URL arg
  - `checkmk_vars-2.json` - OK, with a lot of arguments
  - `checkmk_vars-3.json` - CRITICAL, with a failing header check 
  - `checkmk_vars-4.json` - OK, with a CRITICAL threshold check (`fail_on_thresholds=false`)
  - `checkmk_vars-5.json` - CRITICAL, with a CRITICAL threshold check (`fail_on_thresholds=true`)


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