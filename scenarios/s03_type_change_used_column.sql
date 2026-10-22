-- Scenario 3: Production changes the type of a used column (money -> text)
ALTER TABLE Production.Product ALTER COLUMN ListPrice nvarchar(20) NOT NULL;
