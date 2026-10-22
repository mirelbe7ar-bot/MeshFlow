USE AdventureWorks2022;
GO

CREATE OR ALTER VIEW Production.vw_ProductVendors AS
SELECT p.ProductID,
       p.ProductNumber,
       p.Name               AS Product,
       v.Name               AS Vendor,
       pv.StandardPrice,
       pv.AverageLeadTime   AS LeadTimeDays,
       pv.MinOrderQty,
       CASE WHEN v.PreferredVendorStatus = 1 THEN 'Preferred'
            ELSE 'Standard' END AS VendorStatus,
       v.CreditRating
FROM Production.Product            AS p
LEFT JOIN Purchasing.ProductVendor AS pv ON pv.ProductID = p.ProductID
LEFT JOIN Purchasing.Vendor        AS v  ON v.BusinessEntityID = pv.BusinessEntityID
                                        AND v.ActiveFlag = 1
WHERE p.MakeFlag = 0;
GO

-- Test the view
SELECT TOP 30 * FROM Production.vw_ProductVendors
ORDER BY Product, StandardPrice;