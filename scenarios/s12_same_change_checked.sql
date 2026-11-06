-- Demo 4: the SAME change as scenario 12, but checked by MeshFlow before release
EXEC sp_rename 'Production.Product.ProductNumber', 'ProductCode', 'COLUMN';
