# ============================================================
# VIO 83 AI ORCHESTRA — Test Sistema Plugin / MCP
# Copyright (c) 2026 Viorica Porcu. AGPL-3.0 / Proprietaria
# ============================================================
"""Test completi per il sistema Plugin/MCP di VIO 83 AI Orchestra."""
import pytest
import json
import tempfile
import os
from pathlib import Path


class TestPluginRegistry:
    """Test del registry centrale dei plugin."""

    def test_registry_initializes(self):
        from backend.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        assert registry is not None

    def test_registry_has_builtin_plugins(self):
        from backend.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        plugins = registry.list_plugins()
        assert len(plugins) >= 5

    def test_registry_plugin_ids(self):
        from backend.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        ids = {p['id'] for p in registry.list_plugins()}
        expected = {'vio.filesystem', 'vio.clipboard', 'vio.websearch',
                    'vio.datetime', 'vio.calculator', 'vio.memory'}
        assert expected.issubset(ids)

    def test_registry_get_plugin(self):
        from backend.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        plugin = registry.get_plugin('vio.calculator')
        assert plugin is not None
        assert plugin.info.id == 'vio.calculator'

    def test_registry_get_nonexistent_plugin(self):
        from backend.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        plugin = registry.get_plugin('nonexistent.plugin')
        assert plugin is None

    def test_registry_execute_nonexistent(self):
        from backend.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        result = registry.execute('nonexistent', 'tool', {})
        assert 'error' in result

    def test_registry_tools_context_is_string(self):
        from backend.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        context = registry.get_tools_for_prompt()
        assert isinstance(context, str)
        assert len(context) > 100
        assert 'vio.calculator' in context

    def test_get_registry_singleton(self):
        from backend.plugins.registry import get_registry
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2


class TestCalculatorPlugin:
    """Test plugin calcolatrice — il piu sicuro da testare."""

    def _calc(self, expr):
        from backend.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        return registry.execute('vio.calculator', 'calculate', {'expression': expr})

    def test_simple_addition(self):
        result = self._calc('2 + 3')
        assert result.get('result') == 5

    def test_multiplication(self):
        result = self._calc('7 * 8')
        assert result.get('result') == 56

    def test_power(self):
        result = self._calc('2 ** 10')
        assert result.get('result') == 1024

    def test_sqrt(self):
        import math
        result = self._calc('sqrt(144)')
        assert abs(result.get('result') - 12.0) < 0.001

    def test_pi(self):
        import math
        result = self._calc('pi')
        assert abs(result.get('result') - math.pi) < 0.0001

    def test_trig(self):
        result = self._calc('sin(0)')
        assert abs(result.get('result') - 0.0) < 0.0001

    def test_forbidden_import(self):
        result = self._calc('import os')
        assert 'error' in result

    def test_forbidden_dunder(self):
        result = self._calc('__import__("os")')
        assert 'error' in result

    def test_forbidden_exec(self):
        result = self._calc('exec("pass")')
        assert 'error' in result

    def test_division_by_zero(self):
        result = self._calc('1/0')
        assert 'error' in result

    def test_invalid_expression(self):
        result = self._calc('foobar()')
        assert 'error' in result

    def test_result_in_response(self):
        result = self._calc('100 + 200')
        assert 'result' in result
        assert result['result'] == 300

    def test_expression_echoed(self):
        result = self._calc('42')
        assert result.get('expression') == '42'


class TestDateTimePlugin:
    """Test plugin data/ora."""

    def _execute(self, tool, params=None):
        from backend.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        return registry.execute('vio.datetime', tool, params or {})

    def test_now_returns_dict(self):
        result = self._execute('now')
        assert isinstance(result, dict)
        assert 'error' not in result

    def test_now_has_date_field(self):
        result = self._execute('now')
        assert 'date' in result
        assert '/' in result['date']  # DD/MM/YYYY format

    def test_now_has_time_field(self):
        result = self._execute('now')
        assert 'time' in result
        assert ':' in result['time']

    def test_now_has_weekday(self):
        result = self._execute('now')
        assert 'weekday' in result
        valid_days = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
        assert result['weekday'] in valid_days

    def test_timestamp_is_positive(self):
        result = self._execute('timestamp')
        assert result.get('timestamp', 0) > 0

    def test_timestamp_ms_is_larger(self):
        result = self._execute('timestamp')
        assert result.get('ms', 0) > result.get('timestamp', 0)


class TestMemoryPlugin:
    """Test plugin memoria persistente."""

    def _execute(self, tool, params=None):
        from backend.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        return registry.execute('vio.memory', tool, params or {})

    def test_save_and_load(self):
        key = f'test_key_{id(self)}'
        save_result = self._execute('save', {'key': key, 'value': 'test_value_123'})
        assert save_result.get('success') is True
        load_result = self._execute('load', {'key': key})
        assert load_result.get('value') == 'test_value_123'
        # Cleanup
        self._execute('delete', {'key': key})

    def test_list_returns_dict(self):
        result = self._execute('list')
        assert 'count' in result
        assert 'keys' in result
        assert isinstance(result['keys'], list)

    def test_load_nonexistent(self):
        result = self._execute('load', {'key': 'definitely_nonexistent_key_xyz123'})
        assert 'error' in result

    def test_delete_nonexistent(self):
        result = self._execute('delete', {'key': 'definitely_nonexistent_key_xyz123'})
        assert 'error' in result


class TestPluginInfo:
    """Test metadata e struttura dei plugin."""

    def test_all_plugins_have_required_fields(self):
        from backend.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        for plugin_dict in registry.list_plugins():
            assert 'id' in plugin_dict
            assert 'name' in plugin_dict
            assert 'version' in plugin_dict
            assert 'description' in plugin_dict
            assert 'tools' in plugin_dict
            assert 'status' in plugin_dict

    def test_all_plugins_have_tools(self):
        from backend.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        for plugin_dict in registry.list_plugins():
            assert len(plugin_dict['tools']) > 0

    def test_all_tools_have_required_fields(self):
        from backend.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        for plugin_dict in registry.list_plugins():
            for tool in plugin_dict['tools']:
                assert 'name' in tool
                assert 'description' in tool
                assert 'parameters' in tool

    def test_plugin_ids_are_unique(self):
        from backend.plugins.registry import PluginRegistry
        registry = PluginRegistry()
        ids = [p['id'] for p in registry.list_plugins()]
        assert len(ids) == len(set(ids))

    def test_plugin_status_values(self):
        from backend.plugins.registry import PluginRegistry, PluginStatus
        registry = PluginRegistry()
        valid_statuses = {s.value for s in PluginStatus}
        for plugin_dict in registry.list_plugins():
            assert plugin_dict['status'] in valid_statuses
