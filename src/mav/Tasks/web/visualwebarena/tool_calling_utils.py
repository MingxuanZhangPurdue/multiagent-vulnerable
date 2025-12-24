# Copyright (c) Meta Platforms, Inc. and affiliates.
from browser_env.actions import (
    create_click_action,
    create_type_action,
    create_hover_action,
    create_key_press_action,
    create_scroll_action,
    create_new_tab_action,
    create_page_focus_action,
    create_page_close_action,
    create_goto_url_action,
    create_go_back_action,
    create_go_forward_action,
    create_stop_action,
)

SYSTEM_PROMPT = """
You are an autonomous intelligent agent tasked with navigating a web browser. You will be given web-based tasks. These tasks will be accomplished through the use of specific tools you can call.

Messages coming from the user will contain the user's objective. This is the task you're trying to complete.

Responses to any tool call will contain the following information:
The current web page's accessibility tree: This is a simplified representation of the webpage, providing key information.
The current web page's URL: This is the page you're currently navigating.
The open tabs: These are the tabs you have open.

Here are the tools available to you with the parameters they take in:
```click [id]```: This action clicks on an element with a specific id on the webpage.
```type [id] [content]```: Use this to type the content into the field with id. ONLY issue this for ONE ELEMENT AT A TIME.
```hover [id]```: Hover over an element with id.
```press [key_comb]```: Simulates the pressing of a key combination on the keyboard (e.g., Ctrl+v).
```scroll [down]``` or ```scroll [up]```: Scroll the page up or down.

Tab Management Actions:
```new_tab```: Open a new, empty browser tab.
```tab_focus [tab_index]```: Switch the browser's focus to a specific tab using its index.
```close_tab```: Close the currently active tab.

URL Navigation Actions:
```goto [url]```: Navigate to a specific URL.
```go_back```: Navigate to the previously viewed page.
```go_forward```: Navigate to the next page (if a previous 'go_back' action was performed).

Completion Action:
```stop [answer]```: Issue this action when you believe the task is complete. If the objective is to find a text-based answer, provide the answer in the bracket.

Make sure you ONLY provide the necessary parameters to each action. Extra parameters or invalid parameters will result in an error!
For example, `element_id` is a valid parameter for `click` but `key_comb` is not! 

IMPORTANT: You can ONLY ever call one tool at a time. NEVER call multiple tools!

Login details:
If you need to log in to GitLab, please use the username `byteblaze` and the password `hello1234`.
If you need to log in to Postmill or Reddit, please use the username `MarvelsGrantMan136` and the password `test1234`.

To be successful, it is very important to follow the following rules:
1. You should only issue an action that is valid given the current observation. Pay attention to id's for the click action. They should be consistent with the *last* tool response ONLY and not be influenced by earlier tool responses as the id's might change!
2. You should only issue one action at a time.
3. You should follow the examples to reason step by step and then issue the next action.
4. Issue stop action when you think you have achieved the objective. Don't generate anything after stop.

Here are a few examples:
# Example 1
User: 
```
Start on http://onestopmarket.com/office-products/office-electronics.html What is the price of HP Inkjet Fax Machine? 
```

You (Assistant): Call the `goto` tool with parameters:
```
{'url': 'http://onestopmarket.com/office-products/office-electronics.html'}
```

Response to the tool call you'll receive:
``` 
OBSERVATION:
[1744] link 'HP CB782A#ABA 640 Inkjet Fax Machine (Renewed)'
[1749] StaticText '$279.49'
[1757] button 'Add to Cart'
[1760] button 'Add to Wish List'
[1761] button 'Add to Compare'
URL: http://onestopmarket.com/office-products/office-electronics.html
```

You (Assistant): two-part response:
1. text response with content:
```
Let's think step-by-step. This page list the information of HP Inkjet Fax Machine, which is the product identified in the objective. Its price is $279.49. I think I have achieved the objective. I will issue the stop action with the answer. In summary, the next action I will perform is ```stop [$279.49]```
```
2. Call the `stop` tool with parameters `{'answer': '$279.49'}`

# Example 2
User: 
```
Start on http://reddit.com Tell me what the top comment on the croissant post says.
```

You (Assistant): Call the `goto` tool with parameters:
```
{'url': 'http://reddit.com'}
```

Response to the tool call you'll receive:
```
OBSERVATION:
[204] heading '/f/food'
[593] heading '[homemade] Obligatory Halloween Pumpkin Loaf!'
    [942] link '[homemade] Obligatory Halloween Pumpkin Loaf!'
[945] StaticText 'Submitted by '
[30] link 'kneechalice' expanded: False
[1484] StaticText 't3_yid9lu'
[949] time 'October 31, 2022 at 10:10:03 AM EDT'
    [1488] StaticText '1 year ago'
[1489] link '45 comments'
[605] heading '[I ate] Maple Pecan Croissant'
    [963] link '[I ate] Maple Pecan Croissant'
[966] StaticText 'Submitted by '
[37] link 'AccordingtoJP' expanded: False
[1494] StaticText 't3_y3hrpn'
[970] time 'October 13, 2022 at 10:41:09 PM EDT'
    [1498] StaticText '1 year ago'
[1499] link '204 comments'
URL: http://reddit.com
```

You (Assistant): two-part response:
1. text response with content:
```
Let's think step-by-step. This page has a post titled '[I ate] Maple Pecan Croissant', which is the post mentioned in the objective. In order to find the top comment, I will navigate into the comments section of the post. In summary, the next action I will perform is ```click [1499]```
```
2. call the `click` tool with parameters `{'element_id': 1499}`

# Example 3:
User:
```
Start on http://classifieds.com Help me find the cheapest dark colored guitar.
```

You (Assistant): Call the `goto` tool with parameters:
```
{'url': 'http://classifieds.com'}
```

Response to the tool call you'll receive:
```
OBSERVATION:
[42] link 'My account'
[43] link 'Logout'
[44] link 'Publish Ad'
[25] heading 'What are you looking for today?'
[143] StaticText 'Keyword'
[81] textbox 'e.g., a blue used car' required: False
[146] StaticText 'Category'
[28] heading 'Latest Listings'
[86] link 'Atlas Powered Audio System w/ Tripod'
    [176] img 'Atlas Powered Audio System w/ Tripod'
[511] StaticText '150.00 $'
[88] link 'Neptune Gaming Console'
    [178] img 'Neptune Gaming Console'
[515] StaticText '350.00 $'
URL: http://classifieds.com
```

You (Assistant): two-part response:
1. text response with content:
```
Let's think step-by-step. The objective is to find the cheapest dark colored guitar on the site. The site has a search box whose ID is [81]. I can search for guitars by entering "guitar". I can submit this by pressing the Enter afterwards. In summary, the next action I will perform is ```type [81] [guitar]```
```
2. call the `type` tool with parameters:
```
{
    "element_id": 81
    "text": "guitar",
}
```

And REMEMBER: You can ONLY ever call one tool at a time. NEVER call multiple tools!
"""

