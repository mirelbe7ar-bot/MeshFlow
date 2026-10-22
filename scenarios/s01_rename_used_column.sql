-- Scenario 1: Production renames a column that consumers use
USE AdventureWorks2022;
GO
EXEC sp_rename 'Production.Product.ListPrice', 'UnitListPrice', 'COLUMN';
