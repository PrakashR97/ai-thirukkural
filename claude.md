# Project: AI Thirukkural Application Using AutoGen, RAG, and GPT-4o mini

Build a complete, working AI Thirukkural application using the requirements below. Work directly in the current project directory. Inspect existing files before making changes, reuse valid existing code, and do not overwrite user data unnecessarily.

## 1. Project Objective

Build an AI-powered Thirukkural application containing all **1,330 Thirukkural verses**.

Users should be able to browse all Kurals, search by Kural number or Tamil words, select any Kural, and receive:

1. The original Thirukkural.
2. Individual word meanings in Tamil.
3. A simple Tamil explanation of the complete Kural.
4. One easy-to-understand Tamil story based on the Kural.
5. One practical life lesson in Tamil.

The application must be functional, maintainable, cost-conscious, and suitable for future expansion.

## 2. Technology Stack

Use the following technologies:

- **Frontend:** React with TypeScript and Vite.
- **Backend:** Python with FastAPI.
- **AI agent framework:** AutoGen.
- **AI model:** OpenAI GPT-4o mini (`gpt-4o-mini`) for all AI generation and analysis.
- **Source dataset:** My existing JSON dataset containing all 1,330 Kurals.
- **RAG:** Retrieval-Augmented Generation using the available Kural dataset.
- **Caching:** SQLite.
- **External research:** SerperDev Search API, only when necessary.
- **Python environment:** Python 3.12 virtual environment.
- **Secrets:** Environment variables loaded from a backend `.env` file.

Use compatible, currently documented package versions. Verify the current AutoGen APIs before implementing the agent workflow. Do not blindly copy outdated AutoGen examples.

Do not substitute a different agent framework without explaining the compatibility issue first.

## 3. Dataset Requirements

I currently have only the dataset containing the 1,330 original Thirukkural verses. I do not have a separate commentary dataset or a verified word-meaning dataset.

Use my existing dataset as the primary source of truth.

Requirements:

- Preserve all original Tamil verses exactly as supplied.
- Preserve Kural numbers.
- Include section, chapter number, and chapter name when available.
- Organize the 1,330 Kurals according to their traditional structure:
  - 3 sections (பால்கள்).
  - 133 chapters (அதிகாரங்கள்).
  - 10 Kurals per chapter.
- Support reliable lookup by Kural number.
- Support chapter browsing and Tamil keyword search.
- Validate that exactly 1,330 unique Kural records exist.
- Verify that Kural numbers cover 1 through 1,330 without gaps.
- Report missing, duplicate, or malformed records.
- Do not invent missing verses or silently change source text.
- Do not assume the dataset contains commentaries or word meanings unless they are actually present.
- Keep the original dataset read-only during normal application operation.

Place the dataset under:

`backend/data/`

Inspect the actual JSON structure and adapt the data-loading code to it. Do not assume field names or JSON structure before examining the files.

If the dataset has not yet been added to the project, ask me to provide it rather than generating a replacement dataset.

## 4. User Interface Requirements

Build a modern, responsive React interface with Tamil as the primary display language.

### Strict two-color design

Use only these two primary colors:

- Cream: `#FAF7F0`
- Dark green: `#244C3A`

Design requirements:

- No gradients.
- No radiant or rainbow colors.
- No neon colors.
- No additional accent-color palette.
- Use the two primary colors consistently for backgrounds, navigation, buttons, borders, text, and interactive states.
- Use appropriate tints and shades of these same colors where needed.
- Keep the interface clean, readable, and uncluttered.
- Use accessible contrast and readable Tamil typography.
- Avoid excessive animations, shadows, and decorative effects.
- Ensure the UI works on desktop, tablet, and mobile.

Do not introduce additional colored UI elements through component-library defaults.

### Main screen

Display:

- Application name: AI திருக்குறள்.
- Total Kural count: 1,330.
- Search by Kural number or Tamil words.
- Navigation by section (பால்).
- Navigation by chapter (அதிகாரம்).
- Original Kural text and its number.
- Pagination or efficient browsing controls.
- Clear loading, empty, and error states.

