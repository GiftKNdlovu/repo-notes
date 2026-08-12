# Context: repo-notes

Project notes generator for code repositories.

## Ubiquitous Language

### Language Classifier
Data-driven classifier that maps repository files to target programming language metadata based on file extensions, exact filenames, or matching rules.

### Detector Registry
The central seam providing access to language classification via `get_registry().classify(path)`.

### Language Info
Value object holding language metadata including canonical name, architectural category (backend, frontend, infra, database, etc.), and supported file extensions.
