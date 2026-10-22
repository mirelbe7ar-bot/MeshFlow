-- Table level: rename a table nobody reads (safe)
EXEC sp_rename 'Production.ScrapReason', 'ScrapCause';
