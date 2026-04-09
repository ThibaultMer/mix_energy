#/bin/sh

echo "Build the predict module"
cd predict
poetry build
cd ..
cp predict/dist/predict-*-py3-none-any.whl fastapi/

echo "Build the docker ${IMAGE}"
cd fastapi
docker build -t ${IMAGE} .
cd ..
rm fastapi/*.whl
rm -rf predict/dist
