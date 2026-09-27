## Description
It is an AI Agent Triage for custommer support tickets, it use dataset from Kaggle and it follow...

## Requirement
- It need a device with GPU size xx
- uv dependecy install
- python => 3.14
- download the Kaggle dataset need in the app and save it in the project level with the name "tickets.csv", from the link below xx


## Getting Started
To run the AI Agent, open terminal in project level and run:
`uv run triage -n <number>` for example `uv run triage -n 200`

Questionnaire
A. Problem understanding

- How did you interpret the business problem in an insurance support context?
- Which assumptions did you make about ticket types, urgency, and processes?

B. Data and preprocessing

- Which part of the dataset did you use, for example language, subset, and
fields, and why?
- What preprocessing steps did you apply, and why were they necessary or
helpful?

C. Architecture and tools
- Describe your overall architecture, including main components and their
responsibilities.
- Which open-source libraries and models did you choose, and why, for example
classifier, embeddings, LLM, or orchestration framework?
- How does your triage agent orchestrate the different steps such as topic,
urgency, routing, and missing-info check?

D. Agentic workflow and behavior

- Describe the decision logic of your triage agent and how it decides what to do
next.

- How does the agent behave when information is missing or the ticket is
unclear, for example no product or no clear problem?
In which parts of the workflow did you use ML or LLM-based methods, and
where did you use rules, if any?

E. End-to-end testing and evaluation
- How did you test your triage agent end-to-end?
-  Please describe concrete test scenarios, for example normal tickets, very short
tickets, long or complex tickets, and obviously out-of-scope tickets.
- Which metrics or signals would you track to know whether the system works
well over time?

F. Limitations and improvements

- What are the main limitations of your current prototype, including technical,
data, and quality limitations?
- If you had two more weeks, what would you improve or extend, for example
better models, richer agent behavior, AWS deployment, or monitoring?