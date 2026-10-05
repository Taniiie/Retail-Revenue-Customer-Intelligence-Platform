# Data Quality & Analytics QA Test Cases
## Retail Revenue & Customer Intelligence Platform

> **DATA TRANSPARENCY NOTICE**: All test cases and empirical execution results in this document are evaluated against **100% synthetic** retail data generated for portfolio analytics demonstration.

---

## Executive Summary

This document establishes the formal **Data Quality & Analytics QA Test Case Repository** for the platform. It covers 22 automated test cases spanning Data Completeness, Uniqueness, Range Validity, Referential Integrity, Chronological Consistency, Status Alignment, and Cross-Platform Financial Reconciliation across SQL, Python, and Power BI.

---

## Formal Test Case Execution Table

| Test ID | Category | Test Description | Expected Result | Actual Result | Status | Severity |
|:---|:---|:---|:---|:---|:---:|:---:|
| **DQ-01** | Completeness | Orders table primary key `order_id` has zero nulls | `0 nulls` | `0 nulls` | **PASSED** | CRITICAL |
| **DQ-02** | Uniqueness | Orders table `order_id` is strictly unique | `5,842 unique` | `5,842 unique` | **PASSED** | CRITICAL |
| **DQ-03** | Uniqueness | Customers table `customer_id` is strictly unique | `1,498 unique` | `1,498 unique` | **PASSED** | CRITICAL |
| **DQ-04** | Validity | Product catalog contains exactly 40 active SKUs | `40 products` | `40 products` | **PASSED** | HIGH |
| **DQ-05** | Validity | Order items have strictly positive quantity (>0) and unit prices (>0) | `0 invalid` | `0 invalid` | **PASSED** | CRITICAL |
| **DQ-06** | Consistency | Actual delivery date is on or after order placement date | `0 violations` | `0 violations` | **PASSED** | HIGH |
| **DQ-07** | Referential Integrity | Order items foreign key `order_id` exists in Orders table | `0 orphans` | `0 orphans` | **PASSED** | CRITICAL |
| **DQ-08** | Referential Integrity | Orders foreign key `customer_id` exists in Customers table | `0 orphans` | `0 orphans` | **PASSED** | CRITICAL |
| **DQ-09** | Consistency | Order status aligns with shipping delivery status | `0 conflicts` | `0 conflicts` | **PASSED** | HIGH |
| **REC-01** | Reconciliation | Total Revenue matches across SQL, Python RFM, and Power BI | `$3,990,811.00` | `$3,990,811.00` | **PASSED** | CRITICAL |
| **REC-02** | Reconciliation | Total Order count matches across SQL and Power BI | `5,842 orders` | `5,842 orders` | **PASSED** | CRITICAL |
| **REC-03** | Reconciliation | Active Customer count matches across RFM and Power BI | `1,107 active` | `1,107 active` | **PASSED** | HIGH |
| **REC-04** | Reconciliation | Average Order Value (AOV) matches benchmark | `$683.12` | `$683.12` | **PASSED** | HIGH |
| **REC-05** | Reconciliation | Gross Profit matches across line-item sum and category summary | `$1,240,548.65` | `$1,240,548.65` | **PASSED** | CRITICAL |
| **REC-06** | Reconciliation | Gross Profit Margin % matches benchmark | `31.09%` | `31.09%` | **PASSED** | HIGH |
| **REC-07** | Reconciliation | Carrier SLA Compliance Rate matches across shipping fact and SQL Q17 | `74.47%` | `74.47%` | **PASSED** | HIGH |
| **REC-08** | Reconciliation | Champions RFM segment customer count (254) and revenue ($2,193,910.01) | `254 / $2,193,910.01` | `254 / $2,193,910.01` | **PASSED** | HIGH |
| **REC-09** | Cohort Bounds | Cohort Month 0 retention is strictly 100.0% across all cohorts | `100.0%` | `100.0%` | **PASSED** | CRITICAL |
| **REC-10** | Cohort Retention | Cohort Month 1 average retention rate matches benchmark | `40.98%` | `40.98%` | **PASSED** | HIGH |
| **REC-11** | Cohort Retention | Cohort Month 6 simple arithmetic average retention rate | `19.54%` | `19.54%` | **PASSED** | HIGH |
| **REC-12** | LTV Trajectory | Cohort Month 12 realized cumulative LTV matches dataset average | `$3,377.90` | `$3,377.90` | **PASSED** | HIGH |
| **REC-13** | Completeness | All 9 Power BI Star Schema CSV data sources exist | `9 files` | `9 files` | **PASSED** | CRITICAL |

---

## Execution Summary

* **Total Test Cases Executed**: 22
* **Passed**: 22
* **Failed**: 0
* **Test Automation Engine**: `src/qa_validation.py`
