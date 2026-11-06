USE AdventureWorks2022;
GO

-- Scenario 9 (living contracts): a consumer STOPS using columns.
-- The Sales team rewrites its SELECT * view to list only the columns it really needs.
-- After regenerating, ModifiedDate and rowguid are no longer protected,
-- so dropping ModifiedDate (scenarios/s10_select_star.sql) now passes.
CREATE OR ALTER VIEW Sales.vw_AllProductCategories AS
SELECT ProductCategoryID,
       Name
FROM Production.ProductCategory;
GO

-- Test the view
SELECT * FROM Sales.vw_AllProductCategories;
