# Contract recall and precision (manual check)

For each consumer view written for this thesis, the columns the view really uses
were listed by reading its SQL (SELECT, JOIN, WHERE, GROUP BY, subqueries) and
compared with the columns in its generated contract.

| Consumer view | Columns used (read from SQL) | In contract | Missed | Extra |
|---|---|---|---|---|
| Sales.vw_RevenueByCategory | 12 | 12 | 0 | 0 |
| Sales.vw_ProductSalesByTerritory | 14 | 14 | 0 | 0 |
| Purchasing.vw_PurchaseCostVsListPrice | 9 | 9 | 0 | 0 |
| Purchasing.vw_PurchasingStaffOrders | 9 | 9 | 0 | 0 |
| Production.vw_ProductVendors | 14 | 14 | 0 | 0 |
| Production.vw_StockAndCheapestVendor | 11 | 11 | 0 | 0 |
| HumanResources.vw_SalesStaffPerformance | 13 | 13 | 0 | 0 |
| HumanResources.vw_DepartmentHeadcount | 9 | 9 | 0 | 0 |
| Sales.vw_AllProductCategories | 2 | 2 | 0 | 0 |
| **Total** | **93** | **93** | **0** | **0** |

Contract recall = 93 / 93 = 100%.  Contract precision = 93 / 93 = 100%.

Notes:
- Join columns (e.g. ProductID used only in ON clauses) and filter columns (e.g. MakeFlag
  in WHERE) are counted as used, because removing them breaks the view.
- Columns used only inside a CTE or subquery were also found (vw_PurchaseCostVsListPrice,
  vw_StockAndCheapestVendor, vw_DepartmentHeadcount).
- COUNT(*) uses no specific column.
- The 12 original AdventureWorks views were not checked by hand.
- In scenario 10 (SELECT * version of vw_AllProductCategories) the contract listed all 4
  columns although the view needs fewer: this is the known SELECT * over-protection.
