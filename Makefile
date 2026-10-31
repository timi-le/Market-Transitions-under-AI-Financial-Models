.PHONY: test reproduce pdf validate

test:
	python -m unittest discover -s tests -v

reproduce: test
	python code/synthetic_study.py
	python code/market_study.py
	python code/sensitivity.py
	python code/build_figures.py

pdf:
	latexmk -pdf -interaction=nonstopmode -halt-on-error -jobname=public_review main.tex
	cp public_review.pdf manuscript.pdf

validate:
	python code/validate_release.py
