# Document Feature

Generate concise markdown documentation for implemented features by analyzing code changes and specifications. This command creates documentation in the `app_docs/` directory based on git diff analysis against the main branch and the original feature specification.

## Variables

adw_id: $ARGUMENT
spec_path: $ARGUMENT if provided, otherwise leave it blank
documentation_screenshots_dir: $ARGUMENT if provided, otherwise leave it blank

## Instructions

### 1. Analyze Changes
- Run `git diff origin/main --stat` to see files changed and lines modified
- Run `git diff origin/main --name-only` to get the list of changed files
- For significant changes (>50 lines), run `git diff origin/main <file>` on specific files to understand the implementation details

### 2. Read Specification (if provided)
- If `spec_path` is provided, read the specification file to understand:
  - Original requirements and goals
  - Expected functionality
  - Success criteria
- Use this to frame the documentation around what was requested vs what was built

### 3. Analyze and Copy Screenshots (if provided)
- If `documentation_screenshots_dir` is provided, list and examine screenshots
- Create `app_docs/assets/` directory if it doesn't exist
- Copy all screenshot files (*.png) from `documentation_screenshots_dir` to `app_docs/assets/`
  - Preserve original filenames
  - Use `cp` command to copy files
- Use visual context to better describe UI changes or visual features
- Reference screenshots in documentation using relative paths (e.g., `assets/screenshot-name.png`)

### 4. Generate Documentation
- Create a new documentation file in `app_docs/` directory
- Filename format: `feature-{adw_id}-{descriptive-name}.md`
  - Replace `{descriptive-name}` with a short feature name (e.g., "user-auth", "data-export", "search-ui")
- Follow the Documentation Format below
- Focus on:
  - What was built (based on git diff)
  - How it works (technical implementation)
  - How to use it (user perspective)
  - Any configuration or setup required

### 5. Update Conditional Documentation
- After creating the documentation file, read `.claude/commands/conditional_docs.md`
- Add an entry for the new documentation file with appropriate conditions
- The entry should help future developers know when to read this documentation
- Format the entry following the existing pattern in the file

### 6. Final Output
- When you finish writing the documentation and updating conditional_docs.md, return exclusively the path to the documentation file created and nothing else

## Documentation Format

```md
# <Feature Title>

**ADW ID:** <adw_id>
**Date:** <current date>
**Specification:** <spec_path or "N/A">

## Overview

<2-3 sentence summary of what was built and why>

## Screenshots

<If documentation_screenshots_dir was provided and screenshots were copied>

![<Description>](assets/<screenshot-filename.png>)

## What Was Built

<List the main components/features implemented based on the git diff analysis>

- <Component/feature 1>
- <Component/feature 2>
- <etc>

## Technical Implementation

### Files Modified

<List key files changed with brief description of changes>

- `<file_path>`: <what was changed/added>
- `<file_path>`: <what was changed/added>

### Key Changes

<Describe the most important technical changes in 3-5 bullet points>

## How to Use

<Step-by-step instructions for using the new feature>

1. <Step 1>
2. <Step 2>
3. <etc>

## Configuration

<Any configuration options, environment variables, or settings>

## Testing

<Brief description of how to test the feature>

## Notes

<Any additional context, limitations, or future considerations>
```

## Conditional Docs Entry Format

After creating the documentation, add this entry to `.claude/commands/conditional_docs.md`:

```md
- app_docs/<your_documentation_file>.md
  - Conditions:
    - When working with <feature area>
    - When implementing <related functionality>
    - When troubleshooting <specific issues>
```

## Report

- IMPORTANT: Return exclusively the path to the documentation file created and nothing else.