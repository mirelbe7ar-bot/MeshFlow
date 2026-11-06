-- DEMO RESET: run this in SSMS before rehearsing or before the meeting.
-- It puts the database back to the starting point of the live demo.
USE AdventureWorks2022;
GO
-- Demo 3 (living contracts) starts WITHOUT the Style consumer view
DROP VIEW IF EXISTS Sales.vw_SalesByProductStyle;
GO
-- Safety: make sure scenario 12's column has its normal name
IF COL_LENGTH('Production.Product', 'ProductCode') IS NOT NULL
    EXEC sp_rename 'Production.Product.ProductCode', 'ProductNumber', 'COLUMN';
GO
SELECT 'Reset done' AS Status;
