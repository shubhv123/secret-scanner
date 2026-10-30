# Auto-generated Differential Parity Test Suite by DriftZero
# Target Library: setuptools (84.2.1)
import os
import sys
import json
import pytest
from pathlib import Path
from decimal import Decimal
from datetime import datetime, date

# Ensure workspace root and src directory are on sys.path
_repo_root = Path(__file__).resolve().parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
_src_dir = _repo_root / "src"
if _src_dir.exists() and str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

# Compatibility fix for Python 3.14+ PEP 649 deferred annotations with legacy Pydantic v1
try:
    import pydantic.main
    if hasattr(pydantic.main, "ModelMetaclass"):
        _orig_model_meta_new = pydantic.main.ModelMetaclass.__new__
        def _compat_model_meta_new(mcs, name, bases, namespace, **kwargs):
            if "__annotate_func__" in namespace and not namespace.get("__annotations__"):
                try:
                    namespace["__annotations__"] = namespace["__annotate_func__"](1)
                except Exception:
                    pass
            return _orig_model_meta_new(mcs, name, bases, namespace, **kwargs)
        pydantic.main.ModelMetaclass.__new__ = _compat_model_meta_new
except Exception:
    pass

GOLDEN_FILE = Path(__file__).resolve().parent / "golden.json"
IS_RECORDING = os.getenv("DRIFTZERO_RECORD_GOLDEN", "0") == "1"

# Module-level golden store
_golden_store: dict = {}

def _load_golden() -> dict:
    global _golden_store
    if _golden_store:
        return _golden_store
    if not GOLDEN_FILE.exists():
        if not IS_RECORDING:
            raise AssertionError(
                f"Golden baseline file '{GOLDEN_FILE}' not found! "
                "The old-version container must run with DRIFTZERO_RECORD_GOLDEN=1 first "
                "to record golden baseline outputs before running differential verification."
            )
        return _golden_store
    try:
        _golden_store.clear()
        _golden_store.update(json.loads(GOLDEN_FILE.read_text(encoding="utf-8")))
        return _golden_store
    except Exception as exc:
        raise AssertionError(f"Failed to read golden baseline file: {exc}")

def _save_golden():
    global _golden_store
    GOLDEN_FILE.write_text(json.dumps(_golden_store, indent=2, default=str), encoding="utf-8")


def _generate_sample_input_for_field(field_name: str, type_annotation: str = ""):
    name = field_name.lower()
    t_clean = type_annotation.lower().strip()

    if name == "postal_code":
        return "94105"
    if "email" in name:
        return "dev@example.com"
    if name in ("sender_country", "receiver_country", "country"):
        return "US"
    if name in ("amount", "amount_usd", "price", "rate", "fee", "balance", "cost", "fx_rate"):
        return 100.0
    if name in ("quantity", "count", "limit", "retries", "max_retries", "timeout_seconds", "attempt_count", "unit_price_cents", "qty"):
        return 5
    if name in ("created_at", "updated_at", "timestamp", "date"):
        return "2025-01-01T12:00:00"
    if name in ("is_", "has_", "active", "enabled", "requires_manual_compliance_review"):
        return False
    if name in ("tags", "list", "categories"):
        return ["item_1", "item_2"]
    if name in ("payload", "data", "meta", "metadata", "config", "data_object", "payload_snapshot"):
        return {"status": "ok", "env": "test"}
    if name == "street":
        return "123 Market St"
    if name == "city":
        return "San Francisco"
    if name == "sku":
        return "SKU-TEST-001"
    if name.endswith("_id") or name == "id" or name in ("order_id", "customer_id", "transaction_id", "trace_id", "actor_id", "event_id"):
        return f"test_{field_name}_123"
    if name == "primary_address":
        return {"street": "123 Market St", "city": "San Francisco", "postal_code": "94105"}
    if name == "items":
        return [{"sku": "SKU-001", "quantity": 2, "unit_price_cents": 500}]
    if name == "order":
        return {"order_id": "test_order_123", "created_at": "2025-01-01T12:00:00", "items": [{"sku": "SKU-1", "quantity": 1, "unit_price_cents": 100}]}
    if name == "raw_dict":
        return {"order_id": "test_order_123", "created_at": "2025-01-01T12:00:00", "items": [{"sku": "SKU-1", "quantity": 1, "unit_price_cents": 100}]}
    if name == "raw_json":
        return json.dumps({"order_id": "test_order_123", "created_at": "2025-01-01T12:00:00", "items": [{"sku": "SKU-1", "quantity": 1, "unit_price_cents": 100}]})
    if name == "raw_list" or ("list" in t_clean and "dict" in t_clean):
        return [{"trace_id": "test_trace_123", "attempt_count": 1, "payload": {"status": "ok"}, "scores": [0.2, 0.5, 0.8]}]
    if name == "prompt":
        return {"system_instruction": "Summarize", "user_transcript": "User dialog", "temperature": 0.5}
    if name in ("scores", "__root__", "root"):
        return [0.2, 0.5, 0.8]

    if "int" in t_clean and "list" not in t_clean:
        return 5
    if "float" in t_clean and "list" not in t_clean:
        return 10.5
    if "bool" in t_clean:
        return True
    if "list" in t_clean:
        if "float" in t_clean:
            return [0.2, 0.5, 0.8]
        if "int" in t_clean:
            return [1, 2, 3]
        return ["item_1", "item_2"]
    if "dict" in t_clean:
        return {"key": "value"}
    if "datetime" in t_clean or "date" in t_clean:
        return "2025-01-01T12:00:00"

    return f"sample_{field_name}"