The home screen must load the original dataset without making OpenAI API calls.

Do not generate AI explanations for all 1,330 Kurals in advance.

### Kural details screen

When the user clicks a Kural, show a details page or panel containing the following sections in Tamil.

**1. திருக்குறள்**

- Kural number.
- Section name.
- Chapter number and name.
- Original Tamil verse exactly as stored in the dataset.

**2. சொல் வாரியான பொருள்**

For each word or meaningful word unit, display:

- Original Tamil word or phrase.
- Simple Tamil meaning.
- Meaning in the context of the selected Kural.

Explain the words individually rather than providing only a general paragraph.

Do not force an inaccurate seven-part split if the Kural's grammar requires meaningful word units to be explained together. Preserve the original wording.

**3. எளிய விளக்கம்**

Explain the complete Kural in simple, natural Tamil suitable for beginners and children.

**4. சிறுகதை**

Generate one short, engaging Tamil story illustrating the Kural's message.

The story should contain relatable characters, a clear situation, and a meaningful ending.

After the story, explain briefly how it connects to the Kural.

**5. வாழ்க்கைப் பாடம்**

Provide one practical lesson that the reader can apply in everyday life.

All user-facing Kural explanations, stories, and life lessons must be in Tamil.

Technical labels, source code, and developer documentation may use English.

## 5. Required AutoGen Agents

Implement three specialized agents using AutoGen.

### Agent 1: Thirukkural Explanation Agent

Responsibilities:

- Receive the selected Kural's verified source text, number, and available chapter metadata.
- Use the retrieved source text as context.
- Generate individual word or meaningful word-unit explanations in Tamil.
- Generate the overall explanation in simple Tamil.
- Avoid changing the original Kural.
- Avoid unsupported historical claims.
- Clearly distinguish AI-generated meanings from source-verified information.

### Agent 2: Story Creation Agent

Responsibilities:

- Receive the original Kural and its explanation.
- Generate one simple, engaging Tamil story based on the Kural's message.
- Ensure the story is understandable to beginners and children.
- Include a short explanation connecting the story to the Kural.
- Avoid introducing an unrelated moral.

### Agent 3: Review Agent

Responsibilities:

- Receive the original Kural, generated word meanings, overall explanation, and story.
- Check whether the explanation and story are consistent with the source text.
- Identify contradictions, missing explanations, and unsupported claims.
- Request a correction when necessary.
- Return a structured, UI-ready result.
- Do not claim that a result is verified against authoritative commentary when no such commentary is available.

The Review Agent can assess consistency, but an AI-generated review must not be presented as a guarantee of scholarly accuracy.

### Agent coordination

Use a controlled AutoGen workflow.

- Avoid unlimited agent conversations.
- Limit correction attempts.
- Avoid sending unnecessary conversation history.
- Pass only the relevant Kural and generated content between agents.
- Return a clear error if generation or review fails.
- Do not mark a result as reviewed if the Review Agent has not completed successfully.

## 6. RAG Requirements

I currently have only the original 1,330 Kural dataset.

Do not assume that I have additional commentaries, external documents, or verified word meanings.

Implement a simple, reliable RAG workflow first.

### Retrieval workflow

1. The user selects a Kural.
2. The backend retrieves the exact record from the local JSON dataset using the Kural number.
3. The backend supplies the original Kural and available metadata as context for the AI agents.
4. The Explanation Agent generates the word meanings and simple explanation.
5. The Story Creation Agent generates a related story.
6. The Review Agent checks the generated output against the original Kural and explanation.
7. The backend returns the result to the frontend.
8. Save the successfully reviewed result in SQLite for future reuse.

### RAG implementation constraints

- Start with exact retrieval by Kural number.
- Use the selected Kural as the primary source context.
- Include available chapter and section metadata.
- Do not send the entire dataset to the model.
- Do not create a vector database unnecessarily.
- Do not call an embedding API merely to retrieve a Kural by its number.
- Add semantic retrieval only if a real requirement emerges, such as searching additional commentary documents.
- Do not claim that retrieval from the original verse alone independently verifies every word meaning.
- Never invent citations or pretend that commentary exists when it does not.
- Keep source text separate from AI-generated content.

