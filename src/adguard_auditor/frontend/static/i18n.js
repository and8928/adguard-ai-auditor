/* ===================================================
   i18n Localization Support
   =================================================== */

const translations = {
    en: {
        // Sidebar
        "sidebar.title": "AdGuard AI Auditor",
        "sidebar.settings": "Analysis Settings",
        "settings.model": "AI Model",
        "settings.limit": "Log Limit",
        "limit.100": "100 records",
        "limit.1000": "1000 records",
        "limit.10000": "10000 records",
        "limit.0": "All records",
        "settings.prompt": "Additional AI Instructions",
        "placeholder.prompt": "E.g.: wbsg8v.xyz is my domain, do not block",
        "sidebar.rules": "AI Rules",
        "btn.add_rule": "＋",

        // Main Content Header
        "main.title": "Audit Dashboard",
        "main.subtitle": "Intelligent DNS Log Analysis for AdGuard Home",
        "btn.run_audit": "Run Audit",
        "btn.run_audit.loading": "Analysis running...",
        "btn.fetch_data": "Get AdGuard Data",
        "btn.fetch_data.loading": "Fetching data...",
        "btn.run_analysis": "Run Analysis",
        "btn.run_analysis.loading": "Analyzing...",
        "btn.clear_cache": "Clear Cache",

        // Stepper
        "stepper.title": "Analysis Progress",
        "step.fetch": "Fetch logs from AdGuard",
        "step.clean": "Clean & group data",
        "step.llm": "Data analysis",
        "step.result": "Result",

        // Stats
        "stat.block": "Block",
        "stat.unblock": "Unblock",
        "stat.test": "Test",
        "stat.total": "Total",

        // Results Section
        "results.title": "Analysis Results",
        "btn.apply_changes": "✅ Apply selected changes",
        "btn.applying": "Applying...",
        "tab.block": "🛑 Block",
        "tab.unblock": "🟢 Unblock",
        "tab.test": "⚠️ Test",
        "tab.summary": "📋 Summary",
        "tab.filters": "🌐 Current Rules",
        "label.select_all": "Select all",

        // Table Headers
        "table.domain": "Domain",
        "table.reason": "Reason",
        "table.confidence": "Confidence",
        "table.type": "Type",
        "table.modifiers": "Modifiers",

        // Empty States
        "empty.rules": "No custom rules.<br>Add a rule to let the AI consider your preferences.",
        "empty.filters": "Click \"Load\" to fetch current active filter rules.",
        "empty.no_rules": "No custom rules found.",
        "empty.no_results": "Ready to work",
        "empty.no_results_desc": "Configure the settings in the sidebar and click \"Run Audit\" to start DNS log analysis.",
        "empty.no_recommendations": "No recommendations",

        // Current Rules Card
        "cr.title": "Current Rules",
        "cr.refresh": "↻ Load",
        "cr.search_ph": "Search domain...",
        "cr.filter_all": "All types",
        "cr.filter_block": "🛑 Block only",
        "cr.filter_exception": "🟢 Exceptions only",
        "cr.type_block": "🛑 Block",
        "cr.type_exception": "🟢 Exception",
        "cr.to_block": "Block",
        "cr.to_unblock": "Unblock",
        "cr.delete": "Delete",
        "cr.confirm_delete": "Delete the rule for {0}?",
        "cr.none_found": "No rules match your filter.",
        "cr.showing": "Showing {0} of {1} rules",
        "toast.rule_type_changed": "Rule type changed",
        "toast.rule_type_error": "Error changing rule type",

        // Modal
        "modal.title_new": "New Rule",
        "modal.title_edit": "Edit Rule",
        "modal.name": "Name",
        "modal.name_ph": "E.g.: My domains",
        "modal.text": "Rule text (prompt)",
        "modal.text_ph": "E.g.: Domain wbsg8v.xyz is my personal server, do not block it",
        "modal.desc": "Description (optional)",
        "modal.desc_ph": "Short description",
        "btn.cancel": "Cancel",
        "btn.create": "Create",
        "btn.save": "Save",
        "btn.edit": "✏️",
        "btn.delete": "✕",

        // App.js Dynamic Strings
        "toast.conn_lost": "Connection to server lost",
        "toast.audit_success": "Analysis completed successfully!",
        "toast.audit_error": "Analysis error",
        "toast.no_domains_selected": "No domains selected",
        "toast.changes_applied": "Changes applied",
        "toast.rule_enabled": "Rule enabled",
        "toast.rule_disabled": "Rule disabled",
        "toast.rule_update_error": "Error updating rule",
        "toast.rule_deleted": "Rule deleted",
        "toast.rule_delete_error": "Error deleting rule",
        "toast.fill_required": "Please fill in the rule name and text",
        "toast.rule_created": "Rule created",
        "toast.rule_create_error": "Error creating rule",
        "toast.rule_updated": "Rule updated",
        "toast.network_error": "Network error",
        "step.fetching_count": "Fetched records: {0}",
        "step.connecting": "Connecting to AdGuard...",
        "step.cleaning": "Cleaning & grouping...",
        "step.cleaned_stats": "Allowed: {0}, Blocked: {1}",
        "step.llm_start": "Analyzing via {0}...",
        "step.llm_thinking": "{0} is processing...",
        "step.llm_done": "Analysis finished",
        "step.llm_done_usage": "Analysis finished · in {0} / out {1} tokens",
        "step.est_tokens": "≈ {0} tokens → AI",
        "step.result_usage": "Done · {0} tokens total",
        "step.done": "Done",
        "step.err_conn": "Connection error",
        "step.err_general": "An error occurred",
        "filters.loading": "Loading...",
        "filters.total": "Total rules: {0}",
        "filters.error": "Load error: {0}",
        "summary.placeholder": "The analysis summary will be displayed here after completion.",
        "cache.status": "Cached: {0} ({1} records)",
        "cache.empty": "No cached data",
        "cache.cleared": "Cache cleared",
        "toast.fetch_success": "Data fetched and cached successfully!",
        "toast.no_cache": "No cached data. Run 'Get AdGuard Data' first.",
        "step.from_cache": "Using cached data"
    },
    ru: {
        // Sidebar
        "sidebar.title": "AdGuard AI Auditor",
        "sidebar.settings": "Настройки анализа",
        "settings.model": "Модель анализа",
        "settings.limit": "Лимит логов",
        "limit.100": "100 записей",
        "limit.1000": "1000 записей",
        "limit.10000": "10000 записей",
        "limit.0": "Все записи",
        "settings.prompt": "Дополнительные указания для ИИ",
        "placeholder.prompt": "Например: wbsg8v.xyz - это мой домен, не блокировать",
        "sidebar.rules": "Правила анализа",
        "btn.add_rule": "＋",

        // Main Content Header
        "main.title": "Панель аудита",
        "main.subtitle": "Интеллектуальный анализ DNS-логов AdGuard Home",
        "btn.run_audit": "Запустить аудит",
        "btn.run_audit.loading": "Анализ запущен...",
        "btn.fetch_data": "Получить данные AdGuard",
        "btn.fetch_data.loading": "Получение данных...",
        "btn.run_analysis": "Запустить анализ",
        "btn.run_analysis.loading": "Анализируем...",
        "btn.clear_cache": "Очистить кэш",

        // Stepper
        "stepper.title": "Прогресс анализа",
        "step.fetch": "Сбор логов из AdGuard",
        "step.clean": "Очистка и группировка",
        "step.llm": "Анализ данных",
        "step.result": "Результат",

        // Stats
        "stat.block": "Блокировать",
        "stat.unblock": "Разблокировать",
        "stat.test": "Проверить",
        "stat.total": "Всего",

        // Results Section
        "results.title": "Результаты анализа",
        "btn.apply_changes": "✅ Применить выбранные изменения",
        "btn.applying": "Применение...",
        "tab.block": "🛑 Блокировать",
        "tab.unblock": "🟢 Разблокировать",
        "tab.test": "⚠️ Проверить",
        "tab.summary": "📋 Сводка",
        "tab.filters": "🌐 Текущие правила",
        "label.select_all": "Выбрать все",

        // Table Headers
        "table.domain": "Домен",
        "table.reason": "Причина",
        "table.confidence": "Уверенность",
        "table.type": "Тип",
        "table.modifiers": "Модификаторы",

        // Empty States
        "empty.rules": "Нет пользовательских правил.<br>Добавьте правило, чтобы ИИ учитывал ваши предпочтения.",
        "empty.filters": "Нажмите «Загрузить», чтобы получить актуальные правила фильтрации.",
        "empty.no_rules": "Нет пользовательских правил",
        "empty.no_results": "Готов к работе",
        "empty.no_results_desc": "Настройте параметры в боковой панели и нажмите «Запустить аудит», чтобы начать анализ DNS-логов.",
        "empty.no_recommendations": "Нет рекомендаций",

        // Current Rules Card
        "cr.title": "Текущие правила",
        "cr.refresh": "↻ Загрузить",
        "cr.search_ph": "Поиск домена...",
        "cr.filter_all": "Все типы",
        "cr.filter_block": "🛑 Только блокировки",
        "cr.filter_exception": "🟢 Только исключения",
        "cr.type_block": "🛑 Блок",
        "cr.type_exception": "🟢 Исключение",
        "cr.to_block": "Заблокировать",
        "cr.to_unblock": "Разблокировать",
        "cr.delete": "Удалить",
        "cr.confirm_delete": "Удалить правило для {0}?",
        "cr.none_found": "Нет правил, соответствующих фильтру.",
        "cr.showing": "Показано {0} из {1} правил",
        "toast.rule_type_changed": "Тип правила изменён",
        "toast.rule_type_error": "Ошибка при смене типа правила",

        // Modal
        "modal.title_new": "Новое правило",
        "modal.title_edit": "Редактировать правило",
        "modal.name": "Название",
        "modal.name_ph": "Например: Мои домены",
        "modal.text": "Текст правила (промпт)",
        "modal.text_ph": "Например: Домен wbsg8v.xyz - это мой личный сервер, его нельзя блокировать",
        "modal.desc": "Описание (необязательно)",
        "modal.desc_ph": "Краткое описание",
        "btn.cancel": "Отмена",
        "btn.create": "Создать",
        "btn.save": "Сохранить",
        "btn.edit": "✏️",
        "btn.delete": "✕",

        // App.js Dynamic Strings
        "toast.conn_lost": "Потеряно соединение с сервером",
        "toast.audit_success": "Анализ успешно завершён!",
        "toast.audit_error": "Ошибка при анализе",
        "toast.no_domains_selected": "Не выбрано ни одного домена",
        "toast.changes_applied": "Изменения применены",
        "toast.rule_enabled": "Правило включено",
        "toast.rule_disabled": "Правило выключено",
        "toast.rule_update_error": "Ошибка при обновлении правила",
        "toast.rule_deleted": "Правило удалено",
        "toast.rule_delete_error": "Ошибка при удалении",
        "toast.fill_required": "Заполните название и текст правила",
        "toast.rule_created": "Правило создано",
        "toast.rule_create_error": "Ошибка при создании",
        "toast.rule_updated": "Правило обновлено",
        "toast.network_error": "Ошибка сети",
        "step.fetching_count": "Получено записей: {0}",
        "step.connecting": "Подключение к AdGuard...",
        "step.cleaning": "Очистка и группировка...",
        "step.cleaned_stats": "Allowed: {0}, Blocked: {1}",
        "step.llm_start": "Анализ через {0}...",
        "step.llm_thinking": "{0} обрабатывает запрос...",
        "step.llm_done": "Анализ завершён",
        "step.llm_done_usage": "Анализ завершён · вход {0} / выход {1} токенов",
        "step.est_tokens": "≈ {0} токенов → ИИ",
        "step.result_usage": "Готово · всего {0} токенов",
        "step.done": "Готово",
        "step.err_conn": "Ошибка соединения",
        "step.err_general": "Произошла ошибка",
        "filters.loading": "Загрузка...",
        "filters.total": "Всего правил: {0}",
        "filters.error": "Ошибка загрузки: {0}",
        "summary.placeholder": "Здесь будет отображена сводка анализа после завершения.",
        "cache.status": "Кэш: {0} ({1} записей)",
        "cache.empty": "Нет закэшированных данных",
        "cache.cleared": "Кэш очищен",
        "toast.fetch_success": "Данные получены и закэшированы!",
        "toast.no_cache": "Нет закэшированных данных. Сначала нажмите «Получить данные AdGuard».",
        "step.from_cache": "Используем закэшированные данные"
    }
};