def _build_model_sample_inputs(cls_obj, fallback=None):
    """
    Builds sample inputs at test runtime from the model's own fields
    (model_fields in Pydantic v2 or __fields__ in Pydantic v1, including all inherited ones).
    """
    fields_dict = getattr(cls_obj, "model_fields", None)
    if fields_dict is None:
        fields_dict = getattr(cls_obj, "__fields__", None)

    if not isinstance(fields_dict, dict):
        return dict(fallback or {})

    kwargs = dict(fallback or {})
    for f_name, f_info in fields_dict.items():
        type_str = ""
        if hasattr(f_info, "annotation") and f_info.annotation is not None:
            type_str = getattr(f_info.annotation, "__name__", str(f_info.annotation))
        elif hasattr(f_info, "type_") and f_info.type_ is not None:
            type_str = getattr(f_info.type_, "__name__", str(f_info.type_))
        elif hasattr(f_info, "outer_type_") and f_info.outer_type_ is not None:
            type_str = getattr(f_info.outer_type_, "__name__", str(f_info.outer_type_))

        if f_name not in kwargs or kwargs[f_name] is None:
            kwargs[f_name] = _generate_sample_input_for_field(f_name, type_str)
        elif kwargs[f_name] == f"sample_{f_name}" and type_str:
            kwargs[f_name] = _generate_sample_input_for_field(f_name, type_str)

    return kwargs


