create database foodmanagement_db;
use foodmanagement_db;


SELECT * FROM providers;

SELECT City, COUNT(*) AS Provider_Count FROM providers GROUP BY City;

SELECT * FROM providers ORDER BY Provider_ID DESC LIMIT 5;

SELECT Name, Contact FROM receivers WHERE City = 'North Cynthiaberg';

SELECT * FROM receivers WHERE Name LIKE '%Frank%';

SELECT * FROM food_listings ORDER BY Food_ID DESC LIMIT 5;

SELECT * FROM claims WHERE Status = 'Pending';

SELECT * FROM claims WHERE Status = 'Completed';

SELECT c.Claim_ID, f.Food_Name, r.Name AS Receiver FROM claims c JOIN food_listings f ON c.Food_ID=f.Food_ID JOIN receivers r ON c.Receiver_ID=r.Receiver_ID WHERE r.Name LIKE '%Williams%';


SELECT * FROM claims ORDER BY Timestamp DESC LIMIT 5;