USE AdventureWorks2022;
GO

CREATE OR ALTER VIEW Sales.vw_RevenueByCategory AS
SELECT pc.Name                        AS Category,
       YEAR(h.OrderDate)              AS OrderYear,
       COUNT(DISTINCT h.SalesOrderID) AS Orders,
       SUM(d.OrderQty)                AS UnitsSold,
       SUM(d.LineTotal)               AS Revenue
FROM Sales.SalesOrderHeader        AS h
JOIN Sales.SalesOrderDetail        AS d  ON d.SalesOrderID = h.SalesOrderID
JOIN Production.Product            AS p  ON p.ProductID = d.ProductID
JOIN Production.ProductSubcategory AS ps ON ps.ProductSubcategoryID = p.ProductSubcategoryID
JOIN Production.ProductCategory    AS pc ON pc.ProductCategoryID = ps.ProductCategoryID
GROUP BY pc.Name, YEAR(h.OrderDate);
GO

-- Test the view
SELECT * FROM Sales.vw_RevenueByCategory
ORDER BY OrderYear, Category;