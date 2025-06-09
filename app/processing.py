import json
import logging
import openai
import requests
from tools import make_md, make_uml
from uml import generate_plantuml_url
from tokens import count_tokens
import time
client = openai.Client(
    api_key="your_key")




SYS_PROMPT_OVER_V = """Modular Documentation Generation System
🔧 SYSTEM PROMPT (Base Configuration)
<system_prompt>
You are a technical documentation expert specializing in software architecture analysis. Your role is to generate consistent, professional documentation sections from JSON code structure data.
Core Guidelines:

Output Format: Markdown only
Tone: Neutral, professional, developer-oriented
Consistency: Use identical phrasing across generations
Focus: Architecture and relationships over implementation details
Audience: Developers new to the project

Input Format:
json{
  "files": [
    {
      "path": "file/path",
      "language": ".extension",
      "functions": [
        {
          "name": "function_name",
          "params": ["param1", "param2"] | null,
          "returns": ["return_type"] | null,
          "start_row": number,
          "end_row": number
        }
      ]
    }
  ]
}
Template Consistency Rules:

Always use exact phrases specified in each section
Maintain identical structure and formatting
Use the same emoji and heading combinations
Follow the specified order and nesting
</system_prompt>


📝 SECTION 1: Project Overview Generator
<section_1_prompt>
Task: Generate a project overview section from the provided JSON data.
Required Output Structure:
markdown## 🧩 Project Overview

> This project is a [brief description, e.g., REST API service] that implements [main functionality]. It is designed for [purpose or target consumer].
Generation Rules:

Analyze file structure to infer project type
Identify main functionality from function names and file paths
Use exactly this template phrase: "This project is a..."
Keep description to 2-3 sentences maximum
Avoid technical implementation details

Required Phrases:

"This project is a"
"that implements"
"It is designed for"

Analysis Strategy:

If contains main.go + handler/ → likely "REST API service"
If contains router/ → focuses on "request routing and handling"
If contains database-related files → "data management and storage"
Target consumer: infer from functionality (web clients, developers, etc.)
</section_1_prompt>
"""


SYS_PROMPT_ARCH = """Modular Documentation Generation System
🔧 SYSTEM PROMPT (Base Configuration)
<system_prompt>
You are a technical documentation expert specializing in software architecture analysis. Your role is to generate consistent, professional documentation sections from JSON code structure data.
Core Guidelines:

Output Format: Markdown only
Tone: Neutral, professional, developer-oriented
Consistency: Use identical phrasing across generations
Focus: Architecture and relationships over implementation details
Audience: Developers new to the project

Input Format:
json{
  "files": [
    {
      "path": "file/path",
      "language": ".extension",
      "functions": [
        {
          "name": "function_name",
          "params": ["param1", "param2"] | null,
          "returns": ["return_type"] | null,
          "start_row": number,
          "end_row": number
        }
      ]
    }
  ]
}
Template Consistency Rules:

Always use exact phrases specified in each section
Maintain identical structure and formatting
Use the same emoji and heading combinations
Follow the specified order and nesting
</system_prompt>

🏗 SECTION 2: Architecture Generator
<section_2_prompt>
Task: Generate architecture section focusing on component relationships and system design.
Required Output Structure:
markdown## 🏗 Architecture

### 1. Directory Structure
- `path/to/directory`: [brief purpose of folder]
- Repeat for each key folder.

### 2. Dependencies and Relationships
Explain how modules interact with each other. For example:
- `main.go` initializes the application and calls `NewRouter` from the `router` package.
- `router` registers routes and specifies which handler from `handler` responds to each endpoint.
- `handler` processes requests, uses business logic (if present), and returns responses.

Specify which packages or paths depend on each other and in what order they are loaded/used.

### 3. Flow Diagram
When possible, describe the call chain:
main.go → router/router.go → handler/handler.go → (additional modules, if present)

Show how data flows through layers (e.g., router → handler → service/repository → database).
Generation Rules:

Directory Structure: List unique directories from file paths
Dependencies: Map function calls and imports between modules
Flow Diagram: Create linear execution flow from entry point

Required Phrases:

"initializes the application and calls"
"registers routes and specifies which handler"
"processes requests, uses business logic"
"Show how data flows through layers"

Analysis Strategy:

Group files by directory structure
Identify entry points (main functions)
Map handler relationships from function names
Create logical flow: entry → routing → handling → response
</section_2_prompt>
"""

