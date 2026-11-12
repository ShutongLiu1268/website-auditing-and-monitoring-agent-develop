# Audit Definition BSON Serialization Design

## Status

Approved by user on 2026-10-09.

## Context

`POST /api/audits` validates an `AuditCreateRequest`, builds an `AuditDefinition`, and persists it through `AuditDefinitionRepository`. `PageTarget.url` is typed as Pydantic `HttpUrl`. `AuditDefinitionRepository.create()` currently calls `definition.model_dump()` in Python mode and passes the result directly to PyMongo.

Python-mode serialization retains `HttpUrl` objects. PyMongo cannot encode them, producing `bson.errors.InvalidDocument` and a 500 response.

## Goals

- Persist audit definitions containing valid `HttpUrl` targets without BSON errors.
- Store target URLs as plain strings.
- Preserve Mongo-native `datetime` values such as `created_at`.
- Prevent regression at the actual repository/BSON boundary.

## Non-goals

- Change URL validation rules.
- Change API request or response schemas.
- Change serialization behavior of other repositories.
- Convert all Pydantic models to JSON-mode serialization.

## Recommended approach

Keep Python-mode model serialization in `AuditDefinitionRepository.create()`, then normalize only the nested audit target URLs before calling `insert_one`:

1. Dump the `AuditDefinition` to a document.
2. Rebuild each target mapping with `url` converted using `str()`.
3. Insert the normalized document.
4. Return the original `AuditDefinition` unchanged.

This keeps the fix localized to the failing persistence boundary. Using `model_dump(mode="json")` is rejected because it would convert datetimes to ISO strings, weakening Mongo date storage and query behavior. A global `PageTarget` serializer is also rejected because it changes behavior outside this persistence use case.

## Testing

Add a repository unit test that:

- Creates an `AuditDefinition` with an `HttpUrl` target.
- Calls `AuditDefinitionRepository.create()` with a mocked collection.
- BSON-encodes the document passed to `insert_one`.
- Verifies the stored URL is a string.
- Verifies `created_at` remains a `datetime`.
- Verifies the repository returns the original definition.

The test must fail before the fix because BSON encoding rejects the original `HttpUrl`, then pass after the minimal repository change.

## Verification

Run the targeted repository test, the full backend pytest suite, Ruff checks/formatting, basedpyright, and the required Snyk code scan. Existing user changes outside the audit persistence files must remain untouched.
