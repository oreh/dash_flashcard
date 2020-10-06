REPO=oreh/chinese-flashcard
TAG=0.1.1

build-test:
	docker build -t $(REPO):$(TAG) .
push:
	docker push $(REPO):$(TAG)

jupyter:
	docker run -it --rm \
	    --name dash-jupyter \
	    -p 8888:8888 \
	    -v `pwd`/src:/apps \
	    $(REPO):$(TAG) \
	    jupyter notebook --allow-root --ip='0.0.0.0' --port=8888

run:
	docker run -it --rm \
	    --name dash-test \
	    -p 8443:8443 \
	    -v `pwd`/src:/apps \
	    -e FLASK_APPLICATION_ROOT="/flashcard" \
	    $(REPO):$(TAG)


clean:
	find . \( -name \*.pyc -o -name \*.pyo -o -name __pycache__ \) -prune -exec rm -rf {} +

