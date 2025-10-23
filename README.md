Experiments: 


Variants: 
- FK on experiments.id

variant_metrics: 
- 

users: 
- 



Improvements: 
- decoupling click events from the endpoint to database by using a queue to buffer out analytics
- setting up daily cron jobs to run materialized views for each
- token handling and issuing. 
- 