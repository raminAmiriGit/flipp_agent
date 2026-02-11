# This is instruction to how to create Multi agents

Eventually what I want is a chatbot which user can ask some question about the discount and coupans. They can upload their shopping list and get the best deals and locations of the stores. This requires Knowledge assistant and also Genie agent

## Knowledge assistant 

I want to have a knowledge assistant agent created in data bricks workspace. The knowledge assistant agent should have access to all unstructured data (like PDFs) and parse them. Get the name of KA (knowledge assistant) agent from catalog_config.py file. The path to PDF files are also provided in the config file. THey are stored in Volumn in Unity catalog. 

There are also some json files which are example file. I would like to use it for increase accuracy of an agent. THese are for human labeling examples

## Genie agent

I want also have Genie agent with access to all structured data space which are created (their names are in config file)

## Create multi agent

Multi agent should be combination of both Genie and KA agent