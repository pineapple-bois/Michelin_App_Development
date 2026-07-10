# Michelin Guide to France

An interactive Dash application for exploring Michelin-rated restaurants, French socioeconomic data, and wine appellations across France.

## Links and recognition

- [Live application](https://restaurant-guide-france.net)
- First place in [Plotly's Autumn App Challenge 2024](https://community.plotly.com/t/autumn-app-challenge/87373/26)

## Application pages

- **Guide:** Search French locations, filter restaurants by geography and Michelin rating, and select map markers for restaurant details.
- **Analysis:** Compare restaurant distributions and rankings across regions, departments, and arrondissements.
- **Economics:** Explore socioeconomic indicators alongside Michelin restaurant distributions and optional starred-restaurant overlays.
- **Wine:** Browse French AOCs by region or appellation, show regional outlines and starred restaurants, and select an appellation for generated information.

## Technology

Built with Python 3.12, Dash, Flask, Plotly, pandas, GeoPandas, Flask-Caching, and the OpenAI API.

## Local setup

```bash
git clone https://github.com/pineapple-bois/michelin-guide-france.git
cd michelin-guide-france

python3.12 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -r requirements_dev.txt
```

`requirements.txt` installs the application itself in editable mode. This is required because the active Michelin Guide year is derived from the installed package version.

On Windows, activate the environment with `.venv\Scripts\activate`.

## Environment variables

Create a `.env` file in the repository root:

```dotenv
APP_ENV=development
OPENAI_API_KEY=<your-openai-api-key>
FLASK_SECRET_KEY=<local-development-secret>
```

- `OPENAI_API_KEY` is required by the current import-time OpenAI client and powers Wine appellation information.
- `FLASK_SECRET_KEY` is required in production. It is optional locally, where an omitted value produces a temporary key and sessions reset after restart.
- `OPENAI_REQUEST_LIMIT` optionally sets the generated-information limit per session; the default is `10`.
- `CACHE_TYPE` and `CACHE_DEFAULT_TIMEOUT` optionally configure Flask-Caching; the defaults are process-local `SimpleCache` and `3600` seconds.
- `FORCE_HTTPS` optionally overrides automatic production HTTPS handling.
- `DASH_DEBUG` optionally enables Dash debug mode; the default is false.
- `APP_ENV`, `FLASK_ENV`, or `DASH_ENV` set to `production`, or the presence of Heroku's `DYNO`, enables production defaults.

## Running and testing

Start the application:

```bash
python michelin_app.py
```

Then open [http://127.0.0.1:8050](http://127.0.0.1:8050).

Run the test suite from the repository root:

```bash
python -m pytest
```

The tests do not send OpenAI requests, but application import still requires `OPENAI_API_KEY` to be configured.

## Versioning and annual data

The package version in `pyproject.toml` is the source for the active Michelin Guide year. Version `2026.0` selects Guide year `2026` and runtime data under `assets/data/2026/`. Annual data releases reset the version to `<YEAR>.0`; maintenance releases against the same Guide data may use `<YEAR>.1`, `<YEAR>.2`, and so on.

Annual Michelin restaurant and aggregate geography products come from the public ET repository:

[https://github.com/pineapple-bois/Michelin_Rated_Restaurants](https://github.com/pineapple-bois/Michelin_Rated_Restaurants)

The app consumes approved France products from a local checkout under `data/products/france/<YEAR>/`. The manual release-preparation command is:

```bash
python scripts/load_annual_data.py --et-root ../Michelin_Rated_Restaurants
```

The loader is disabled before 1 April of the current calendar year. It copies only the explicit annual manifest into `assets/data/<YEAR>/`, leaves `assets/data/wine_regions_aoc_area.geojson` untouched, refreshes the package version to `<YEAR>.0`, imports the app, and runs the full test suite. It does not clone, download, run the ET pipeline, commit, tag, push, deploy, or modify the ET repository.

For remote LAN binding to test changes on smaller devices locally set:

```python
if __name__ == '__main__':
    app.run_server(
        debug=CONFIG.debug,
        host="0.0.0.0",
        port=8050,
    )
```

## Deployment

The production process declared in `Procfile` is:

```text
web: gunicorn michelin_app:server
```

The deployment uses Python 3.12 and installs the GIS system packages declared in `Aptfile`. Production requires stable `FLASK_SECRET_KEY` and `OPENAI_API_KEY` values. HTTPS defaults to enabled when the environment is detected as production.

## Project documentation

See [AGENTS.md](AGENTS.md) for the current architecture, module ownership, operating conventions, and validation guidance.

## Licence and attribution

This project is released under the [MIT Licence](LICENSE.md).

The Michelin Star logo is by Nikolaos Dimos and is used under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) via Wikimedia Commons.
