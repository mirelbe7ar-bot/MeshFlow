USE AdventureWorks2022;

SELECT OBJECT_SCHEMA_NAME(d.referencing_id) AS ConsumerDomain,
       OBJECT_NAME(d.referencing_id)        AS ConsumerView,
       d.referenced_schema_name             AS ProducerDomain,
       d.referenced_entity_name             AS ProducerTable
FROM sys.sql_expression_dependencies AS d
JOIN sys.views AS v ON v.object_id = d.referencing_id
WHERE d.referenced_schema_name <> OBJECT_SCHEMA_NAME(d.referencing_id)
ORDER BY ConsumerDomain, ConsumerView, ProducerDomain;