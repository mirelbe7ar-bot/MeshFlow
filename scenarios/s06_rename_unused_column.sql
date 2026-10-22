-- Scenario 6: Purchasing renames a column no consumer uses (safe)
EXEC sp_rename 'Purchasing.Vendor.PurchasingWebServiceURL', 'WebsiteURL', 'COLUMN';
