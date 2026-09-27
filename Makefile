SHELL := /bin/bash

PYTHON ?= python3
VALIDATOR := ./validate_output.py
OUTPUT_DIR ?= ./outputs
FILE ?=

.PHONY: help validate-file validate-outputs test-validator test check-tracked ci

help:
	@echo "Targets:"
	@echo "  make validate-file FILE=path/to/output.json"
	@echo "  make validate-outputs [OUTPUT_DIR=./outputs]"
	@echo "  make test-validator"
	@echo "  make check-tracked"
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

# Fails if any tracked file matches .gitignore (single source of truth).
check-tracked:
	@bad=$$(git ls-files --cached --ignored --exclude-standard); \
	if [[ -n "$$bad" ]]; then \
		echo "Tracked files match .gitignore; untrack with: git rm --cached <file>"; echo "$$bad"; exit 1; \
	fi

ci: check-tracked test-validator validate-outputs test
	@echo "CI checks passed."