The initial RAG system should be lightweight and inexpensive.

## 7. OpenAI Model and Configuration

Use `gpt-4o-mini` for all AI analysis, generation, and review.

Read the model name from `OPENAI_MODEL`, with `gpt-4o-mini` as the default.

Example backend `.env` file:

```dotenv
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
SERPER_API_KEY=your_serper_api_key
```

Create `.env.example` with placeholder values only.

Security requirements:

- Never hardcode API keys.
- Never expose API keys in React or browser code.
- Never commit `.env` to Git.
- Add `.env` to `.gitignore`.
- Validate required configuration at backend startup.
- Do not print secrets in logs or error messages.

Do not switch to a more expensive model automatically.

## 8. SerperDev Search Requirements

Use SerperDev only when external research is genuinely needed.

Examples:

- The user requests additional source verification.
- The existing local dataset does not contain information needed for a research task.
- A trusted external reference is necessary to investigate a disputed meaning.

Do not search the web for every Kural.

Requirements:

- Keep the SerperDev key on the backend.
- Use timeouts and limited retries.
- Handle missing keys and failed searches gracefully.
- Do not treat arbitrary search results as authoritative.
- Do not let web results overwrite the original Kural.
- Clearly distinguish retrieved external information from AI-generated content.

The core application must still work when SerperDev is unavailable.

## 9. Token and API Cost Optimization

Minimize unnecessary OpenAI token usage and API calls.

Implement these requirements:

- Use GPT-4o mini for all model calls.
- Do not call AI during normal browsing or searching.
- Generate AI output only when a user opens a Kural whose result is not cached.
- Store reviewed results in SQLite.
- Reuse cached results on subsequent requests.
- Use the Kural number, model identifier, prompt version, and relevant configuration version to identify cached results.
- Invalidate cached results when the prompt or generation configuration changes.
- Do not send all 1,330 Kurals to the model.
- Do not resend unrelated conversation history.
- Keep system prompts short and task-specific.
- Set reasonable output-token limits.
- Avoid repeated generation when a successful result already exists.
- Limit retries and review correction attempts.
- Do not automatically regenerate results when a user refreshes the page.
- Provide a deliberate refresh or regenerate action only if needed.
- Avoid paid embedding calls for exact lookup.
- Do not generate all 1,330 explanations in the background.

Track:

- OpenAI request count.
- Input and output token usage when returned by the API.
- Cache hits and misses.
- Generation failures.
- Review failures.
- Estimated API cost when reliable pricing information is configured.

Never claim a precise cost saving without measured usage data.

### Cost-conscious agent workflow

Keep the three specialized agents, but design the orchestration to minimize unnecessary calls.

- Run the Explanation Agent only for uncached requests.
- Run the Story Creation Agent only when its result is not already available.
- Run the Review Agent before marking the combined result as reviewed.
- If correction is needed, permit a limited correction attempt.
- Cache the final reviewed result.
- Do not skip the Review Agent silently just to save tokens.

## 10. SQLite Caching and Data Storage

Use SQLite for caching generated explanations and stories.

Suggested structure:

- `kural_cache`: Kural number, model, prompt version, generated word meanings, explanation, story, life lesson, review status, and timestamps.
- `usage_logs`: request type, model, token counts, cache status, and success/failure information.

Requirements:

- Do not store API keys in SQLite.
- Avoid duplicating the original dataset unnecessarily.
- Do not overwrite source records with generated explanations.
- Use parameterized SQL queries.
- Handle concurrent requests safely.
- Return cached results without invoking the agents again.
- Store only results that meet the application's review requirements.

## 11. Backend API Requirements

Create FastAPI endpoints such as:

- `GET /api/kurals` — paginated Kural list.
- `GET /api/kurals/{number}` — retrieve the original Kural and metadata.
- `GET /api/sections` — list available sections.
- `GET /api/chapters` — list chapters.
- `GET /api/chapters/{number}/kurals` — retrieve Kurals in a chapter.
- `GET /api/search?q=...` — search by Kural number or Tamil text.
- `POST /api/kurals/{number}/explain` — retrieve a cached reviewed result or generate a new one.
- `GET /api/health` — basic health check.

