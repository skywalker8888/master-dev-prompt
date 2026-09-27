SHELL := /bin/bash

PYTHON ?= python3
VALIDATOR := ./validate_output.py
OUTPUT_DIR ?= ./outputs
FILE ?=

.PHONY: help validate-file validate-outputs test-validator test ci

help:
	@echo "Targets:"
	@echo "  make validate-file FILE=path/to/output.json"
	@echo "  make validate-outputs [OUTPUT_DIR=./outputs]"
	@echo "  make test-validator"
	@echo "  make ci"

validate-file:
	@if [[ -z "$(FILE)" ]]; then \
		echo "FILE is required. Example: make validate-file FILE=outputs/sample.json"; \
		exit 2; \
	fi
	@$(PYTHON) $(VALIDATOR) "$(FILE)"

validate-outputs:
	@files=$$(find "$(OUTPUT_DIR)" -type f -name "*.json" ! -name "*.invalid.json" 2>/dev/null | sort); \
	if [[ -z "$$files" ]]; then \
		echo "No JSON files found in $(OUTPUT_DIR). Skipping."; \
		exit 0; \
	fi; \
	while IFS= read -r file; do \
		echo "Validating $$file"; \
		$(PYTHON) $(VALIDATOR) "$$file"; \
	done <<< "$$files"

test-validator:
	@$(PYTHON) $(VALIDATOR) ./ci/fixtures/valid_output.json

test:
	@$(PYTHON) -m pytest tests/ -v

ci: test-validator validate-outputs test
	@echo "CI checks passed."
