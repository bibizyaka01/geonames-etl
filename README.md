# GeoNames ETL на Apache Airflow

Курсовая работа по предмету «Управление конфигурацией программного обеспечения».

Автор: Андреев Владимир Борисович.

## Назначение

Локальная платформа загрузки открытых географических данных GeoNames в PostgreSQL.
Основной акцент проекта — воспроизводимое развёртывание через Docker Compose,
конфигурация вне кода и автоматические проверки в GitHub Actions.

## Планируемая архитектура

- Apache Airflow 3 с Python 3.12 и CeleryExecutor: API server, scheduler,
  DAG processor, triggerer и масштабируемые workers.
- Redis как брокер задач.
- PostgreSQL 16: отдельные экземпляры для метаданных Airflow и DWH.
- Одноразовый init-контейнер для первоначальной настройки Airflow.
- Слои DWH: `stg`, `core`, `mart`.
- Три DAG: справочники, первичная загрузка и ежедневные изменения.
- Режим `lite` для разработки и `full` для полного набора данных.

Начальная конфигурация предусматривает одного worker. Масштабирование до трёх
workers проверяется после отладки загрузки.

## Структура

```text
dags/                  DAG Airflow
src/                   общий Python-код ETL
sql/init/              схемы и таблицы DWH
sql/transformations/   преобразования данных
docker/                скрипты настройки контейнеров
tests/                 проверки поведения ETL
```

## Текущее состояние

Созданы каркас проекта и Dockerfile собственного образа Airflow.
Compose, DAG и CI будут добавлены на следующих этапах.
Запуск всей платформы пока не реализован.

## Образ Airflow

Базовый образ: `apache/airflow:3.4.0-python3.12`. Один образ будет использоваться
всеми компонентами Airflow. Дополнительные зависимости устанавливаются при сборке
от пользователя `airflow`; установка пакетов при запуске не требуется.

В `requirements.txt` зафиксированы зависимости для CeleryExecutor, PostgreSQL,
HTTP-запросов и FAB auth manager (вход по логину и паролю).
Для потокового COPY используется Psycopg 3.

В `docker/constraints-3.12.txt` сохранён официальный список совместимых версий:
https://raw.githubusercontent.com/apache/airflow/constraints-3.4.0/constraints-3.12.txt

Constraints ограничивают версии зависимостей, но не устанавливают все перечисленные
пакеты. При обновлении Airflow нужно согласованно обновлять базовый образ,
версию Airflow в команде pip, requirements и constraints.

Сборка из каталога проекта:

```powershell
docker build -t geonames-airflow:dev .
```

Проверка образа без запуска платформы:

```powershell
docker run --rm geonames-airflow:dev python --version
docker run --rm geonames-airflow:dev version
docker run --rm geonames-airflow:dev pip check
```

В образ копируются DAG, общий Python-код и SQL. `.dockerignore` ограничивает
контекст сборки необходимыми файлами, исключая `.env` и каталог `.git`.

## Настройки

Скопируйте шаблон настроек в PowerShell из каталога проекта:

```powershell
Copy-Item .env.example .env
```

Файл `.env` предназначен для локальных настроек и исключён из Git.
Перед запуском платформы потребуется заполнить пароли; пустые значения в шаблоне
не предназначены для работающих сервисов.

## Данные

Источник: https://download.geonames.org/export/dump/

Данные GeoNames распространяются по лицензии Creative Commons Attribution 4.0:
https://creativecommons.org/licenses/by/4.0/
