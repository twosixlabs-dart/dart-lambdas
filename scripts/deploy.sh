#!/bin/bash

# This script is meant to be run *locally*; it expects to find credentials in ~/.aws/ for profile "hungerford"

if [ -z "$1" ]; then
    echo "Missing parameter: lambda function name"
    exit 1
fi

function deploy {
    rm -rf lamda
    rm -rf lambda.zip

    mkdir lambda

    pip3 install --target lambda/ .

    echo "from dart_lambdas.${1} import lambda_handler" > lambda/lambda_function.py

    # Zip lambda function from inside package directory to produce appropriate structure
    cd lambda
    zip -r ../lambda.zip *
    cd ..

    # Upload to aws
    aws --profile dart lambda update-function-code --function-name $1 --zip-file fileb://lambda.zip

    rm -rf lamda
    rm -rf lambda.zip
}

for arg in "$@"
do
    deploy ${arg}
done
