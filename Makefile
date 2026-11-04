VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: setup proto collector api dashboard test clean

setup: $(VENV) proto
	cd dashboard && npm install

$(VENV): requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt
	@touch $(VENV)

proto: $(VENV)
	$(PYTHON) -m grpc_tools.protoc \
		-I proto \
		--python_out=collector \
		--grpc_python_out=collector \
		proto/wifican.proto
	$(PYTHON) scripts/fix_grpc_imports.py

collector: $(VENV) proto
ifndef SCOOTER_IP
	$(error SCOOTER_IP is required. Usage: make collector SCOOTER_IP=192.168.1.x)
endif
	SCOOTER_IP=$(SCOOTER_IP) $(PYTHON) -m collector.main

api: $(VENV)
	cd api && ../$(PYTHON) -m uvicorn main:app --reload

dashboard:
	cd dashboard && npm run dev

test: $(VENV) proto
	cd api && ../$(PYTHON) -m pytest tests/ -v
	$(PYTHON) -m pytest collector/tests/ -v

clean:
	rm -f olamate.db
	rm -f collector/wifican_pb2.py collector/wifican_pb2_grpc.py
	rm -rf dashboard/dist
	rm -rf $(VENV)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
