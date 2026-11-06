-- Scenario 12: what happens WITHOUT the framework
-- The producer (Production) renames a used column (ProductNumber) directly in the database,
-- with no contract check. Run the three parts one at a time (highlight + Execute).
USE AdventureWorks2022;
GO

-- PART 1: the consumer works before the change
SELECT TOP 5 * FROM Purchasing.vw_PurchaseCostVsListPrice;
GO

-- PART 2: the producer renames the column directly (no check, no warning)
EXEC sp_rename 'Production.Product.ProductNumber', 'ProductCode', 'COLUMN';
GO
-- The consumer now fails:
SELECT TOP 5 * FROM Purchasing.vw_PurchaseCostVsListPrice;
GO

-- PART 3: undo the change so the database is back to normal
EXEC sp_rename 'Production.Product.ProductCode', 'ProductNumber', 'COLUMN';
GO
SELECT TOP 5 * FROM Purchasing.vw_PurchaseCostVsListPrice;
GO
