.PHONY: install ingest train train-models predict simulate dashboard betting final all

install:
	pip install -e .

ingest:
	python -m src.cli ingest

train:
	python -m src.cli train

train-models:
	python -m src.cli train-models

predict:
	python -m src.cli predict --round $(ROUND)

simulate:
	python -m src.cli simulate --round $(ROUND)

betting:
	python -m src.cli betting

final:
	python -m src.cli final

update-r16:
	python -m src.cli update-r16

dashboard:
	streamlit run src/publish/dashboard.py

all: ingest train predict betting
