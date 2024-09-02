#!/usr/bin/env bash

pip install -r requirements.txt --break-system-packages

cd ..
sudo chmod +x auto_updater.pyw


echo "The installation is successful."