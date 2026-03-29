from ..schemas.adguard_models import FilterRule
from collections import defaultdict


# class AnalysisService:

def get_status(reason):
    # Логика определения: заблокировано или пропущено
    blocked_reasons = ['FilteredBlackList', 'FilteredSafeBrowsing', 'FilteredSafeSearch']
    if reason in blocked_reasons:
        return 'Blocked'
    return 'Allowed'


def clean_and_prepare_logs(row_data):
    filter_result = set()
    results = {'Allowed': [], 'Blocked': []}

    for entry in row_data:
        domain = entry.get('question', {}).get('name', 'unknown')
        # print(domain)
        if domain not in filter_result:
            filter_result.add(domain)
            reason = entry.get('reason', '')
            filterId = entry.get('filterId', '')
            status = get_status(reason)
            results[status].append({'domain': domain, 'filterId': filterId})
    return results


# def clean_filtering(row_data):
#     optimized = optimize_filtering_rules(row_data)
#     final_result = apply_forced_domains(
#         rules_objects=optimized['clean_rules_objects'],
#         # force_block=DOMAINS_TO_BLOCK,
#         # force_unblock=DOMAINS_TO_UNBLOCK
#     )
#     print(f"final_result = {final_result}")
#     return final_result


def parse_rule_filtering(rule: str) -> FilterRule:
    """Breaks down a single rule into its components"""
    original_raw = rule.strip()
    rule = original_raw

    if not rule or rule.startswith('!'):  # пустые и комментарии
        return FilterRule(original_raw, False, '', [], '', False)

    is_exception = rule.startswith('@@')
    if is_exception:
        rule = rule[2:]

    if '$' in rule:
        pattern_part, modifiers_part = rule.split('$', 1)
        modifiers = [m.strip() for m in modifiers_part.split(',') if m.strip()]
    else:
        pattern_part = rule
        modifiers = []

    domain = ''
    if pattern_part.startswith('||'):
        domain = pattern_part[2:].rstrip('^')
        is_valid = bool(domain) and ' ' not in domain
    elif pattern_part.startswith('|'):
        domain = pattern_part[1:].rstrip('^')
        is_valid = True
    else:
        domain = pattern_part.rstrip('^')
        is_valid = bool(domain)

    return FilterRule(
        raw=original_raw,
        is_exception=is_exception,
        domain_pattern=pattern_part,
        modifiers=modifiers,
        domain=domain,
        is_valid=is_valid
    )


def optimize_filtering_rules(rules: list[str]) -> dict:
    """
    Filter processing function: removes duplicates, resolves conflicts based on priorities,
    preserves blocking rules with equal strength, and collects statistics.
    """
    parsed = [parse_rule_filtering(r) for r in rules]

    valid_rules = [r for r in parsed if r.is_valid and r.domain]
    invalid_rules = [r for r in parsed if not r.is_valid and r.raw and not r.raw.startswith('!')]

    grouped = defaultdict(list)
    for r in valid_rules:
        key = (r.domain_pattern, tuple(sorted(r.modifiers)))
        grouped[key].append(r)

    clean_rules = {}
    warnings_merged = []
    # full_domain_list= []

    for key, rules_list in grouped.items():
        domain_pattern, modifiers = key

        blocks = [r for r in rules_list if not r.is_exception]
        exceptions = [r for r in rules_list if r.is_exception]

        max_block_pri = 1 if any(b.is_important for b in blocks) else 0
        max_exc_pri = 1 if any(e.is_important for e in exceptions) else 0

        if blocks and not exceptions:
            winner = next(b for b in blocks if (1 if b.is_important else 0) == max_block_pri)
            clean_rules[winner.domain]= winner
            continue

        if exceptions and not blocks:
            winner = next(e for e in exceptions if (1 if e.is_important else 0) == max_exc_pri)
            clean_rules[winner.domain]= winner
            continue

        if max_block_pri > max_exc_pri:
            winner = next(b for b in blocks if b.is_important)
            clean_rules[winner.domain]= winner

        elif max_exc_pri > max_block_pri:
            winner = next(e for e in exceptions if e.is_important)
            clean_rules[winner.domain]= winner

        else:
            winner = next(b for b in blocks if (1 if b.is_important else 0) == max_block_pri)
            clean_rules[winner.domain]= winner

            warnings_merged.append({
                'domain': winner.domain,
                'pattern': domain_pattern,
                'priority_level': 'important' if max_block_pri == 1 else 'normal',
                'conflict_rules': list(set(r.raw for r in rules_list)),  # Уникальный список исходников
                'kept_rule': winner.raw
            })

    return {
        # 'clean_rules_raw': [r.raw for r in clean_rules],
        'clean_rules_objects': clean_rules,
        # 'full_domain_list': [f.domain for f in clean_rules],
        'warnings_merged': warnings_merged,
        'invalid_rules': [r.raw for r in invalid_rules],
        'stats': {
            'total_input_lines': len(rules),
            'valid_processed': len(valid_rules),
            'total_clean': len(clean_rules),
            'duplicates_and_conflicts_removed': len(valid_rules) - len(clean_rules),
            'equal_power_conflicts': len(warnings_merged)
        }
    }


def apply_forced_domains(
        rules_objects: list[FilterRule],
        force_block: list[str] = None,
        force_unblock: list[str] = None
) -> dict:
    """
    Hard blocking and unblocking is applied.
    Removes conflicting (and weaker) rules from the current list
    and adds comments for visual separation.
    """
    force_block = set([d.strip().replace('||', '').replace('^', '') for d in (force_block or [])])
    force_unblock = set([d.strip().replace('||', '').replace('^', '') for d in (force_unblock or [])])

    intersection = force_block.intersection(force_unblock)
    if intersection:
        raise ValueError(f"Конфликт во входных данных! Домены в обоих списках: {intersection}")

    final_objects = []
    removed_due_to_conflict = []

    for r in rules_objects:
        if not r.is_valid and r.raw.startswith('!'):
            final_objects.append(r)
            continue

        conflict = False

        if r.domain in force_block:
            if r.is_exception:
                conflict = True
            elif not r.is_important:
                conflict = True

        if r.domain in force_unblock:
            if not r.is_exception:
                conflict = True
            elif not r.is_important:
                conflict = True

        if conflict:
            removed_due_to_conflict.append(r.raw)
        else:
            final_objects.append(r)

    if force_block:
        final_objects.append(parse_rule_filtering("! === PERMANENT BLOCK ==="))
        for domain in sorted(force_block):
            final_objects.append(parse_rule_filtering(f"||{domain}^$important"))

    if force_unblock:
        final_objects.append(parse_rule_filtering("! === PERMANENT UNBLOCK ==="))
        for domain in sorted(force_unblock):
            final_objects.append(parse_rule_filtering(f"@@||{domain}^$important"))

    return {
        # 'rules_objects': final_objects,
        'rules_raw': [r.raw for r in final_objects],
        'removed_conflicts': removed_due_to_conflict
    }
