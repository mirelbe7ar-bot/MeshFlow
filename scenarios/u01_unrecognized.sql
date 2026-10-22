-- Fail-safe test: a change the checker does not understand
EXEC('ALTER TABLE Production.Product DROP COLUMN Color');
