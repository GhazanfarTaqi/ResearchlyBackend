from agents.research_agent import researchApp
from agents.writer_agent import writerApp
from rich import print



topic = input("enter a topic you want to research:")
print("-------starting Reseach Pipeline--------")
research_data = researchApp.invoke({"topic":topic})

print(research_data)

print("-------starting Writer Pipeline--------")

writer_data = writerApp.invoke({"topic":topic, "papers":research_data["papers"]})

print(writer_data['starter_manuscript'])