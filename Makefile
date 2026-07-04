.PHONY: help install format lint test run clean

help:
	@echo "Доступные команды:"
	@echo "  make install  - установить проект в editable-режиме с dev-зависимостями"
	@echo "  make format   - отформатировать исходный код"
	@echo "  make lint     - проверить код линтером"
	@echo "  make test     - запустить тесты"
	@echo "  make run      - запустить CLI"
	@echo "  make clean    - удалить служебные артефакты"

install:
	python -m pip install -e ".[dev]"

format:
	python -m ruff format src tests

lint:
	python -m ruff check src tests

test:
	python -m pytest

run:
	employees

clean:
	python -c "from pathlib import Path; import shutil; [shutil.rmtree(path, ignore_errors=True) for path in Path('.').rglob('__pycache__')]; [shutil.rmtree(Path(name), ignore_errors=True) for name in ('.pytest_cache', 'build', 'dist')]; [shutil.rmtree(path, ignore_errors=True) for path in Path('.').rglob('*.egg-info') if path.is_dir()]"
