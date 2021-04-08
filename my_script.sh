#!/bin/bash

export WORKING_DIR=`pwd`
echo "> Working dir: $WORKING_DIR"

export WORKING_DIR_ITEMS=`ls`
echo "> Working dir: $WORKING_DIR_ITEMS"

echo "> Getting data..."
git clone git@github.com:karizmaconseil/travis_test.git

echo "> Making data dir"
sudo mv travis_test data

echo "> Access and show to data directory"
sudo cd data
sudo ls
