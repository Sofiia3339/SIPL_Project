# SIPL Language Toolkit

Реалізовано формальну граматику, парсер із власним AST та SourceSpan, інтерпретатор, трасування, CLI, побудову й незалежне обчислення семантичних термів. Обрані завдання: **CORE-01 (0.5), CORE-02 (1.5), CORE-03 (2.0), CORE-04 (1.0), CORE-05 (1.0), SEM-01 (2.0), SEM-02 (2.0)**. Заявлена сума — **10.0 балів**. Критерії наведено в `docs/scope.md`.

## Обрані завдання

| ID | Завдання | Бали |
|---|---|---:|
| CORE-01 | Формальна граматика SIPL та опис лексики | 0.5 |
| CORE-02 | Парсер, власне типізоване AST та SourceSpan | 1.5 |
| CORE-03 | Інтерпретатор та контроль ліміту кроків | 2.0 |
| CORE-04 | Події виконання та трасування | 1.0 |
| CORE-05 | CLI-команди та JSON-контракт | 1.0 |
| SEM-01 | Автоматична побудова семантичного терму | 2.0 |
| SEM-02 | Обчислення терму та журнал застосованих правил | 2.0 |

## Запуск на macOS / Linux

Потрібен Python 3.10 або новіший. Виконання й основні тести не потребують сторонніх бібліотек.
Відкрийте термінал у розпакованій папці `SIPL_Project`:

```bash
python3 --version
export PYTHONPATH="$PWD/src"
python3 -m sipl check examples/power.sipl
python3 -m sipl run examples/power.sipl --state '{"X":5,"Y":2}'
```

Очікуваний кінцевий стан: `{"X":5,"Y":0,"R":25}`.
`export` діє для поточної вкладки термінала. Після відкриття нової вкладки повторіть його.

Альтернатива — встановити готовий пакет із архіву, без завантажень із мережі:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --no-index dist/sipl_sofia_toolkit-1.0.0-py3-none-any.whl
sipl run examples/power.sipl --state '{"X":5,"Y":2}'
```

Для встановлення з коду: `python3 -m pip install .` (потрібен доступ для встановлення збирача setuptools). Пакет локальний; публікація на PyPI не заявляється.

## Команди

```bash
python3 -m sipl parse examples/power.sipl --json
python3 -m sipl check examples/power.sipl
python3 -m sipl run examples/gcd.sipl --state '{"M":8,"N":16}'
python3 -m sipl trace examples/power.sipl --state '{"X":5,"Y":2}' --json
python3 -m sipl term examples/power.sipl
python3 -m sipl eval-term examples/power.sipl --state '{"X":5,"Y":2}' --json
python3 -m sipl run examples/sum_even.sipl --state '{"N":3}'
python3 -m sipl run examples/undefined.sipl
python3 -m sipl trace examples/infinite.sipl --max-steps 30 --json
```

`check` перевіряє синтаксис; визначеність змінних залежить від початкового стану й перевіряється під час виконання. У `run` журнал вимкнений; `trace` вмикає журнал AST; `eval-term` вмикає журнал формальних правил. Параметр `--state` — JSON-об’єкт, `--max-steps` — додатне ціле число, за замовчуванням 10000.

| Приклад | Вхід | Очікуваний результат |
|---|---|---|
| power | X=5, Y=2 | R=25, Y=0 |
| gcd | M=8, N=16 | M=N=8 |
| sum_even | N=3 | R=12, I=4 |
| branch | X=-7 | R=7 |
| undefined | порожній стан | E_UNDEFINED |
| infinite | max-steps=30 | E_LIMIT |

## Тести й покриття

```bash
export PYTHONPATH="$PWD/src"
python3 -m unittest discover -s tests -v
```

Для всіх перевірок, включно зі схемою JSON та вимірюванням покриття:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
export PYTHONPATH="$PWD/src"
python3 -m coverage run --source=sipl -m unittest discover -s tests -v
python3 -m coverage report --fail-under=80
```

Звіт фактично виконаної перевірки — `docs/validation.txt`; вимірювання охоплює весь `src/sipl`, включно з CLI та семантикою. Без jsonschema пропускається лише тест формальної JSON-схеми; решта тестів працює на стандартній бібліотеці. Тести містять 16 позитивних і 23 негативні синтаксичні приклади, 10 еталонних семантичних термів та перевірки класів вхідних даних.

## Структура

- `grammar/sipl.ebnf` — формальна граматика.
- `src/sipl/lexer.py`, `parser.py`, `ast.py` — лексика, синтаксис, власна модель AST.
- `src/sipl/interpreter/` — безпосереднє виконання AST.
- `src/sipl/semantics/` — TFA/TFB/TFS, sem_P/S/A/B, застосування термів.
- `src/sipl/runtime.py`, `diagnostics.py` — стан, події, результати, діагностика.
- `src/sipl/cli.py` — команди та JSON-контракт.
- `examples/`, `tests/` — приклади й автоматичні перевірки.
- `docs/` — специфікація, результати демонстрацій.

 Граматика та реалізаційні уточнення описані в `docs/language.md`, API — у `docs/api.md`.

## Обмеження та здача

Це базова SIPL із цілими числами, `+ - * = > ¬ ∨`. Рекурсивні функції, IDE й формальні доведення загальної коректності не входять до обраних завдань. Перевищення бюджету не доводить нескінченність циклу. За помилки повертається проміжний стан; лише `finished` означає кінцевий результат.
