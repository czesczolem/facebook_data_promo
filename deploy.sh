#!/usr/bin/env bash

docker build -t gcr.io/analytics-242319/promo_job . &
gcloud docker -- push gcr.io/analytics-242319/promo_job:latest &
kubectl create -f kubernetes/job.yaml &
