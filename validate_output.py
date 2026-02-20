#!/usr/bin/env python3
"""
Output Format Validator
Validates that the API response matches the exact required format for test cases.
"""

import json
import sys
from typing import Any


def validate_suspicious_account(account: dict[str, Any], index: int) -> list[str]:
    """Validate a single suspicious account entry."""
    errors = []
    
    # Check required fields
    required_fields = ["account_id", "suspicion_score", "detected_patterns", "ring_id"]
    for field in required_fields:
        if field not in account:
            errors.append(f"Account {index}: Missing required field '{field}'")
    
    # Validate types
    if "account_id" in account and not isinstance(account["account_id"], str):
        errors.append(f"Account {index}: 'account_id' must be a string")
    
    if "suspicion_score" in account:
        if not isinstance(account["suspicion_score"], (int, float)):
            errors.append(f"Account {index}: 'suspicion_score' must be a number")
        elif not (0 <= account["suspicion_score"] <= 100):
            errors.append(f"Account {index}: 'suspicion_score' must be between 0 and 100")
    
    if "detected_patterns" in account and not isinstance(account["detected_patterns"], list):
        errors.append(f"Account {index}: 'detected_patterns' must be an array")
    
    if "ring_id" in account and account["ring_id"] is not None:
        if not isinstance(account["ring_id"], str):
            errors.append(f"Account {index}: 'ring_id' must be a string or null")
    
    return errors


def validate_fraud_ring(ring: dict[str, Any], index: int) -> list[str]:
    """Validate a single fraud ring entry."""
    errors = []
    
    # Check required fields
    required_fields = ["ring_id", "member_accounts", "pattern_type", "risk_score", "member_count"]
    for field in required_fields:
        if field not in ring:
            errors.append(f"Ring {index}: Missing required field '{field}'")
    
    # Validate types
    if "ring_id" in ring and not isinstance(ring["ring_id"], str):
        errors.append(f"Ring {index}: 'ring_id' must be a string")
    
    if "member_accounts" in ring:
        if not isinstance(ring["member_accounts"], list):
            errors.append(f"Ring {index}: 'member_accounts' must be an array")
        elif not all(isinstance(m, str) for m in ring["member_accounts"]):
            errors.append(f"Ring {index}: All 'member_accounts' must be strings")
    
    if "pattern_type" in ring and not isinstance(ring["pattern_type"], str):
        errors.append(f"Ring {index}: 'pattern_type' must be a string")
    
    if "risk_score" in ring:
        if not isinstance(ring["risk_score"], (int, float)):
            errors.append(f"Ring {index}: 'risk_score' must be a number")
        elif not (0 <= ring["risk_score"] <= 100):
            errors.append(f"Ring {index}: 'risk_score' must be between 0 and 100")
    
    if "member_count" in ring:
        if not isinstance(ring["member_count"], int):
            errors.append(f"Ring {index}: 'member_count' must be an integer")
        elif ring["member_count"] < 1:
            errors.append(f"Ring {index}: 'member_count' must be at least 1")
        # Validate member_count matches member_accounts length
        elif "member_accounts" in ring and ring["member_count"] != len(ring["member_accounts"]):
            errors.append(
                f"Ring {index}: 'member_count' ({ring['member_count']}) "
                f"does not match length of 'member_accounts' ({len(ring['member_accounts'])})"
            )
    
    return errors


def validate_summary(summary: dict[str, Any]) -> list[str]:
    """Validate the summary section."""
    errors = []
    
    # Check required fields
    required_fields = [
        "total_accounts_analyzed",
        "suspicious_accounts_flagged",
        "fraud_rings_detected",
        "processing_time_seconds"
    ]
    for field in required_fields:
        if field not in summary:
            errors.append(f"Summary: Missing required field '{field}'")
    
    # Validate types
    int_fields = ["total_accounts_analyzed", "suspicious_accounts_flagged", "fraud_rings_detected"]
    for field in int_fields:
        if field in summary and not isinstance(summary[field], int):
            errors.append(f"Summary: '{field}' must be an integer")
    
    if "processing_time_seconds" in summary:
        if not isinstance(summary["processing_time_seconds"], (int, float)):
            errors.append(f"Summary: 'processing_time_seconds' must be a number")
    
    return errors


def validate_response(response: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate the complete API response.
    Returns (is_valid, errors).
    """
    errors = []
    
    # Check top-level structure
    required_sections = ["suspicious_accounts", "fraud_rings", "summary"]
    for section in required_sections:
        if section not in response:
            errors.append(f"Missing required section '{section}'")
            return False, errors
    
    # Validate suspicious_accounts
    if not isinstance(response["suspicious_accounts"], list):
        errors.append("'suspicious_accounts' must be an array")
    else:
        for i, account in enumerate(response["suspicious_accounts"]):
            errors.extend(validate_suspicious_account(account, i))
        
        # Check sorting (descending by suspicion_score)
        scores = [a.get("suspicion_score", 0) for a in response["suspicious_accounts"]]
        if scores != sorted(scores, reverse=True):
            errors.append("'suspicious_accounts' must be sorted by 'suspicion_score' in descending order")
    
    # Validate fraud_rings
    if not isinstance(response["fraud_rings"], list):
        errors.append("'fraud_rings' must be an array")
    else:
        for i, ring in enumerate(response["fraud_rings"]):
            errors.extend(validate_fraud_ring(ring, i))
    
    # Validate summary
    if not isinstance(response["summary"], dict):
        errors.append("'summary' must be an object")
    else:
        errors.extend(validate_summary(response["summary"]))
    
    # Cross-validation
    if isinstance(response["suspicious_accounts"], list) and isinstance(response["summary"], dict):
        if "suspicious_accounts_flagged" in response["summary"]:
            expected = response["summary"]["suspicious_accounts_flagged"]
            actual = len(response["suspicious_accounts"])
            if expected != actual:
                errors.append(
                    f"Summary 'suspicious_accounts_flagged' ({expected}) "
                    f"does not match actual count ({actual})"
                )
    
    if isinstance(response["fraud_rings"], list) and isinstance(response["summary"], dict):
        if "fraud_rings_detected" in response["summary"]:
            expected = response["summary"]["fraud_rings_detected"]
            actual = len(response["fraud_rings"])
            if expected != actual:
                errors.append(
                    f"Summary 'fraud_rings_detected' ({expected}) "
                    f"does not match actual count ({actual})"
                )
    
    return len(errors) == 0, errors


def main():
    """Main validation function."""
    if len(sys.argv) < 2:
        print("Usage: python validate_output.py <response.json>")
        print("   or: python validate_output.py - (read from stdin)")
        sys.exit(1)
    
    # Read JSON
    if sys.argv[1] == "-":
        data = json.load(sys.stdin)
    else:
        with open(sys.argv[1], 'r') as f:
            data = json.load(f)
    
    # Validate
    is_valid, errors = validate_response(data)
    
    # Report
    if is_valid:
        print("✅ VALIDATION PASSED")
        print(f"   - {len(data['suspicious_accounts'])} suspicious accounts")
        print(f"   - {len(data['fraud_rings'])} fraud rings")
        print(f"   - {data['summary']['total_accounts_analyzed']} total accounts")
        return 0
    else:
        print("❌ VALIDATION FAILED")
        print(f"\nFound {len(errors)} error(s):\n")
        for error in errors:
            print(f"  • {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
