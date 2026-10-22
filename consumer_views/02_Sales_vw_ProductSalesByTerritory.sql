USE AdventureWorks2022;
GO

CREATE OR ALTER VIEW Sales.vw_ProductSalesByTerritory AS
SELECT t.Name            AS Territory,
       t.[Group]         AS Region,
       p.ProductNumber,
       p.Name            AS Product,
       p.Color,
       SUM(d.OrderQty)   AS UnitsSold,
       SUM(d.LineTotal)  AS Revenue
FROM Sales.SalesOrderDetail  AS d
JOIN Sales.SalesOrderHeader  AS h ON h.SalesOrderID = d.SalesOrderID
JOIN Sales.SalesTerritory    AS t ON t.TerritoryID = h.TerritoryID
JOIN Production.Product      AS p ON p.ProductID = d.ProductID
WHERE p.FinishedGoodsFlag = 1
GROUP BY t.Name, t.[Group], p.ProductNumber, p.Name, p.Color;
GO

-- Test the view: top 20 product-territory combinations by revenue
SELECT TOP 20 * FROM Sales.vw_ProductSalesByTerritory
ORDER BY Revenue DESC;