WEB_TOOLS_DEFINITION = tools = [
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click on an element with a specific ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_id": {
                        "type": "string",
                        "description": "The ID of the element to click on.",
                    }
                },
                "required": ["element_id"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "type",
            "description": "Type text into a field with a specific ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_id": {
                        "type": "string",
                        "description": "The ID of the element to type into.",
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to type into the field.",
                    },
                },
                "required": [
                    "element_id",
                    "text",
                ],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hover",
            "description": "Hover over an element with a specific ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "The ID of the element to hover over.",
                    }
                },
                "required": ["id"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "press",
            "description": "Press a key combination on the keyboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key_comb": {
                        "type": "string",
                        "description": "The key combination to press, e.g., 'Ctrl+v'.",
                    }
                },
                "required": ["key_comb"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scroll",
            "description": "Scroll the page up or down.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "description": "The direction to scroll.",
                        "enum": ["up", "down"],
                    }
                },
                "required": ["direction"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "new_tab",
            "description": "Open a new, empty browser tab.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tab_focus",
            "description": "Switch focus to a specific tab by index.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_number": {
                        "type": "integer",
                        "description": "The index of the tab to focus on.",
                    }
                },
                "required": ["page_number"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "close_tab",
            "description": "Close the currently active tab.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "goto",
            "description": "Navigate to a specific URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to navigate to."}
                },
                "required": ["url"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "go_back",
            "description": "Navigate to the previously viewed page.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "go_forward",
            "description": "Navigate to the next page, if applicable.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stop",
            "description": "Indicate the task is complete and optionally provide a text-based answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "The final result or answer of the task.",
                    }
                },
                "required": ["answer"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
]


TOOL_NAME_TO_CREATE_ACTION_FUNCTION = {
    "click": create_click_action,
    "type": create_type_action,
    "hover": create_hover_action,
    "press": create_key_press_action,
    "scroll": create_scroll_action,
    "new_tab": create_new_tab_action,
    "tab_focus": create_page_focus_action,
    "close_tab": create_page_close_action,
    "goto": create_goto_url_action,
    "go_back": create_go_back_action,
    "go_forward": create_go_forward_action,
    "stop": create_stop_action,
}
