#!/usr/bin/env bash

# python3 -m venv env
# env/bin/activate
# pip install --upgrade pip
# pip install awscli

aws s3 sync ../site/ s3://www.piratestudios.com/maptable --exclude .DS_Store --profile piratestudios

aws cloudfront create-invalidation --distribution-id E15MKJJIEOCOF6 --paths '/maptable/*' --profile piratestudios