def _serialize_value(val, mode="json"):
    """
    Serializes models and Python values across legacy and modern library versions.
    Normalizes both sides through mode='json' (converts Decimals, datetimes, Enums, sets to JSON-safe types).
    """
    if val is None:
        return None

    if hasattr(val, "value"):
        return _serialize_value(val.value, mode=mode)

    # Modern Pydantic v2 / dataclasses with model_dump
    if hasattr(val, "model_dump") and callable(getattr(val, "model_dump")):
        if mode == "json":
            try:
                dumped = val.model_dump(mode="json")
                return _serialize_value(dumped, mode=mode)
            except Exception:
                try:
                    return json.loads(json.dumps(val.model_dump(), default=str))
                except Exception:
                    pass
        return val.model_dump()

    # Legacy Pydantic v1 / objects with dict()
    if hasattr(val, "dict") and callable(getattr(val, "dict")):
        if mode == "json":
            if hasattr(val, "json") and callable(getattr(val, "json")):
                try:
                    return json.loads(val.json())
                except Exception:
                    pass
            try:
                return json.loads(json.dumps(val.dict(), default=str))
            except Exception:
                pass
        return val.dict()

    if isinstance(val, str):
        s_val = val.strip()
        if (s_val.startswith("{") and s_val.endswith("}")) or (s_val.startswith("[") and s_val.endswith("]")):
            try:
                parsed_json = json.loads(s_val)
                return _serialize_value(parsed_json, mode=mode)
            except Exception:
                pass
        return val.replace("#/$defs/", "#/definitions/")

    if isinstance(val, (int, float, bool)):
        return val
    if isinstance(val, (list, tuple)):
        return [_serialize_value(item, mode=mode) for item in val]
    if isinstance(val, (set, frozenset)):
        serialized_items = [_serialize_value(item, mode=mode) for item in val]
        return sorted(serialized_items, key=lambda x: json.dumps(x, default=str) if isinstance(x, (dict, list)) else str(x))
    if isinstance(val, dict):
        norm_dict = {}
        for k, v in val.items():
            str_k = str(k)
            if str_k in ("$defs", "definitions"):
                str_k = "definitions"
            norm_dict[str_k] = _serialize_value(v, mode=mode)
        return norm_dict
    if isinstance(val, Decimal):
        return str(val) if mode == "json" else float(val)
    if isinstance(val, (datetime, date)):
        return val.isoformat()

    return str(val)


def _is_base_settings_subclass(cls_obj):
    try:
        if isinstance(cls_obj, type) and cls_obj.__name__ != "BaseSettings":
            return any(base.__name__ == "BaseSettings" for base in cls_obj.__mro__)
    except Exception:
        pass
    return False


def _get_field_env_vars_to_set(cls_obj, sample_kwargs):
    env_vars = {}
    env_prefix = ""
    model_config = getattr(cls_obj, "model_config", None)
    if isinstance(model_config, dict):
        env_prefix = model_config.get("env_prefix", "") or ""
    elif hasattr(model_config, "env_prefix"):
        env_prefix = getattr(model_config, "env_prefix", "") or ""

    if not env_prefix:
        cfg = getattr(cls_obj, "Config", None)
        if cfg and hasattr(cfg, "env_prefix"):
            env_prefix = getattr(cfg, "env_prefix", "") or ""

    fields_dict = getattr(cls_obj, "model_fields", None)
    if fields_dict is None:
        fields_dict = getattr(cls_obj, "__fields__", None)
    if not isinstance(fields_dict, dict):
        fields_dict = {k: None for k in sample_kwargs}

    for f_name, val in (sample_kwargs or {}).items():
        f_info = fields_dict.get(f_name)
        var_name = ""

        if f_info is not None:
            extra = getattr(getattr(f_info, "field_info", None), "extra", {})
            env_val = getattr(f_info, "env", None)
            if isinstance(extra, dict) and extra.get("env"):
                var_name = extra["env"]
            elif isinstance(env_val, str) and env_val:
                var_name = env_val
            elif getattr(getattr(f_info, "field_info", None), "env", None):
                var_name = getattr(f_info.field_info, "env")

            if not var_name:
                v_alias = getattr(f_info, "validation_alias", None)
                if isinstance(v_alias, str) and v_alias:
                    var_name = v_alias
                elif getattr(f_info, "has_alias", False) and isinstance(getattr(f_info, "alias", None), str):
                    var_name = f_info.alias

        if not var_name:
            var_name = f"{env_prefix}{f_name}".upper()

        if hasattr(val, "value"):
            val = val.value

        if isinstance(val, bool):
            str_val = "true" if val else "false"
        elif isinstance(val, (dict, list)):
            str_val = json.dumps(val)
        elif isinstance(val, (datetime, date)):
            str_val = val.isoformat()
        else:
            str_val = str(val)

        env_vars[var_name] = str_val
        env_vars[f"{env_prefix}{f_name}".upper()] = str_val

    return env_vars


