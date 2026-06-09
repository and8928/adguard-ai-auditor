"""
Unit tests for analysis_service.py — rule parsing, optimization, and log cleaning.
"""
import pytest
from src.adguard_auditor.services.analysis_service import (
    parse_rule_filtering,
    optimize_filtering_rules,
    clean_and_prepare_logs,
    get_status,
    apply_blocks_to_rules,
    apply_unblocks_to_rules,
    apply_forced_domains,
)




class TestGetStatus:
    def test_blocked_reasons(self):
        assert get_status("FilteredBlackList") == "Blocked"
        assert get_status("FilteredSafeBrowsing") == "Blocked"
        assert get_status("FilteredSafeSearch") == "Blocked"

    def test_allowed_reasons(self):
        assert get_status("NotFilteredNotFound") == "Allowed"
        assert get_status("NotFilteredWhiteList") == "Allowed"
        assert get_status("") == "Allowed"




class TestCleanAndPrepareLogs:
    def test_groups_allowed_and_blocked(self, sample_querylog_entries):
        result = clean_and_prepare_logs(sample_querylog_entries)
        assert "Allowed" in result
        assert "Blocked" in result

    def test_removes_duplicates(self, sample_querylog_entries):
        result = clean_and_prepare_logs(sample_querylog_entries)
        allowed_domains = [e["domain"] for e in result["Allowed"]]
        # analytics.google.com appears twice in input but only once in output
        assert allowed_domains.count("analytics.google.com") == 1

    def test_correct_counts(self, sample_querylog_entries):
        result = clean_and_prepare_logs(sample_querylog_entries)
        # 3 unique allowed, 2 unique blocked
        assert len(result["Allowed"]) == 3
        assert len(result["Blocked"]) == 2

    def test_empty_input(self):
        result = clean_and_prepare_logs([])
        assert result == {"Allowed": [], "Blocked": []}




class TestParseRuleFiltering:
    def test_simple_domain(self):
        rule = parse_rule_filtering("||example.com^")
        assert rule.domain == "example.com"
        assert rule.is_exception is False
        assert rule.is_valid is True
        assert rule.modifiers == []

    def test_exception_rule(self):
        rule = parse_rule_filtering("@@||example.com^")
        assert rule.domain == "example.com"
        assert rule.is_exception is True
        assert rule.is_valid is True

    def test_important_modifier(self):
        rule = parse_rule_filtering("||example.com^$important")
        assert rule.domain == "example.com"
        assert rule.is_important is True

    def test_multiple_modifiers(self):
        rule = parse_rule_filtering("||example.com^$important,third-party")
        assert rule.is_important is True
        assert rule.is_third_party is True
        assert len(rule.modifiers) == 2

    def test_exception_with_important(self):
        rule = parse_rule_filtering("@@||example.com^$important")
        assert rule.is_exception is True
        assert rule.is_important is True

    def test_comment_is_invalid(self):
        rule = parse_rule_filtering("! This is a comment")
        assert rule.is_valid is False

    def test_empty_string_is_invalid(self):
        rule = parse_rule_filtering("")
        assert rule.is_valid is False

    def test_single_pipe_domain(self):
        rule = parse_rule_filtering("|example.com^")
        assert rule.domain == "example.com"
        assert rule.is_valid is True

    def test_bare_domain(self):
        rule = parse_rule_filtering("example.com")
        assert rule.domain == "example.com"
        assert rule.is_valid is True

    def test_raw_preserved(self):
        raw = "  ||example.com^$important  "
        rule = parse_rule_filtering(raw)
        assert rule.raw == raw.strip()




