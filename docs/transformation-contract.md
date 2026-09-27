# Data Transformation & Validation Contract

## Purpose

The transformation layer converts validated source-specific customer
objects into a clean, standardized representation suitable for downstream
loading into the data warehouse/database.

## Current Source Contract

The Stripe extractor returns:

    List[Customer]

where `Customer` is the Pydantic model defined in:

    src/models/customer.py

The extractor performs initial Pydantic validation using:

    Customer.model_validate(raw)

Therefore, the transformation layer is responsible for downstream
data-quality transformation rather than duplicating source parsing.

## Source Fields

The current Stripe Customer model contains:

- id
- object
- name
- email
- phone
- description
- address
- shipping
- balance
- currency
- delinquent
- invoice_prefix
- tax_exempt
- default_source
- invoice_settings
- metadata
- created
- livemode
- test_clock
- preferred_locales

## Transformation Responsibilities

The transformation layer will handle:

1. Data cleaning
2. Null/empty-value normalization
3. String normalization
4. Date/time normalization
5. Source-field mapping
6. Output validation
7. Invalid-record handling

## Important Constraints

- Do not duplicate Stripe extraction logic.
- Do not modify the existing Customer source model unless integration
  demonstrates a concrete requirement.
- Do not perform currency conversion unless the project specification
  requires it.
- Preserve source identifiers.
- Do not silently discard records that fail downstream validation.
- Transformation logic should be independently unit-testable.

## Initial Data Quality Rules

The following rules are candidates for implementation:

- Trim leading/trailing whitespace from string fields.
- Treat empty strings as missing values where appropriate.
- Normalize email addresses to lowercase.
- Normalize currency codes to lowercase ISO-style codes.
- Convert Stripe Unix timestamps into a consistent datetime representation.
- Preserve optional fields as null when no valid value exists.
- Preserve customer IDs without modification.

## Test Data

The repository provides a Stripe test-data seeder containing customers
with:

- Different countries
- Different address completeness
- Different customer plans
- Different metadata
- Optional/missing address fields

These records can be used to exercise transformation behavior.

## Downstream Contract

The final transformed structure must be confirmed against the database
loader/schema before the transformation output is considered stable.