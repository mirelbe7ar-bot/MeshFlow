USE AdventureWorks2022;
GO

CREATE OR ALTER VIEW Purchasing.vw_PurchasingStaffOrders AS
SELECT e.BusinessEntityID                     AS EmployeeID,
       CONCAT(pp.FirstName, ' ', pp.LastName) AS EmployeeName,
       e.JobTitle,
       COUNT(poh.PurchaseOrderID)             AS PurchaseOrders,
       SUM(poh.TotalDue)                      AS TotalSpent,
       MAX(poh.OrderDate)                     AS LastOrderDate
FROM Purchasing.PurchaseOrderHeader AS poh
JOIN HumanResources.Employee        AS e  ON e.BusinessEntityID = poh.EmployeeID
JOIN Person.Person                  AS pp ON pp.BusinessEntityID = e.BusinessEntityID
GROUP BY e.BusinessEntityID, pp.FirstName, pp.LastName, e.JobTitle;
GO

-- Test the view
SELECT * FROM Purchasing.vw_PurchasingStaffOrders
ORDER BY TotalSpent DESC;