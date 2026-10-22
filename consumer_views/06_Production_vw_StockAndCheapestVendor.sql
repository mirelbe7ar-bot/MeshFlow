USE AdventureWorks2022;
GO

CREATE OR ALTER VIEW Production.vw_StockAndCheapestVendor AS
SELECT p.ProductNumber,
       p.Name            AS Product,
       p.ReorderPoint,
       SUM(i.Quantity)   AS QuantityInStock,
       CASE WHEN SUM(i.Quantity) < p.ReorderPoint THEN 'Reorder'
            ELSE 'OK' END AS StockStatus,
       v.Name            AS CheapestVendor,
       pv.StandardPrice
FROM Production.Product          AS p
JOIN Production.ProductInventory AS i  ON i.ProductID = p.ProductID
JOIN Purchasing.ProductVendor    AS pv ON pv.ProductID = p.ProductID
JOIN Purchasing.Vendor           AS v  ON v.BusinessEntityID = pv.BusinessEntityID
WHERE pv.StandardPrice = (SELECT MIN(pv2.StandardPrice)
                          FROM Purchasing.ProductVendor AS pv2
                          WHERE pv2.ProductID = p.ProductID)
GROUP BY p.ProductNumber, p.Name, p.ReorderPoint, v.Name, pv.StandardPrice;
GO

-- Test the view
SELECT * FROM Production.vw_StockAndCheapestVendor
ORDER BY StockStatus DESC, Product;