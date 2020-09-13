.PHONY: .

SHELL := /bin/bash
TIMER = TIMEFORMAT="This make $(MAKECMDGOALS) target took %1R seconds" && time  # bash built-in, requires bash to be the SHELL above
PACKAGE = awair_command_line
SRC := $(PACKAGE)/*.py
PYTHONPATH = export PYTHONPATH=.


all: black ci
	@echo ""
	@echo "ALL GOOD!"
	@echo ""

ci: blackcheck typecheck pep lint test coverage

black:
	@$(TIMER) black $(SRC)

blackcheck:
	@$(TIMER) black --check $(SRC)

lint:
	@$(PYTHONPATH) $(TIMER) pylint_runner -v --rcfile .pylintrc .

pep:
	@$(TIMER) pycodestyle $(SRC)

typecheck:
	@$(TIMER) mypy $(SRC)

coverage: coverage-run coverage-report

coverage-run:
	@$(TIMER) coverage run --source=. -m pytest -c setup.cfg --durations=5 -vv .
	@# @py.test --cov-report term-missing --cov=. .

coverage-report:
	@echo
	@echo
	@$(TIMER) coverage report -m

test:
	@$(PYTHONPATH) $(TIMER) py.test .

run:
	@$(PYTHONPATH) $(TIMER) python $(PACKAGE)/awair.py

clean:
	@rm -rf .coverage .mypy_cache .pytest_cache __pycache__ build dist *.egg-info

#
# Below this, things are only useful for wheel management
#
wheel: clean ci wheel-build

# Builds the wheel
wheel-build:
	@rm -f dist/*.whl
	@python3 setup.py bdist_wheel

# Installs the wheel
wheel-install:
	@python3 -m pip install --force dist/*.whl

# Uploads to pypi
wheel-push:
	@python3 -m twine upload dist/*.whl

# Initializes the environment - only need to run once
init:
	@python3 -m virtualenv .env
	@python3 -m pip install --upgrade pip setuptools wheel tqdm twine
	@python3 -m pip install -r requirements.txt

