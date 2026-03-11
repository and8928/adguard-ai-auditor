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
