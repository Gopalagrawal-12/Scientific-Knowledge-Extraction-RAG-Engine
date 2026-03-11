import os
import asyncio
from database import get_all_stored_filenames
from agent import get_authentic_buddy_agent


async def chat_terminal():
    # 1. Use the SAME User ID you used in research.py
    current_user = "123"

    # 2. Check if the Agent actually has "Eyes" on your files
    my_files = get_all_stored_filenames(current_user)

    print("\n" + "=" * 60)
    print(f"🤖 BUDDY AGENT ONLINE | User: {current_user}")
    print(f"📚 Connected Library: {', '.join(my_files) if my_files else 'Empty'}")
    print("=" * 60)
    print("Commands: 'exit' to quit, 'context' to see what I know.\n")

    # 3. Initialize the Authentic Agent
    buddy = get_authentic_buddy_agent(current_user)

    while True:
        query = input("You: ").strip()

        if query.lower() == 'exit':
            break

        if query.lower() == 'context':
            print(f"I am looking at {len(my_files)} documents in your private silo.")
            continue

        if not query:
            continue

        print("\nBuddy is thinking...")

        # 4. The Agent performs RAG (Retrieval-Augmented Generation)
        response = buddy.chat(query)

        # If the agent didn't use any documents and is giving a general answer
        if not response.source_nodes and "UNIBOT" not in str(response):
            print(
                "\nBuddy: I couldn't find that in your documents. Please use my other AI agent for universal information: UNIBOT.")
        else:
            print(f"\nBuddy: {response}")
        print("-"*60)

        # This shows you which EXACT files the agent used to answer
        if response.source_nodes:
            sources = set([node.metadata.get('filename') for node in response.source_nodes])
            print(f"\n📍 Sources used: {', '.join(sources)}")
        print("-" * 30 + "\n")


if __name__ == "__main__":
    asyncio.run(chat_terminal())