def verify_base_settings_env_differential(mod_name: str, cls_name: str, cls_obj, sample_kwargs: dict = None):
    """
    Differential parity assertion for BaseSettings subclasses:
    Sets each field's environment variable, instantiates the model with no arguments,
    and records/verifies the resulting instance against golden.json.
    Restores original environment variables afterward.
    """
    global _golden_store
    golden_key = f"settings_env::{mod_name}.{cls_name}"

    final_kwargs = _build_model_sample_inputs(cls_obj, fallback=sample_kwargs)
    env_vars = _get_field_env_vars_to_set(cls_obj, final_kwargs)

    saved_env = {}
    keys_to_clean = []
    try:
        for k, v in env_vars.items():
            if k in os.environ:
                saved_env[k] = os.environ[k]
            else:
                keys_to_clean.append(k)
            os.environ[k] = v

        if IS_RECORDING:
            record = {}
            try:
                try:
                    instance = cls_obj(_env_file=None)
                except (TypeError, ValueError):
                    instance = cls_obj()
                record["status"] = "ok"
                record["output"] = _serialize_value(instance, mode="json")
            except Exception as exc:
                record["status"] = "error"
                record["error_type"] = type(exc).__name__

            _load_golden()
            _golden_store[golden_key] = record
            _save_golden()
            return

        golden = _load_golden()
        if golden_key not in golden:
            raise AssertionError(
                f"Missing golden baseline entry for BaseSettings '{mod_name}.{cls_name}'. "
                "Old-version container must record golden.json before verification."
            )

        expected = golden[golden_key]
        if expected["status"] == "ok":
            try:
                instance = cls_obj(_env_file=None)
            except (TypeError, ValueError):
                instance = cls_obj()
            actual_norm = _serialize_value(instance, mode="json")
            expected_norm = _serialize_value(expected["output"], mode="json")
            assert actual_norm == expected_norm, (
                f"Differential BaseSettings Parity Mismatch for '{cls_name}' when loaded from env vars:\n"
                f"Expected (Golden): {expected_norm}\n"
                f"Actual   (New):    {actual_norm}"
            )
        else:
            with pytest.raises(Exception) as exc_info:
                cls_obj()
            actual_type = exc_info.value.__class__.__name__
            expected_type = expected["error_type"]
            assert actual_type == expected_type, (
                f"Error type mismatch for BaseSettings '{cls_name}' loaded from env vars: "
                f"expected {expected_type}, got {actual_type}"
            )
    finally:
        for k in keys_to_clean:
            os.environ.pop(k, None)
        for k, v in saved_env.items():
            os.environ[k] = v