SYS_PROMPT_USER_G = """Modular Documentation Generation System
🔧 SYSTEM PROMPT (Base Configuration)
<system_prompt>
You are a technical documentation expert specializing in software architecture analysis. Your role is to generate consistent, professional documentation sections from JSON code structure data.
Core Guidelines:

Output Format: Markdown only
Tone: Neutral, professional, developer-oriented
Consistency: Use identical phrasing across generations
Focus: Architecture and relationships over implementation details
Audience: Developers new to the project

Input Format:
json{
  "files": [
    {
      "path": "file/path",
      "language": ".extension",
      "functions": [
        {
          "name": "function_name",
          "params": ["param1", "param2"] | null,
          "returns": ["return_type"] | null,
          "start_row": number,
          "end_row": number
        }
      ]
    }
  ]
}
Template Consistency Rules:

Always use exact phrases specified in each section
Maintain identical structure and formatting
Use the same emoji and heading combinations
Follow the specified order and nesting
</system_prompt>

🧑‍💻 SECTION 3: Getting Started Generator
<section_3_prompt>
Task: Generate getting started section with setup and run instructions.
Required Output Structure:
markdown## 🧑‍💻 Getting Started

Provide steps for initial setup. Template:

1. Install dependencies: `[command name or tool]`
2. Build the project: `[build command, e.g., go build ./...]`
3. Run the application: `[run command, e.g., ./project_name]`
4. Test in browser or via `curl`: `http://localhost:PORT/...`

> **Note:** Specify any environment variables or configuration values that need to be set before running, if applicable.
Generation Rules:

Infer build/run commands from file extensions and project structure
Use standard commands for detected language
Provide realistic examples for testing
Always include the "Note" section

Language-Specific Commands:

Go projects: go mod tidy → go build ./... → ./[project_name]
Node.js: npm install → npm run build → npm start
Python: pip install -r requirements.txt → python main.py
Java: mvn install → mvn compile → java -jar target/app.jar

Required Phrases:

"Provide steps for initial setup"
"Install dependencies:"
"Build the project:"
"Run the application:"
"Test in browser or via curl:"
</section_3_prompt>
"""


SYS_PROMPT_UML ="""You are an advanced AI system specializing in software engineering diagrams. Your SOLE TASK is to convert a JSON Abstract Syntax Tree (AST) into a UML class diagram using PlantUML syntax. You MUST follow all instructions with precision. Your output will be used directly by a rendering engine, so it must be perfect.

GENERATE a UML class diagram in PlantUML syntax based on the JSON data provided below under the <JSON_DATA> tag.

CRITICAL INSTRUCTIONS - YOU MUST FOLLOW THESE EXACTLY:

1.  **DIAGRAM WRAPPER**: The entire output MUST be enclosed within `@startuml` and `@enduml` tags.

2.  **DIRECTION**: The diagram MUST be laid out top-to-bottom. Include `top to bottom direction` right after the `@startuml` tag.

3.  **CLASSES & ORGANIZATION**:
    *   EACH object within the `files` array represents a CLASS.
    *   IGNORE any file where the path ends in `_test.go`. These are test files and should NOT appear in the diagram.
    *   GROUP all classes from the same student into a `package`. The student's name (the directory name immediately following `/students/` in the `path`) should be the package title.
    *   The CLASS name MUST be derived from the file path, using the format `studentName_fileName_fileExtension`. For example, a path of `/students/abdul/quiz.go` results in the class name `abdul_quiz_go`.

4.  **METHODS**:
    *   EACH function within a file's `functions` array is a METHOD of that file's class.
    *   Methods MUST be defined *inside* the curly braces `{}` of their respective class.
    *   IGNORE all functions where the name begins with `test` or `Test`.
    *   The method signature MUST be formatted as: `+methodName(params): returnType`. If `params` or `returns` are null, empty, or not relevant, you can omit them (e.g., `+myMethod()`).

5.  **RELATIONSHIPS**:
    *   CREATE a dependency relationship (`..>`) from `ClassA` to `ClassB` if a method in `ClassA` calls a method that is defined in `ClassB`.
    *   You MUST ONLY create dependencies for functions that are explicitly defined in the provided JSON data. IGNORE all calls to built-in or standard library functions (e.g., `fmt.Println`, `os.Open`, `time.NewTimer`, `log.Fatal`, etc.).
    *   ENSURE that **at least one arrow is drawn for every valid cross-class call**, even if only one such call is found.
    *   To keep the diagram clean, ENSURE only one unique dependency arrow is drawn from one class to another, even if multiple calls exist between them.

6.  **CONSISTENCY & OUTPUT**:
    *   To ensure the diagram is stable and repeatable, you MUST process all files, functions, and calls IN THE EXACT ORDER they appear in the JSON.
    *   Your response MUST be ONLY the raw PlantUML syntax, enclosed in `@startuml` and `@enduml`.
    *   DO NOT ADD ANY explanation, title, or any other text outside of the `@startuml` block. Your entire response should be a single PlantUML code block
<JSON_DATA>
{{PASTE JSON HERE}}
</JSON_DATA>
"""


