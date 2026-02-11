# This instruction is to create the app

I want to create an app that can be deployed in databricks app. It should be also deploy in my own machine. You can use stramlit. The app should communicate with databricks multi agent endpoint and to provide the chatbot box for the client. Below are some information

* Endpoint name:
endpoint name is should come from agent name. The agent name for Multi agent (MAS) is provided in the config file n the ```conf/catalog_config.py```. For example MAS_NAME = "Flipp_Deal_Supervisor" and the serving endpoint name is ```mas-base-model-33ad5053``` . You need to find endpoint name and URL based on the name of the MAS agent.

* Use the Endpoint url to communicate with the agent in the backend
* For the app itself, I need to have
    * Flipp logo in the top-left corner with a tagline like "Your Smart Deal Finder" (Search for it in browser and download the logo)
    * Branding & Layout
    * Clean white/light-gray background to match Flipp's existing app aesthetic
    * Top navigation bar with tabs: Home, Flyers, Shopping List, AI Assistant. Add some of the PDFs, stored in ```/data/catalog_style``` in Flyers page. For AI assitant, add the chatbot
    * User avatar/profile icon in the top-right for personalization settings (location, preferred stores). It can be empty icons with no actions

* Chatbot Interface
    * Chatbot with history box. The client can ask a question and the app should send the question to the endpoint and return back the results.
    * Floating chat bubble (bottom-right corner) with a sparkle/AI icon and label "Ask Flipp" — tapping opens the full chat panel

    * Animated typing indicator with Flipp branding while the agent processes queries

    * Suggested prompt chips above the input field — e.g., "Best deals near me", "BBQ on a budget", "BOGO this week", "Cheapest diapers"


Some of these features do not need to have actual actions, It can be an icon in the app. The only one should really work is the chatbot feature and also providing some flyers examples.