let currentLang = localStorage.getItem('lang') || 'en';

function t(key, ...args) {
    let translation = translations[currentLang][key] || translations['en'][key] || key;
    args.forEach((arg, i) => {
        translation = translation.replace(`{${i}}`, arg);
    });
    return translation;
}

function updateDOMTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const textTags = ['DIV', 'SPAN', 'P', 'H1', 'H2', 'H3', 'LABEL', 'TH', 'TD', 'BUTTON', 'OPTION'];
        if (textTags.includes(el.tagName)) {
            el.innerHTML = t(key);
        }
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        el.placeholder = t(key);
    });

    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        el.title = t(key);
    });

    // Update tabs counts since they might have been overwritten if they are inside buttons
    if (typeof window.updateTabCounts === 'function' && window.state && window.state.results) {
        window.updateTabCounts(
            (window.state.results.domains_to_block || []).length,
            (window.state.results.domains_to_unblock || []).length,
            (window.state.results.domains_to_test || []).length
        );
    } else if (typeof window.updateTabCounts === 'function') {
        window.updateTabCounts(0, 0, 0);
    }
}

function setLanguage(lang) {
    if (translations[lang]) {
        currentLang = lang;
        localStorage.setItem('lang', lang);
        updateDOMTranslations();

        // Rerender dynamic components if needed
        if (typeof window.renderRules === 'function' && window.state && window.state.rules) {
            window.renderRules();
        }
        if (typeof window.renderResults === 'function' && window.state && window.state.results) {
            window.renderResults(window.state.results);
        }
        if (typeof window.renderCurrentRules === 'function' && window.state && window.state.currentRules) {
            window.renderCurrentRules();
        }

        // Update language switcher UI
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.lang === lang);
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    updateDOMTranslations();
});
