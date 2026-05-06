.PHONY: all
all:

.PHONY: venv
venv:
	  /usr/bin/python -m venv venv
	./venv/bin/python -m pip install -e '.[test]'

.PHONY: test
test:
	./venv/bin/pytest

.PHONY: build
build:
	/usr/bin/python -m build

.PHONY: clean
clean:
	rm -fr -- venv
	rm -fr -- dist src/*.egg-info
