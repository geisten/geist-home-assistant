.PHONY: test

test:
	@python3 tests/test_ha_app.py
	@python3 tests/test_runtime_lock.py
	@python3 tests/test_ha_integration.py
	@python3 tests/test_ha_health.py
	@python3 tests/test_ha_transport.py
	@python3 tests/test_ha_preflight.py
	@python3 tests/test_ha_chaos.py
	@python3 tests/test_ha_lifecycle.py
	@python3 tests/test_ha_history.py
	@python3 tests/test_ha_operability.py
	@python3 tests/test_ha_dynamic_tools_v1.py
	@python3 tests/test_protocol_contract.py
	@python3 tests/test_hacs_package.py
	@tests/test_ha_install.sh
	@tests/test_ha_setup.sh
