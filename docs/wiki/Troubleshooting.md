# Troubleshooting

This page contains common troubleshooting tips for setup and execution issues.

## Dependency installation problems

If the installation fails:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Test failures

Run the suite with verbosity:

```bash
pytest tests/ -v
```

Check whether the issue is related to:

- missing dependencies
- config errors
- unsupported Python version
- a data-fetch logic issue

## No data returned

If the pipeline cannot fetch data:

- verify the symbol list in `config/config.yaml`
- confirm the date range is valid
- check the cache directory configuration
- verify the environment has internet access if external data is used

## Model training errors

If a model fails during training:

- validate the feature matrix is not empty
- check that model configuration keys exist
- confirm the chosen model type is supported
- inspect the pipeline logs for exception details

## Logging

The project uses `loguru` and writes logs to the configured file in `logging.file`.

Check the logs for the exact failure step:

```bash
tail -f logs/trading_system.log
```

## Need more help

If you are contributing code or extending functionality, review the project README and the relevant source modules under `src/`.
