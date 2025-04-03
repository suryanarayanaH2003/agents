from crewai import Agent, Task, Crew, LLM
from pymongo import MongoClient
import os
from django.conf import settings

# Set API Key for Gemini
os.environ["GEMINI_API_KEY"] = "key in env"

# Initialize LLM
my_llm = LLM(
    model='gemini/gemini-1.5-flash',
    api_key=os.environ["GEMINI_API_KEY"]
)

# MongoDB Connection
client = MongoClient('mongodb+srv://suryahihub:713321Ad105@cluster0.iojbuw6.mongodb.net/')
db = client['policy_compliance_db']
policies_collection = db['policies']
results_collection = db['compliance_results']

# Define Agents
policy_reader_agent = Agent(
    role="Policy Reader",
    goal="Extract and summarize company policies from uploaded documents",
    backstory="You are an expert at reading and interpreting policy documents.",
    verbose=True,
    llm=my_llm,
    tools=[]
)

law_finder_agent = Agent(
    role="Law Finder",
    goal="Retrieve the government laws from a predefined file",
    backstory="You are a lawyer who knows the laws and their history.",
    verbose=True,
    llm=my_llm,
    tools=[]
)

rule_checker_agent = Agent(
    role="Rule Checker",
    goal="Compare company policies with government laws and identify gaps",
    backstory="You are a compliance analyst with a keen eye for detail.",
    verbose=True,
    llm=my_llm,
    tools=[]
)

fixer_agent = Agent(
    role="Fixer",
    goal="Suggest actionable changes to policies to ensure compliance",
    backstory="You are a policy editor who crafts precise solutions.",
    verbose=True,
    llm=my_llm,
    tools=[]
)

watcher_agent = Agent(
    role="Watcher",
    goal="Monitor for updates and alert the company (simulated for this project)",
    backstory="You are a vigilant observer of regulatory shifts.",
    verbose=True,
    llm=my_llm,
    tools=[]
)

# Function to Read Laws from File
def fetch_laws():
    laws_file_path = os.path.join(settings.BASE_DIR, 'laws.txt')
    try:
        with open(laws_file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Error: Laws file not found."

# Define Tasks with MongoDB Integration
def create_tasks(policy_file_path, policy_id):
    policy_read_task = Task(
        description=f"Read and extract policies from the file at {policy_file_path}",
        agent=policy_reader_agent,
        expected_output="A summary of company policies in text format",
        callback=lambda output: policies_collection.update_one(
            {"_id": policy_id},
            {"$set": {"policy_text": output.raw if hasattr(output, "raw") else str(output)}}
        )
    )
    
    laws_text = fetch_laws()
    
    law_fetch_task = Task(
        description="Read the government laws from the predefined file",
        agent=law_finder_agent,
        expected_output="A list of government laws",
        callback=lambda output: results_collection.update_one(
            {"policy_id": policy_id}, {"$set": {"laws": laws_text}}, upsert=True
        )
    )

    compliance_check_task = Task(
        description="Compare the extracted policies with government laws and identify gaps",
        agent=rule_checker_agent,
        expected_output="A report of compliance gaps",
        callback=lambda output: results_collection.update_one(
            {"policy_id": policy_id}, {"$set": {"gaps": output.raw if hasattr(output, "raw") else str(output)}}
        )
    )

    fix_task = Task(
        description="Suggest specific changes to policies to resolve compliance gaps",
        agent=fixer_agent,
        expected_output="A list of policy suggestions",
        callback=lambda output: results_collection.update_one(
            {"policy_id": policy_id}, {"$set": {"suggestions": output.raw if hasattr(output, "raw") else str(output)}}
        )
    )

    watch_task = Task(
        description="Simulate monitoring for updates and prepare an alert (for learning purposes)",
        agent=watcher_agent,
        expected_output="An alert message or 'No updates' if none",
        callback=lambda output: results_collection.update_one(
            {"policy_id": policy_id}, {"$set": {"alerts": output.raw if hasattr(output, "raw") else str(output)}}
        )
    )

    return [policy_read_task, law_fetch_task, compliance_check_task, fix_task, watch_task]

# Run the Crew
def run_crew(policy_file_path, policy_id):
    tasks = create_tasks(policy_file_path, policy_id)
    crew = Crew(
        agents=[policy_reader_agent, law_finder_agent, rule_checker_agent, fixer_agent, watcher_agent],
        tasks=tasks,
        google_api_key=os.environ["GEMINI_API_KEY"],
        verbose=True
    )
    result = crew.kickoff()
    return result
