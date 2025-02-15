import RedditRetriever
from smolagents import CodeAgent, DuckDuckGoSearchTool, LiteLLMModel
context = ""
context += "Content from Reddit: " + str(RedditRetriever.get_reddit_trends())+"\n"


model = LiteLLMModel("ollama/llama3.1:8b-instruct-q5_K_M")
agent = CodeAgent(tools=[DuckDuckGoSearchTool()], model=model)
agent.run(f"Given the context, generate funny and engaging script that may be used to generate funny shorts videos (brain rot videos, rizz story videos, etc.) visit links in the context and read them and generate the content. do not write any openings. make it plain text with sentences ending with a dot. maintainning mockary is key! exclude serious non funny topics. write wild things. context:{context}"
          )








