-- Scenario 10: Production drops ModifiedDate from ProductCategory.
-- No consumer really needs this column, but a SELECT * consumer reads every column,
-- so the contract protects it and the change is blocked (over-protection).
ALTER TABLE Production.ProductCategory DROP COLUMN ModifiedDate;
