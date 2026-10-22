USE AdventureWorks2022;
GO

CREATE OR ALTER VIEW Purchasing.vw_PurchaseCostVsListPrice AS
WITH Purchases AS (
    SELECT pod.ProductID,
           AVG(pod.UnitPrice)   AS AvgPurchasePrice,
           SUM(pod.ReceivedQty) AS UnitsReceived
    FROM Purchasing.PurchaseOrderDetail AS pod
    GROUP BY pod.ProductID
)
SELECT p.ProductNumber,
       p.Name                            AS Product,
       p.StandardCost,
       p.ListPrice,
       pu.AvgPurchasePrice,
       pu.UnitsReceived,
       p.ListPrice - pu.AvgPurchasePrice AS MarginPerUnit
FROM Purchases          AS pu
JOIN Production.Product AS p ON p.ProductID = pu.ProductID
WHERE p.MakeFlag = 0;
GO

-- Test the view
SELECT TOP 20 * FROM Purchasing.vw_PurchaseCostVsListPrice
ORDER BY UnitsReceived DESC;