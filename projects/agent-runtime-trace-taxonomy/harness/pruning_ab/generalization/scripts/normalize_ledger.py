#!/usr/bin/env python3
"""Provider-normalized call-level record builder + byte-identity assertions (shared by both shims/analysis).
Implements the mission section-6 schema. Anthropic effective-cost decomposition kept ONLY for anthropic.
"""
import json, hashlib

SCHEMA_FIELDS=["study","provider","requested_model","served_model","task_id","arm","replicate","call_index",
 "timestamp","input_tokens","output_tokens","cache_read_tokens","cache_creation_tokens","cached_tokens",
 "provider_cost_usd","latency_seconds","messages_before_chars","messages_after_chars","characters_removed",
 "changed_message_count","first_changed_message_index","stable_prefix_chars","transform_module_sha256",
 "transform_function_sha256","raw_provider_usage"]

def blank(**kw):
    r={k:None for k in SCHEMA_FIELDS}; r["study"]="cross_model_generalization_v1"; r["raw_provider_usage"]={}
    r.update(kw); return r

# Anthropic canonical effective cost (UNCHANGED from the frozen study). Only valid for anthropic provider.
def anthropic_effective_cost(input_tok, cache_read, cache_creation, output_tok):
    def z(x): return x or 0
    return z(input_tok) + 0.1*z(cache_read) + 1.25*z(cache_creation) + 5*z(output_tok)

def assert_byte_identical(before_msgs, after_msgs, label="C0/SHAM"):
    b=json.dumps(before_msgs, sort_keys=True); a=json.dumps(after_msgs, sort_keys=True)
    if b!=a:
        raise AssertionError(f"{label} NOT byte-identical: before_sha={hashlib.sha256(b.encode()).hexdigest()[:12]} after_sha={hashlib.sha256(a.encode()).hexdigest()[:12]}")
    return True

def provider_native_cost_vs_c0(arm_cost, c0_cost):
    """Cross-provider: relative cost vs that model's OWN C0. Never apply anthropic weights here."""
    if not c0_cost: return None
    return (arm_cost - c0_cost)/c0_cost
