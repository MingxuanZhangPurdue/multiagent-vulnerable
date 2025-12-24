# Copyright (c) Meta Platforms, Inc. and affiliates.
import re
import streamlit as st
import os
import json
from openai import AzureOpenAI


def main():
    st.title("Replay ChatGPT Conversation with Azure OpenAI API")

    # Upload config file
    config_file = st.file_uploader("Upload the config file", type=["json"])

    # Upload conversation file
    conversation_file = st.file_uploader(
        "Upload the conversation log file", type=["jsonl", "json"]
    )

    # Check if all inputs are provided
    if config_file and conversation_file:
        # Load config
        config = json.load(config_file)
        st.write("Config loaded:", config)

        # Load conversation
        conversation_content = conversation_file.read().decode("utf-8")
        all_lines = conversation_content.strip().split("\n")

        agent_turn_to_replay = st.selectbox(
            "Choose an agent turn to replay:", range(len(all_lines))
        )

        conversation_in_the_chosen_agent_turn = json.loads(
            all_lines[agent_turn_to_replay]
        )
        st.write("Conversation loaded for the chosen agent turn:")
        st.json(conversation_in_the_chosen_agent_turn)

        conversation_turn_to_edit = st.selectbox(
            "Choose a conversation turn to edit:",
            range(len(conversation_in_the_chosen_agent_turn)),
        )

        user_message_to_edit = conversation_in_the_chosen_agent_turn[
            conversation_turn_to_edit
        ]
        for content in user_message_to_edit["content"]:
            if content["type"] == "text":
                user_text_to_edit = content["text"]
                break

        url_match = re.search(r"URL: (.+)", user_text_to_edit)
        if url_match:
            url = url_match.group(1)
        else:
            st.error("No URL found in the last user message.")
            url = ""

        if user_text_to_edit and url:
            new_url = st.text_input("Edit the URL:", value=url)
            new_user_text = re.sub(
                r"(URL: ).+", r"\1" + new_url, user_text_to_edit
            )

            for content in user_message_to_edit["content"]:
                if content["type"] == "text":
                    content["text"] = new_user_text
                    break

            if st.button("Send Conversation to Azure OpenAI"):
                # Initialize client
                client = AzureOpenAI(
                    azure_endpoint=os.environ["AZURE_API_ENDPOINT"],
                    api_key=os.environ["AZURE_API_KEY"],
                    api_version="2024-06-01",
                )

                st.write("Edited conversation")
                st.json(conversation_in_the_chosen_agent_turn)

                # Send the conversation
                response = client.chat.completions.create(
                    messages=conversation_in_the_chosen_agent_turn,
                    model=config["model"],
                    temperature=config["temperature"],
                    max_tokens=config["max_tokens"],
                    top_p=config["top_p"],
                )

                st.write("Response from Azure OpenAI:")
                st.write(response.choices[0].message.content)
            else:
                st.write("No user message found in the conversation.")

    else:
        st.write("Please provide all required inputs.")


if __name__ == "__main__":
    main()
