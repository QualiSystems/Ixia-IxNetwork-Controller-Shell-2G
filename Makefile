
repo=localhost
user=pypiadmin
password=pypiadmin

install:
	pip install -i http://$(repo):8036 --trusted-host $(repo) -U --pre -r test_requirements.txt

.PHONY: build
build:
	shellfoundry install
