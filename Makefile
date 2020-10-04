REPO=ringfence-app
TAG=0.0.1

build-test:
	docker build -t dash-base .

jupyter:
	docker run -it --rm \
	    --name dash-jupyter \
	    -p 8888:8888 \
	    -v `pwd`/src:/apps \
	    dash-base \
	    jupyter notebook --allow-root --ip='0.0.0.0' --port=8888

run:
	docker run -it --rm \
	    --name dash-test \
	    -p 8443:8443 \
	    -v `pwd`/src:/apps \
	    dash-base \
	    python app.py

clean:
	find . \( -name \*.pyc -o -name \*.pyo -o -name __pycache__ \) -prune -exec rm -rf {} +

