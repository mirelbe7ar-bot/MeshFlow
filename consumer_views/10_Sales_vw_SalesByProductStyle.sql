USE AdventureWorks2022;
GO

-- Scenario 8 (living contracts): a NEW consumer starts using a column
-- that no consumer used before (Production.Product.Style).
CREATE OR ALTER VIEW Sales.vw_SalesByProductStyle AS
SELECT p.Style,
       COUNT(DISTINCT d.SalesOrderID) AS Orders,
       SUM(d.LineTotal)               AS Revenue
FROM Sales.SalesOrderDetail AS d
JOIN Production.Product     AS p ON p.ProductID = d.ProductID
WHERE p.Style IS NOT NULL
GROUP BY p.Style;
GO

-- Test the view
SELECT * FROM Sales.vw_SalesByProductStyle;
