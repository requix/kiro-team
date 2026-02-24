# Track Agentic KPIs

Update or create the ADW performance tracking tables in `app_docs/agentic_kpis.md`. This command analyzes the current ADW run's metrics and maintains both summary and detailed KPI tables. Think hard about building this, these are key KPIs for the AI Developer Workflow (ADW) system. Use the python commands as suggestions and guides for how to calculate the values. Ultimately, do whatever python calculation you need to do to get the values.

## Variables

state_json: $ARGUMENTS
attempts_incrementing_adws: [`adw_plan_iso`, `adw_patch_iso`]

## Instructions

### 1. Parse State Data
- Parse the provided state_json to extract:
  - adw_id
  - issue_number
  - issue_class
  - plan_file path
  - all_adws list (contains workflow names run)

### 2. Calculate Metrics

#### Get Current Date/Time
- Run `date` command to get current date/time

#### Calculate Attempts
IMPORTANT: Use Python to calculate the exact count value:
- Count occurrences of any of the adws in the attempts_incrementing_adws list in all_adws list
- Run: `python -c "all_adws = <list>; attempts = sum(1 for w in all_adws if any(adw in w for adw in attempts_incrementing_adws)); print(attempts)"`

#### Calculate Plan Size
- If plan_file exists in state, read the file
- Count total lines using: `wc -l <plan_file>`
- If file doesn't exist, use 0

#### Calculate Diff Statistics
- Run: `git diff origin/main --shortstat`
- Parse output to extract:
  - Files changed
  - Lines added
  - Lines removed
- Format as: "Added/Removed/Total Files" (e.g., "150/25/8")

### 3. Read Existing File
- Check if `app_docs/agentic_kpis.md` exists
- If it exists, read and parse the existing tables
- If not, prepare to create new file with both tables

### 4. Update ADW KPIs Table
- Check if current adw_id already exists in the table
- If exists: update that row with new values
- If not: append new row at the bottom
- Set Created date on new rows, Updated date on existing rows
- Use `date` command for timestamps

### 5. Calculate Agentic KPIs

IMPORTANT: All calculations must be done using Python expressions. Use `python -c "print(expression)"` for every numeric calculation.

#### Current Streak
- Count consecutive rows from bottom of ADW KPIs table where Attempts ≤ 2
- Use Python: `python -c "attempts_list = <list>; streak = 0; for a in reversed(attempts_list): streak = streak + 1 if a <= 2 else break; print(streak)"`

#### Longest Streak
- Find longest consecutive sequence where Attempts ≤ 2
- Use Python to calculate

#### Total Plan Size
- Sum all plan sizes from ADW KPIs table
- Use Python: `python -c "sizes = <list>; print(sum(sizes))"`

#### Largest Plan Size
- Find maximum plan size
- Use Python: `python -c "sizes = <list>; print(max(sizes) if sizes else 0)"`

#### Total Diff Size
- Sum all diff statistics (added + removed lines)
- Parse each diff entry and sum using Python

#### Largest Diff Size
- Find maximum diff (added + removed lines)
- Use Python to calculate

#### Average Presence
- Calculate average of all attempts
- Use Python: `python -c "attempts = <list>; print(sum(attempts) / len(attempts) if attempts else 0)"`
- Round to 2 decimal places

### 6. Write Updated File
- Create/update `app_docs/agentic_kpis.md` with the structure below
- Ensure proper markdown table formatting
- Include "Last Updated" timestamp using `date` command

## File Structure

```markdown
# Agentic KPIs

Performance metrics for the AI Developer Workflow (ADW) system.

## Agentic KPIs

Summary metrics across all ADW runs.

| Metric            | Value          | Last Updated |
| ----------------- | -------------- | ------------ |
| Current Streak    | <number>       | <date>       |
| Longest Streak    | <number>       | <date>       |
| Total Plan Size   | <number> lines | <date>       |
| Largest Plan Size | <number> lines | <date>       |
| Total Diff Size   | <number> lines | <date>       |
| Largest Diff Size | <number> lines | <date>       |
| Average Presence  | <number>       | <date>       |

## ADW KPIs

Detailed metrics for individual ADW workflow runs.

| Date   | ADW ID | Issue Number | Issue Class | Attempts   | Plan Size (lines) | Diff Size (Added/Removed/Files) | Created   | Updated   |
| ------ | ------ | ------------ | ----------- | ---------- | ----------------- | ------------------------------- | --------- | --------- |
| <date> | <id>   | <number>     | <class>     | <attempts> | <size>            | <diff>                          | <created> | <updated> |
```

## Report

Return only: "Updated app_docs/agentic_kpis.md"