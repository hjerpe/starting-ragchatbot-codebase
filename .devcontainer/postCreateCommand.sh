#!/bin/bash

SCRIPT_DIR_PARENT=$( cd -- "$( dirname -- "$(dirname -- "${BASH_SOURCE[0]}")" )" &> /dev/null && pwd )
sudo apt-get --yes update && sudo apt-get --yes upgrade
