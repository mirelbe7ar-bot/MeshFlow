-- Scenario 7: Person renames a column used by many domains
EXEC sp_rename 'Person.Person.FirstName', 'GivenName', 'COLUMN';
