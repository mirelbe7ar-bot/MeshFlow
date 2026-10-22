-- Scenario 11: widening a type (safe by default, blocked in strict mode)
ALTER TABLE Production.Product ALTER COLUMN ReorderPoint int NOT NULL;
