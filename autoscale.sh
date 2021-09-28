#!/bin/bash
kubectl autoscale deployment nginx --min=3 --max=20 --cpu-percent=20
kubectl autoscale deployment php --min=3 --max=20 --cpu-percent=20