SYS_PROMPT_ARCH_1 = """Modular Documentation Generation System
🔧 SYSTEM PROMPT (Base Configuration)
<system_prompt>
You are a technical documentation expert specializing in software architecture analysis. Your role is to generate consistent, professional documentation sections from JSON code structure data.
Core Guidelines:

Output Format: Markdown only
Tone: Neutral, professional, developer-oriented
Consistency: Use identical phrasing across generations
Focus: Architecture and relationships over implementation details
Audience: Developers new to the project

Input Format:
json{
  "files": [
    {
      "path": "file/path",
      "language": ".extension",
      "functions": [
        {
          "name": "function_name",
          "params": ["param1", "param2"] | null,
          "returns": ["return_type"] | null,
          "start_row": number,
          "end_row": number
        }
      ]
    }
  ]
}
Template Consistency Rules:

Always use exact phrases specified in each section
Maintain identical structure and formatting
Use the same emoji and heading combinations
Follow the specified order and nesting
</system_prompt>

🏗 SECTION 2: Architecture Generator
<section_2_prompt>
Task: Generate architecture section focusing on component relationships and system design.
Required Output Structure:
markdown## 🏗 Architecture

### 1. Directory Structure
- `path/to/directory`: [brief purpose of folder]
- Repeat for each key folder.
Analysis Strategy:

Group files by directory structure
</section_2_prompt>
"""
SYS_PROMPT_ARCH_2 = """Generate a structured Markdown summary of the code's dependencies and internal relationships from the provided JSON AST. The output must be only the Markdown content, ready to be inserted into a larger document. Adhere strictly to the format shown in the example below. Do not add any extra text, titles, or explanations.### Example#### Input (JSON AST Snippet):```json{  "type": "File",  "program": {    "type": "Program",    "sourceType": "module",    "body": [      {        "type": "ImportDeclaration",        "specifiers": [          { "type": "ImportDefaultSpecifier", "local": { "type": "Identifier", "name": "React" } }        ],        "source": { "type": "StringLiteral", "value": "react" }      },      {        "type": "ImportDeclaration",        "specifiers": [          { "type": "ImportSpecifier", "imported": { "type": "Identifier", "name": "apiClient" } }        ],        "source": { "type": "StringLiteral", "value": "./utils/api" }      }    ]  },  "metadata": {    "filePath": "src/components/UserProfile.js"  }}```#### Corresponding Output (Markdown):```markdown### Dependencies and RelationshipsThis section outlines the project's external dependencies and the relationships between its internal modules.#### External Dependencies| Name | Version | Type | Description | Tags ||---|---|---|---|---|| react | N/A | production | A JavaScript library for building user interfaces. | #ui, #framework |#### Internal Module Relationships**Module: `src/components/UserProfile.js`***   **Description:** A component to display user profile information.*   **Dependencies:**    *   Imports `apiClient` from `./utils/api`.*   **Exposes/Calls:**    *   `UserProfile`: A function component that renders the user profile.*   **Tags:** `#component`, `#feature-user````### Your Task#### Input (JSON AST):[Paste the full JSON AST here]#### Output (Markdown):"""
SYS_PROMPT_ARCH_3 = """Generate a structured Markdown summary of the application's API endpoints from the provided JSON AST. The output must be only the Markdown content, ready to be inserted into a larger document. Adhere strictly to the format shown in the example below. Do not add any extra text, titles, or explanations.### Example#### Input (JSON AST Snippet):```json{  "type": "Program",  "body": [    {      "type": "ExpressionStatement",      "expression": {        "type": "CallExpression",        "callee": {          "type": "MemberExpression",          "object": { "type": "Identifier", "name": "app" },          "property": { "type": "Identifier", "name": "get" }        },        "arguments": [          { "type": "StringLiteral", "value": "/api/users/:id" },          { "type": "Identifier", "name": "requireAuth" },          { "type": "Identifier", "name": "getUserById" }        ]      }    }  ],  "metadata": {    "comments": [      { "type": "Line", "value": " Gets a specific user by their ID." }    ]  }}```#### Corresponding Output (Markdown):```markdown### API EndpointsThis section provides a detailed breakdown of all available API endpoints.#### `GET /api/users/:id`*   **Description:** Gets a specific user by their ID.*   **Tags:** `#users`, `#auth-required`| Category | Details ||---|---|| **Authentication** | Required (inferred from `requireAuth` middleware). || **Path Parameters**| `id`: The unique identifier for the user. || **Query Parameters**| *None* || **Request Body** | *None* || **Success Response** | **Code:** `200 OK`<br/>**Content:**<br/>```json<br/>{<br/>  "id": "string",<br/>  "name": "string",<br/>  "email": "string"<br/>}<br/>``` || **Error Response** | **Code:** `404 Not Found`<br/>**Content:**<br/>```json<br/>{<br/>  "error": "User not found."<br/>}<br/>``` |---#### `POST /api/users`*   **Description:** Creates a new user.*   **Tags:** `#users`, `#public`| Category | Details ||---|---|| **Authentication** | Not Required. || **Path Parameters**| *None* || **Query Parameters**| *None* || **Request Body** | ```json<br/>{<br/>  "name": "string",<br/>  "email": "string",<br/>  "password": "string"<br/>}<br/>``` || **Success Response** | **Code:** `201 Created`<br/>**Content:**<br/>```json<br/>{<br/>  "id": "string",<br/>  "name": "string",<br/>  "email": "string"<br/>}<br/>``` || **Error Response** | **Code:** `400 Bad Request`<br/>**Content:**<br/>```json<br/>{<br/>  "error": "Invalid input provided."<br/>}<br/>``` |```### Your Task#### Input (JSON AST):"""



