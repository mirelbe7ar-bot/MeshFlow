USE AdventureWorks2022;
GO

-- Scenario 10 (limitation): a consumer that uses SELECT *
-- Sales reads ALL columns of Production's ProductCategory table.
CREATE OR ALTER VIEW Sales.vw_AllProductCategories AS
SELECT *
FROM Production.ProductCategory;
GO

-- Test the view
SELECT * FROM Sales.vw_AllProductCategories;