def verify_model_differential(mod_name: str, cls_name: str, cls_obj, sample_kwargs: dict = None):
    """
    Differential parity assertion for models:
    - Builds inputs at test runtime from model_fields or __fields__, including inherited ones.
    - Normalizes both sides through _serialize_value(mode="json") before comparing.
    - Compares error type only, not message.
    - For BaseSettings subclasses, runs environment variable check.
    """
    global _golden_store
    golden_key = f"model::{mod_name}.{cls_name}"

    runtime_inputs = _build_model_sample_inputs(cls_obj, fallback=sample_kwargs)
    final_kwargs = runtime_inputs if runtime_inputs else dict(sample_kwargs or {})

    if IS_RECORDING:
        record = {}
        try:
            instance = cls_obj(**final_kwargs)
            record["status"] = "ok"
            record["output"] = _serialize_value(instance, mode="json")
            record["model_dump"] = record["output"]
            record["model_dump_json"] = record["output"]
        except Exception as exc:
            record["status"] = "error"
            record["error_type"] = type(exc).__name__

        # Record error type on invalid / empty inputs
        try:
            cls_obj()
            record["empty_input_status"] = "ok"
        except Exception as exc:
            record["empty_input_status"] = "error"
            record["invalid_error_type"] = type(exc).__name__

        _load_golden()
        _golden_store[golden_key] = record
        _save_golden()

        # Runtime check for BaseSettings subclasses: set each field's env var and compare against golden
        if _is_base_settings_subclass(cls_obj):
            verify_base_settings_env_differential(mod_name, cls_name, cls_obj, sample_kwargs=final_kwargs)
        return

    # Verification Mode (New Container)
    golden = _load_golden()
    if golden_key not in golden:
        raise AssertionError(
            f"Missing golden baseline entry for model '{mod_name}.{cls_name}'. "
            "Old-version container must record golden.json before verification."
        )

    expected = golden[golden_key]

    if expected["status"] == "ok":
        instance = cls_obj(**final_kwargs)

        # Normalize both sides through _serialize_value(mode="json") before comparing
        actual_norm = _serialize_value(instance, mode="json")
        expected_norm = _serialize_value(
            expected.get("output") or expected.get("model_dump_json") or expected.get("model_dump"),
            mode="json"
        )
        assert actual_norm == expected_norm, (
            f"Differential Model Parity Mismatch for '{cls_name}':\n"
            f"Expected (Golden): {expected_norm}\n"
            f"Actual   (New):    {actual_norm}"
        )
    else:
        # Expected error on instantiation: compare error type only, not message
        with pytest.raises(Exception) as exc_info:
            cls_obj(**final_kwargs)
        actual_type = exc_info.value.__class__.__name__
        expected_type = expected["error_type"]
        assert actual_type == expected_type, (
            f"Error type mismatch for '{cls_name}': expected {expected_type}, got {actual_type}"
        )

    # Assert error type on invalid / empty inputs: compare error type only, not message
    if expected.get("empty_input_status") == "error":
        with pytest.raises(Exception) as exc_info:
            cls_obj()
        actual_type = exc_info.value.__class__.__name__
        expected_type = expected["invalid_error_type"]
        assert actual_type == expected_type, (
            f"Validation error type mismatch for invalid inputs on '{cls_name}': "
            f"expected {expected_type}, got {actual_type}"
        )

    # Runtime check for BaseSettings subclasses: set each field's env var and compare against golden
    if _is_base_settings_subclass(cls_obj):
        verify_base_settings_env_differential(mod_name, cls_name, cls_obj, sample_kwargs=final_kwargs)


def verify_function_differential(mod_name: str, fn_name: str, fn_obj, sample_kwargs: dict = None):
    """
    Differential parity assertion for functions:
    - Normalizes both sides through _serialize_value(mode="json") before comparing.
    - Compares error type only, not message.
    """
    global _golden_store
    golden_key = f"func::{mod_name}.{fn_name}"
    final_kwargs = dict(sample_kwargs or {})

    if IS_RECORDING:
        record = {}
        try:
            res = fn_obj(**final_kwargs)
            record["status"] = "ok"
            record["output"] = _serialize_value(res, mode="json")
        except Exception as exc:
            record["status"] = "error"
            record["error_type"] = type(exc).__name__

        _load_golden()
        _golden_store[golden_key] = record
        _save_golden()
        return

    # Verification Mode (New Container)
    golden = _load_golden()
    if golden_key not in golden:
        raise AssertionError(
            f"Missing golden baseline entry for function '{mod_name}.{fn_name}'. "
            "Old-version container must record golden.json before verification."
        )

    expected = golden[golden_key]

    if expected["status"] == "ok":
        res = fn_obj(**final_kwargs)
        actual_norm = _serialize_value(res, mode="json")
        expected_norm = _serialize_value(expected["output"], mode="json")
        assert actual_norm == expected_norm, (
            f"Differential Function Parity Mismatch for '{fn_name}':\n"
            f"Expected (Golden): {expected_norm}\n"
            f"Actual   (New):    {actual_norm}"
        )
    else:
        # Expected error on function execution: compare error type only, not message
        with pytest.raises(Exception) as exc_info:
            fn_obj(**final_kwargs)
        actual_type = exc_info.value.__class__.__name__
        expected_type = expected["error_type"]
        assert actual_type == expected_type, (
            f"Function error type mismatch for '{fn_name}': expected {expected_type}, got {actual_type}"
        )


