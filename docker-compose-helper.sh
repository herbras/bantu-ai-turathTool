#!/bin/bash
# Helper script to run docker-compose from root directory
cd deployment && docker-compose "$@" 