class TestOptimizeFilteringRules:
    def test_removes_duplicates(self):
        rules = ["||example.com^", "||example.com^"]
        result = optimize_filtering_rules(rules)
        assert result.stats.total_clean == 1
        assert result.stats.duplicates_and_conflicts_removed == 1

    def test_different_domains_with_different_modifiers_coexist(self):
        """Rules for different domains are always kept independently."""
        rules = ["||ads.com^$important", "@@||cdn.com^"]
        result = optimize_filtering_rules(rules)
        assert result.stats.total_clean == 2
        assert "ads.com" in result.clean_rules_objects
        assert "cdn.com" in result.clean_rules_objects

    def test_same_domain_different_modifiers_last_group_wins(self):
        """Same domain with different modifier sets: last processed group overwrites in output dict."""
        rules = ["||example.com^$important", "@@||example.com^"]
        result = optimize_filtering_rules(rules)
        # Both are valid and processed, but output dict is keyed by domain,
        # so only one survives — this documents the current behavior
        assert result.stats.total_clean == 1

    def test_equal_power_conflict_generates_warning(self):
        """Block and exception of equal power should generate a warning."""
        rules = ["||example.com^", "@@||example.com^"]
        result = optimize_filtering_rules(rules)
        assert len(result.warnings_merged) == 1
        assert result.warnings_merged[0].domain == "example.com"

    def test_comments_and_empty_lines_skipped(self):
        rules = ["! comment", "", "||valid.com^"]
        result = optimize_filtering_rules(rules)
        assert result.stats.total_clean == 1

    def test_stats_are_correct(self, sample_filter_rules):
        result = optimize_filtering_rules(sample_filter_rules)
        assert result.stats.total_input_lines == len(sample_filter_rules)
        assert result.stats.total_clean <= result.stats.valid_processed




class TestApplyBlocksToRules:
    def test_add_new_block(self):
        optimized = optimize_filtering_rules(["||existing.com^"])
        rules, stats = apply_blocks_to_rules(optimized, ["newdomain.com"])
        assert stats["added"] == 1
        assert any("newdomain.com" in r for r in rules)

    def test_already_blocked(self):
        optimized = optimize_filtering_rules(["||existing.com^"])
        rules, stats = apply_blocks_to_rules(optimized, ["existing.com"])
        assert stats["already_blocked"] == 1

    def test_overwrite_exception(self):
        optimized = optimize_filtering_rules(["@@||exception.com^"])
        rules, stats = apply_blocks_to_rules(optimized, ["exception.com"])
        assert stats["overwritten_exceptions"] == 1


class TestApplyUnblocksToRules:
    def test_add_new_unblock(self):
        optimized = optimize_filtering_rules(["||existing.com^"])
        rules, stats = apply_unblocks_to_rules(optimized, ["newdomain.com"])
        assert stats["added"] == 1
        assert any("@@||newdomain.com^" in r for r in rules)

    def test_overwrite_block(self):
        optimized = optimize_filtering_rules(["||blocked.com^"])
        rules, stats = apply_unblocks_to_rules(optimized, ["blocked.com"])
        assert stats["overwritten_blocks"] == 1

    def test_already_unblocked(self):
        optimized = optimize_filtering_rules(["@@||already.com^"])
        rules, stats = apply_unblocks_to_rules(optimized, ["already.com"])
        assert stats["already_unblocked"] == 1




class TestApplyForcedDomains:
    def test_conflict_raises_error(self):
        """Passing the same domain to both force_block and force_unblock should raise ValueError."""
        rules = [parse_rule_filtering("||example.com^")]
        with pytest.raises(ValueError, match="Конфликт"):
            apply_forced_domains(rules, force_block=["example.com"], force_unblock=["example.com"])

    def test_force_block_adds_important_rule(self):
        rules = [parse_rule_filtering("||existing.com^")]
        result = apply_forced_domains(rules, force_block=["newblock.com"])
        assert any("||newblock.com^$important" in r for r in result["rules_raw"])

    def test_force_unblock_adds_exception(self):
        rules = [parse_rule_filtering("||existing.com^")]
        result = apply_forced_domains(rules, force_unblock=["unblock.com"])
        assert any("@@||unblock.com^$important" in r for r in result["rules_raw"])
