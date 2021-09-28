#!/bin/bash
kubectl autoscale deployment nginx --min=3 --max=10 --cpu-percent=10
kubectl autoscale deployment php --min=3 --max=10 --cpu-percent=10
