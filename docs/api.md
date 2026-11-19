# API та CLI JSON 1.0

```python
from sipl import parse, run, sem_P, evaluate, format_term

program = parse('begin R := X + 1 end')
execution = run(program, {'X': 4}, trace=True)
term = sem_P(program)
application = evaluate(term, {'X': 4}, trace=True)
assert execution.state == application.state == {'X': 4, 'R': 5}
print(format_term(term))
```

`parse` повертає `Prog`, `sem_P` — терм типу `TFS`, а `run` та `evaluate` — `Result`. Арифметичні терми належать `TFA`, логічні — `TFB`. Семантичний обчислювач виконує власне дерево термів і не викликає AST-інтерпретатор. Спільні компоненти — валідація стану, базові арифметичні операції, бюджет і моделі подій.

У бібліотечному API помилки синтаксису та некоректні аргументи викликають `SiplError` із `diagnostic`. Виявлені під час виконання невизначеність/ліміти повертаються в `Result`. API побудови термів очікує власні AST-вузли; сторонні або неправильно сконструйовані вузли можуть викликати `TypeError`. CLI перехоплює також надмірну вкладеність побудови та серіалізації.

## Конверт JSON

Усі шість команд підтримують `--json` після назви команди. Вивід — один JSON-об’єкт у stdout, діагностика також міститься в ньому. Формальна схема: `docs/cli.schema.json`, JSON Schema Draft 2020-12.

```json
{"schema_version":"1.0","command":"check","ok":true,"data":{"valid":true},"diagnostic":null}
```

| Команда | Поля `data` |
|---|---|
| `check` | `valid` |
| `parse` | `ast` — власні вузли з `type` і `span` |
| `run`, `trace`, `eval-term` | `status`, `state`, `steps`, `events`, `diagnostic` |
| `term` | `text`, `term` — текстове і структуроване подання |

За помилки до виконання `data=null`; за помилки виконання зберігаються проміжний стан і події. `command=null` можливе, якщо назву команди не розпізнано. `--help` має звичайну поведінку argparse: текст довідки та код 0.

| Код завершення | Значення |
|---|---|
| 0 | Успішна команда / завершене обчислення |
| 2 | Лексична/синтаксична помилка, некоректні аргументи, читання файла |
| 3 | Невизначена змінна під час обчислення |
| 4 | Ліміт кроків |
| 5 | Ресурсна межа |

`diagnostic` містить `code`, `message`, `span` (або null). Текст повідомлення може уточнюватися, стабільними є коди і структура. Межі схемою перевіряються структурно; семантичну коректність AST, наприклад належність операндів саме до Aexp, гарантує парсер, а не JSON Schema.

## Події

Кожна подія містить `index`, `kind`, `span`, знімок `state` і `details`. Індекси починаються з 0. Завершені вузли мають парні Before/After; за помилки After для незавершеного вузла відсутній.

| kind | Стабільні поля details |
|---|---|
| BeforeStatement, AfterStatement | `node` |
| VariableChanged | `name`, `old` (null, якщо змінної не було), `new` |
| ConditionChecked | `value`, `owner` (`If` або `While`) |
| RuleEnter | `rule`; для AF_IF — `condition`, `selected`; для AF_WH — `condition`, `iteration` |
| RuleApplied | `rule`; залежні від правила аргументи та результат |
| Finished | порожній об’єкт |
| Failed | `diagnostic`, `status` |

В `eval-term` події `RuleApplied` для `AF_S` містять `function`, `arguments`, `result`; `AF_DNM` — `name`, `result`; `AF_CONST` — `result`; `AF_AS` — `before`, `name`, `value`; `AF_SEQ`, `AF_IF`, `AF_WH`, `AF_ID` — `before`; `AF_WH` також `iterations`. Поточний стан після застосування правила міститься у спільному `state` події. `AF_CONST` — реалізаційна назва очевидного правила n(st)=n; решта імен узято з таблиць посібників.

Події доступні як `Result.events` у бібліотеці. Це журнал виконання, а не інтерактивний debugger: continue/breakpoints у цьому наборі не заявлено.
