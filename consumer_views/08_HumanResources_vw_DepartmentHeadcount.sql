USE AdventureWorks2022;
GO

CREATE OR ALTER VIEW HumanResources.vw_DepartmentHeadcount AS
SELECT d.Name      AS Department,
       d.GroupName,
       COUNT(*)    AS Headcount,
       STRING_AGG(CAST(CONCAT(pp.FirstName, ' ', pp.LastName) AS nvarchar(max)), ', ')
                   AS Employees
FROM (SELECT edh.BusinessEntityID, edh.DepartmentID
      FROM HumanResources.EmployeeDepartmentHistory AS edh
      WHERE edh.EndDate IS NULL) AS cur
JOIN HumanResources.Department AS d  ON d.DepartmentID = cur.DepartmentID
JOIN Person.Person             AS pp ON pp.BusinessEntityID = cur.BusinessEntityID
GROUP BY d.Name, d.GroupName;
GO

-- Test the view
SELECT Department, GroupName, Headcount
FROM HumanResources.vw_DepartmentHeadcount
ORDER BY Headcount DESC;