def test_differential_parity_0_secret_scanner_cli():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from secret_scanner.cli import main

    # Differential Parity Test for Function: secret_scanner.cli.main
    sample_kwargs = {'args_list': 'sample_args_list'}
    verify_function_differential("secret_scanner.cli", "main", main, sample_kwargs)



def test_differential_parity_1_secret_scanner_formatter():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from secret_scanner.formatter import obfuscate_secret, format_console, format_json, format_markdown

    # Differential Parity Test for Function: secret_scanner.formatter.obfuscate_secret
    sample_kwargs = {'secret': 'sample_secret'}
    verify_function_differential("secret_scanner.formatter", "obfuscate_secret", obfuscate_secret, sample_kwargs)

    # Differential Parity Test for Function: secret_scanner.formatter.format_console
    sample_kwargs = {'findings': [{'trace_id': 'test_trace_123', 'attempt_count': 1, 'payload': {'status': 'ok'}, 'scores': [0.2, 0.5, 0.8]}]}
    verify_function_differential("secret_scanner.formatter", "format_console", format_console, sample_kwargs)

    # Differential Parity Test for Function: secret_scanner.formatter.format_json
    sample_kwargs = {'findings': [{'trace_id': 'test_trace_123', 'attempt_count': 1, 'payload': {'status': 'ok'}, 'scores': [0.2, 0.5, 0.8]}]}
    verify_function_differential("secret_scanner.formatter", "format_json", format_json, sample_kwargs)

    # Differential Parity Test for Function: secret_scanner.formatter.format_markdown
    sample_kwargs = {'findings': [{'trace_id': 'test_trace_123', 'attempt_count': 1, 'payload': {'status': 'ok'}, 'scores': [0.2, 0.5, 0.8]}]}
    verify_function_differential("secret_scanner.formatter", "format_markdown", format_markdown, sample_kwargs)



def test_differential_parity_2_secret_scanner_github_scanner():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from secret_scanner.github_scanner import GitHubScanner

    # Differential Parity Test for Model: secret_scanner.github_scanner.GitHubScanner
    sample_kwargs = _build_model_sample_inputs(GitHubScanner, fallback={'scanner': 'sample_scanner'})
    verify_model_differential("secret_scanner.github_scanner", "GitHubScanner", GitHubScanner, sample_kwargs)



def test_differential_parity_3_secret_scanner_hooks():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from secret_scanner.hooks import HookManager

    # Differential Parity Test for Model: secret_scanner.hooks.HookManager
    sample_kwargs = _build_model_sample_inputs(HookManager, fallback={'repo_path': 'sample_repo_path'})
    verify_model_differential("secret_scanner.hooks", "HookManager", HookManager, sample_kwargs)



def test_differential_parity_4_secret_scanner_rules():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from secret_scanner.rules import RuleMatcher, calculate_entropy

    # Differential Parity Test for Model: secret_scanner.rules.RuleMatcher
    sample_kwargs = _build_model_sample_inputs(RuleMatcher, fallback={'config_path': 'sample_config_path'})
    verify_model_differential("secret_scanner.rules", "RuleMatcher", RuleMatcher, sample_kwargs)

    # Differential Parity Test for Function: secret_scanner.rules.calculate_entropy
    sample_kwargs = {'text': 'sample_text'}
    verify_function_differential("secret_scanner.rules", "calculate_entropy", calculate_entropy, sample_kwargs)



def test_differential_parity_5_secret_scanner_scanner():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from secret_scanner.scanner import Scanner

    # Differential Parity Test for Model: secret_scanner.scanner.Scanner
    sample_kwargs = _build_model_sample_inputs(Scanner, fallback={'rule_matcher': 'sample_rule_matcher', 'num_threads': 5})
    verify_model_differential("secret_scanner.scanner", "Scanner", Scanner, sample_kwargs)


