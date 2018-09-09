#!/bin/bash

aws rds delete-db-cluster --db-cluster-identifier $1  --skip-final-snapshot --region us-west-2
aws cloudformation delete-stack --stack-name ${1}-bastion --region us-west-2
aws cloudformation delete-stack --stack-name $1 --region us-west-2
