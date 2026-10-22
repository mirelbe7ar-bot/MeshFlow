USE AdventureWorks2022;
GO

CREATE OR ALTER VIEW HumanResources.vw_SalesStaffPerformance AS
SELECT e.BusinessEntityID                        AS EmployeeID,
       CONCAT(pp.FirstName, ' ', pp.LastName)    AS EmployeeName,
       e.JobTitle,
       DATEDIFF(YEAR, e.HireDate, '2014-12-31')  AS YearsAtCompany,
       st.Name                                   AS Territory,
       sp.SalesQuota,
       sp.SalesYTD,
       sp.Bonus,
       RANK() OVER (ORDER BY sp.SalesYTD DESC)   AS SalesRank
FROM HumanResources.Employee   AS e
JOIN Sales.SalesPerson         AS sp ON sp.BusinessEntityID = e.BusinessEntityID
JOIN Person.Person             AS pp ON pp.BusinessEntityID = e.BusinessEntityID
LEFT JOIN Sales.SalesTerritory AS st ON st.TerritoryID = sp.TerritoryID;
GO

-- Test the view
SELECT * FROM HumanResources.vw_SalesStaffPerformance
ORDER BY SalesRank;