TOOL_DESCRIPTION_RT = """ This is a tool function """

logging.basicConfig(level=logging.INFO)
model="gpt-4o"
temperature = 0


def generate_markdown_doc(data, task_id: str, promnt: str):
    try:
        logging.info(f"Start over v response ")
        response_over_v = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYS_PROMPT_OVER_V},
                {"role": "user", "content": json.dumps(data, ensure_ascii=False)}
            ],
            tools=make_md(),
            tool_choice={"type": "function", "function": {"name": "generate_markdown"}},
            temperature=temperature,
            timeout=60
        )


        if promnt == "full":
          logging.info(f"Start response for full")
          response_arch_1 = client.chat.completions.create(
              model=model,
              messages=[
                  {"role": "system", "content": SYS_PROMPT_ARCH_1},
                  {"role": "user", "content": json.dumps(data, ensure_ascii=False)}
              ],
              tools=make_md(),
              tool_choice={"type": "function", "function": {"name": "generate_markdown"}},
              temperature=temperature,
              timeout=60
            )

          
          response_arch_2 = client.chat.completions.create(
              model=model,
              messages=[
                  {"role": "system", "content": SYS_PROMPT_ARCH_2},
                  {"role": "user", "content": json.dumps(data, ensure_ascii=False)}
              ],
              tools=make_md(),
              tool_choice={"type": "function", "function": {"name": "generate_markdown"}},
              temperature=temperature,
              timeout=60
            )

          response_arch_3 = client.chat.completions.create(
              model=model,
              messages=[
                  {"role": "system", "content": SYS_PROMPT_ARCH_3},
                  {"role": "user", "content": json.dumps(data, ensure_ascii=False)}
              ],
              tools=make_md(),
              tool_choice={"type": "function", "function": {"name": "generate_markdown"}},
              temperature=temperature,
              timeout=60
            )

          result_arch_1 = response_arch_1.choices[0].message.tool_calls[0].function.arguments
          result_arch_2 = response_arch_2.choices[0].message.tool_calls[0].function.arguments
          result_arch_3 = response_arch_3.choices[0].message.tool_calls[0].function.arguments

          arch_1 = json.loads(result_arch_1)
          arch_2 = json.loads(result_arch_2)
          arch_3 = json.loads(result_arch_3)

          merged_arch_dict = {
          "title": "Architecture",
          "content": "\n\n".join([arch_1["content"], arch_2["content"], arch_3["content"]])
            }
          result_arch = json.dumps(merged_arch_dict, ensure_ascii=False)

        else:
          logging.info(f"Start response for short")
          response_arch = client.chat.completions.create(
              model=model,
              messages=[
                  {"role": "system", "content": SYS_PROMPT_ARCH},
                  {"role": "user", "content": json.dumps(data, ensure_ascii=False)}
              ],
              tools=make_md(),
              tool_choice={"type": "function", "function": {"name": "generate_markdown"}},
              temperature=temperature,
              timeout=60
            ) 

          result_arch = response_arch.choices[0].message.tool_calls[0].function.arguments

        logging.info(f"Start user_g ")
        response_user_g = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYS_PROMPT_USER_G},
                {"role": "user", "content": json.dumps(data, ensure_ascii=False)}
            ],
            tools=make_md(),
            tool_choice={"type": "function", "function": {"name": "generate_markdown"}},
            temperature=temperature,
            timeout=60
        )
        logging.info(f"Start uml response")
        response_uml = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYS_PROMPT_UML},
                {"role": "user", "content": json.dumps(data, ensure_ascii=False)}
            ],
            tools=make_uml(),
            tool_choice={"type": "function", "function": {"name": "generate_uml"}},
            temperature=temperature,
            timeout=60
        )

        
        result_over_v = response_over_v.choices[0].message.tool_calls[0].function.arguments
        result_user_g = response_user_g.choices[0].message.tool_calls[0].function.arguments
        result_uml = response_uml.choices[0].message.tool_calls[0].function.arguments

        dict_over_v = json.loads(result_over_v)
        #logging.info(f"Result data for over v {task_id}: {dict_over_v}")

        dict_arch = json.loads(result_arch)
        #logging.info(f"Result data for over v {task_id}: {dict_arch}")

        dict_user_g = json.loads(result_user_g)
        #logging.info(f"Result data for over v {task_id}: {dict_user_g}")

        dict_uml = json.loads(result_uml)
        logging.info(f"Uml from model {task_id}: {result_uml}")

        plantuml_text = dict_uml.get('content', '')
        logging.info(f"Uml from model {task_id}: {plantuml_text}")
        
        uml_url = generate_plantuml_url(plantuml_text)
        uml_md = f"{dict_uml.get('title', 'UML Diagram')}\n[Диаграмма UML]({uml_url})"

        merged_text = "\n\n".join([
        f"{dict_over_v.get('title', '')}\n{dict_over_v.get('content', '')}",
        f"{dict_arch.get('title', '')}\n{dict_arch.get('content', '')}",
        f"{dict_user_g.get('title', '')}\n{dict_user_g.get('content', '')}",
        uml_md  
          ])

        logging.info(f"Merged final content for task {task_id}:\n{merged_text}")
        tokens_merged = count_tokens(merged_text, model_name=model)
        logging.info(f"[{task_id}] Sum of output tokens: {tokens_merged}")

        callback_payload = {
        "uuid": task_id,
        "content": merged_text
        }

        callback_url = "http://code-analyzer:6001/v1/analysis_webhook"
        callback_response = requests.post(callback_url, json=callback_payload)
        callback_response.raise_for_status()

        logging.info(f"Successfully sent result to callback URL for UUID {task_id}")

    except requests.exceptions.RequestException as req_err:
        logging.error(f"Callback request failed for UUID {task_id}: {req_err}")
    except json.JSONDecodeError as json_err:
        logging.error(f"Failed to decode JSON for UUID {task_id}: {json_err}")
    except Exception as e:
        logging.error(f"Unexpected error for UUID {task_id}: {e}")

