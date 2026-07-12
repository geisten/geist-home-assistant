.PHONY: test

test:
	@python3 tests/test_ha_app.py
	@python3 tests/test_ha_integration.py
	@python3 tests/test_ha_health.py
	@python3 tests/test_ha_history.py
	@python3 tests/test_ha_operability.py
	@python3 tests/test_ha_dynamic_tools_v1.py
	@python3 tests/test_protocol_contract.py
	@tests/test_ha_install.sh
	@tests/test_ha_setup.sh
