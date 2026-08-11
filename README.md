# csvconv

`csvconv` is a small command-line tool for converting CSV files into SQLite
databases and exporting SQLite tables back to CSV.

## Features

- Convert a CSV file into a SQLite database with one table.
- Export a SQLite table to a CSV file.
- Use the CSV filename as the default SQLite table name.
- Override the table name with `--table`.
- Append a new table to an existing database with `--append`.
- Preserve all imported CSV values as SQLite `TEXT` columns.
- Validate CSV headers before import, including empty and duplicate column names.
- Quote SQLite identifiers safely, so table and column names can contain special
  characters.
- Export the first user table by default when no table is specified.
- Escape embedded newlines during CSV export for easier line-oriented processing.

## Requirements

- Python 3.9 or newer.

The tool only uses Python standard library modules at runtime.

## Installation

Install the package from the project directory:

```bash
pip install .
```

This provides the `csvconv` command defined in `pyproject.toml`.

## Usage

Convert a CSV file to a new SQLite database:

```bash
csvconv csv2sqlite input.csv output.sqlite
```

Use a custom table name:

```bash
csvconv csv2sqlite input.csv output.sqlite --table people
```

Append a new table to an existing database:

```bash
csvconv csv2sqlite other.csv output.sqlite --append --table other_people
```

Export a SQLite table to CSV:

```bash
csvconv sqlite2csv output.sqlite exported.csv --table people
```

If `--table` is omitted during export, `csvconv` uses the first user-created
table found in the database.

## Development

Run the script directly without installing:

```bash
python csvconv.py csv2sqlite input.csv output.sqlite
python csvconv.py sqlite2csv output.sqlite exported.csv
```
