
repo=localhost
user=pypiadmin
password=pypiadmin

install:
	pip install -i http://$(repo):8036 --trusted-host $(repo) -U --pre -r --no-input --disable-pip-version-check src/requirements.txt

download:
	pip download -i http://$(repo):8036 --trusted-host $(repo) --pre  -d dist/downloads -r src/requirements.txt

.PHONY: build
build:
	shellfoundry install
