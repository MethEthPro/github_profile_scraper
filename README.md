# GitHub Profile Scraper
This project is designed to scrape repositories from a given GitHub profile using the GitHub API. The script fetches repository data, handles pagination, and ensures that the API rate limits are respected during execution. Additionally, it features a custom scoring algorithm to rank repositories based on various factors.

Features
Retrieves all repositories from a GitHub profile
Handles API rate limits gracefully
Converts API rate limit reset time to Indian Standard Time (IST)
Implements retry logic to handle temporary failures
Custom scoring algorithm to give a score to repositories


EXPLANATION- 
you need to enter the profile link you want to get all the repositories of , for eg   "https://github.com/JaideepGuntupalli"  
as all of this have been done through github api , you will need to generate your own token , and pass it in the github_token variable 
then the code checks if there is sufficient limit of requests remaining before running the code , the max limit is 5000 in an hour 
i have put a check such that if less than 1000 requests are remaining you cant run the code , obviously you can change it as per your wish and the limit resest to 5000 every hour so no need to worry if you exceed the limit, and your ip is restricted so using a token from another github acc on the same device wont help , so 1000 is a safe number 
so your limit is displayed every time you run the file , and if you exceed it i have made a function that will tell you the time in UCT and IST as to when the limit will reset 
then with the help of api i got all the repos , then i iterated through all the repos got the name,stars,forks,description,primary language, watchers, each language used with their percentage , commit count and contributors count , and then the final score for the repo 


i have only considered files that are important for analysis like .py, .js, .ts and ignored other like csv , json and txt files 
also for each file i have considered how many class ,modules, packages are there for the main extensions obviously  
also there is a check if the file is bigger than 3mb to ignore it 
also i have gotten total code lines for each file 
and just for python files also checked if there are nested loops and other complex parts
and using this i have created a scroing algorithm for each repo  it included lines of code, maximum folder depth , total files in repo and other complex algosn 




some drawbacks-
takes a lot of time for big repositories , i have not yet implemented parallel processing
there is no ranking system and the score generated is not limited to 100 , so a score of 96 does not mean a complex repository , rather it would be a very small one 
i was not able to get the repository size from the api, i mean i was getting it , but it was like in bytes and kilobytes so i am unsure about it
