# Senior-year-internship-final-project

A simple Python calculator that estimates glaze drying time for a batch in a ceramics studio, built because we often couldn’t predict when pieces would be ready.

## About
At the studio we often couldn’t predict when a batch of glazed pieces would be dry enough to fire. I wrote a small Python tool that takes simple inputs—piece size (via a shape-based surface-area proxy), number of coats, glaze type, and environment (humidity / airflow / temperature)—and returns an estimated drying time with a small safety buffer. It’s fast, transparent, and runs in a plain terminal. In day-to-day use, it was consistently close.

## Quick Start
```bash
python3 glaze_dry_time.py

