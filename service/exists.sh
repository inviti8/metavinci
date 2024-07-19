#!/usr/bin/env bash
serviceName="metavinci"

if systemctl --all --type service | awk '$1 ~ '"/$serviceName/" >/dev/null;then
    echo "Yes"
else
    echo "No"
fi