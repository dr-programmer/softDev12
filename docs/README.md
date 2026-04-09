# Документация

Този директория съдържа документацията за проекта, организирана в три секции:

1. **[Ползване на API-а](api_usage.md)** — Структура на входни и изходни данни, HTTP кодове за грешки, примери за всички endpoints
2. **[Архитектура на проекта](architecture.md)** — Ключови класове, методи, обосновка на решения, UML диаграми
3. **[Самоанализ на работата](self_analysis.md)** — Анализ на спазване на SOLID принципите

## Генериране на PDF

За генериране на PDF от Markdown файловете може да се използва:

```bash
# С pandoc (ако е инсталиран)
pandoc docs/api_usage.md docs/architecture.md docs/self_analysis.md -o docs/documentation.pdf

# Или чрез VS Code разширения за Markdown to PDF
```

Mermaid диаграмите в `architecture.md` могат да се визуализират:
- В GitHub (автоматично)
- В VS Code с разширение "Markdown Preview Mermaid Support"
- На https://mermaid.live/