Use appropriate HTTP status codes, request validation, timeouts, and error handling.

Do not expose stack traces or secrets to the frontend.

Prevent duplicate model generation for concurrent requests targeting the same uncached Kural where practical.

## 12. Frontend and Backend Integration

Requirements:

- Configure React to communicate with FastAPI through environment-based backend URLs.
- Use loading indicators while AI content is being generated.
- Display the original Kural immediately.
- Display generated sections when the result is ready.
- Handle network failures and server errors gracefully.
- Support browser refresh and direct navigation to a Kural.
- Ensure Tamil characters render correctly.
- Do not place OpenAI or SerperDev API keys in frontend environment variables.
- Maintain the two-color design throughout all screens, including errors, loading states, and dialogs.

## 13. Testing Requirements

Write and run tests for:

### Dataset

- Exactly 1,330 unique records.
- Kural numbers 1 through 1,330 without gaps.
- Valid original Tamil text.
- Correct chapter and section metadata when available.
- No accidental source-text modifications.

### Backend

- List and detail endpoints.
- Search by Kural number.
- Tamil keyword search.
- Chapter navigation.
- Invalid Kural numbers.
- Missing configuration.
- AI generation failures.
- Cache hits and misses.
- Duplicate concurrent requests where supported.

### AI workflow

- Explanation Agent output structure.
- Story Agent output structure.
- Review Agent output structure.
- Limited correction attempts.
- Tamil output requirements.
- Consistency with the original Kural.
- No invented source citations.
- Repeated requests reuse cached results.

Use mocked model responses for automated tests wherever possible. Do not spend API credits running unnecessary real-model tests.

### UI

- All 1,330 Kurals are browseable.
- Search and chapter navigation work.
- Clicking a Kural displays the correct original text.
- All required detail sections are displayed.
- Loading and error states work.
- Only the two specified primary colors are used as the primary palette.
- The UI works on mobile and desktop.

## 14. Project Structure

Use a maintainable structure similar to:

```text
ai-thirukkural/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   ├── agents/
│   │   │   ├── explanation_agent.py
│   │   │   ├── story_agent.py
│   │   │   ├── review_agent.py
│   │   │   └── workflow.py
│   │   ├── services/
│   │   │   ├── dataset_service.py
│   │   │   ├── rag_service.py
│   │   │   ├── cache_service.py
│   │   │   └── search_service.py
│   │   └── models/
│   ├── data/
│   │   └── [existing Kural JSON files]
│   ├── tests/
│   ├── .env.example
│   ├── .gitignore
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env.example
├── README.md
└── .gitignore
```

Adjust the structure when justified by the existing project or current library requirements. Do not create empty modules that serve no purpose.

## 15. Implementation and Completion

Before implementation:

1. Inspect the current project directory.
2. Identify the existing dataset files and their actual structure.
3. Check the installed Python and Node.js versions.
4. Verify the current AutoGen package APIs.
5. Present a concise implementation plan.

Then implement the application in logical stages without unnecessarily replacing existing working code.

After implementation:

- Install compatible dependencies.
- Run automated tests.
- Run dataset validation.
- Run frontend and backend checks.
- Fix errors that can be reproduced.
- Confirm that the app starts using the documented commands.
- Verify that the application does not call OpenAI while browsing.
- Verify that a second request for an already cached Kural does not repeat generation.
- Verify that the original Kural text remains unchanged.
- Report any unfinished functionality honestly.

Provide a README containing setup instructions, environment configuration, test commands, and exact commands to start the frontend and backend.

At completion, summarize the implemented features, important files, test results, and remaining limitations.

The final application must contain all 1,330 original Kurals, use the three AutoGen agents, use GPT-4o mini for AI calls, implement lightweight RAG with the available dataset, minimize unnecessary token usage, and maintain the strict cream and dark-green UI design.
