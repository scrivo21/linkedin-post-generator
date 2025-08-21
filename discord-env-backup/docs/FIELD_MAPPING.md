# LinkedIn Form Field Mapping

## HTML to Discord Modal Mapping

This document shows how the original HTML form fields map to the Discord modal forms.

### Page 1 (Discord Modal 1)

| HTML Field | Discord Field | Type | Max Length | Notes |
|------------|---------------|------|------------|--------|
| `industry` | `industry` | Short Text | 100 | Topic/Industry |
| `audience` | `audience` | Short Text | 100 | Target Audience |
| `situation` | `situation` | Paragraph | 500 | Specific Situation/Challenge |
| `keyInsight` | `key_insight` | Paragraph | 400 | Key Insight/Lesson |
| `experience` | `experience` | Paragraph | 1000 | Your Experience/Background |

### Page 2 (Discord Modal 2)

| HTML Field | Discord Field | Type | Max Length | Notes |
|------------|---------------|------|------------|--------|
| `credibilitySignpost` | `credibility_signpost` | Short Text | 150 | Credibility Signpost |
| `personalAnecdote` | `personal_anecdote` | Paragraph | 800 | Personal Anecdote |
| `timeframe` | `timeframe` | Short Text | 100 | Timeframe/Context |
| `contextualInfo` | `contextual_info` | Paragraph | 600 | Contextual Information (Optional) |
| `goldenThreads[]` + `spellingError` | `post_options` | Paragraph | 300 | Combined Golden Threads & Spelling Error |

## Golden Threads Mapping

### HTML Form (Checkboxes)
```html
<input type="checkbox" name="goldenThreads" value="data-analysis">
<input type="checkbox" name="goldenThreads" value="community-asset">
```

### Discord Form (Text Input)
```
Golden Threads: data-analysis, community-asset (or both)
Spelling Error: its instead of it's (or leave blank for natural error)

Example: data-analysis | its instead of it's
```

**Parsing Logic:**
- Split on `|` to separate Golden Threads from Spelling Error
- Parse Golden Threads: `data`, `data-analysis` → `data-analysis`
- Parse Golden Threads: `community`, `community-asset` → `community-asset`
- Both can be selected: `data-analysis, community-asset`

## Field Descriptions

### Core Content Fields (Page 1)

**Topic/Industry**
- HTML: "The main industry or topic area your post will focus on"
- Purpose: Tailors content to professional niche

**Target Audience**  
- HTML: "Who are you writing this post for? Be specific about your intended readers"
- Purpose: Focuses content for specific readership

**Specific Situation/Challenge**
- HTML: "Describe the specific scenario, problem, or challenge you want to address"
- Purpose: Provides concrete context for the post

**Key Insight/Lesson**
- HTML: "What's the main point, insight, or lesson you want readers to take away?"
- Purpose: Defines the core message

**Your Experience/Background**
- HTML: "Share your relevant experience, qualifications, or credentials"
- Purpose: Establishes authority on the topic
- **Updated**: Removed artificial 200-char limit from Discord version

### Story Details Fields (Page 2)

**Credibility Signpost**
- HTML: "A brief phrase that establishes your credibility"
- Purpose: Shows how expertise will be referenced
- Examples: "After 12 years in recruitment...", "Having closed over 200 deals..."

**Personal Anecdote**
- HTML: "Share a brief personal story or example that illustrates your key point"
- Purpose: Makes the insight relatable and memorable

**Timeframe/Context**
- HTML: "When did this happen? Provide temporal context"
- Purpose: Grounds the story in time
- Examples: "Last quarter", "During the pandemic", "3 months ago"

**Contextual Information** (Optional)
- HTML: "Add industry trends, statistics, or background information"  
- Purpose: Supports the main point with additional data

**Golden Threads** (Combined with Spelling Error)
- HTML: Two separate checkboxes for predefined themes
- Discord: Combined text input for both threads and spelling preference
- Purpose: Weaves consistent brand themes into content

## Content Generation Rules (Preserved)

### Australian English Requirements
- Use Australian spelling: realise, colour, analyse, organisation
- Conversational mate-to-mate tone
- Natural contractions: I'm, you're, we've

### LinkedIn Structure
- **Hook + Rehook**: First 3 lines as one paragraph (max 200 characters)
- **Professional Credibility**: Through storytelling, not explicit claims
- **No Marketing Elements**: No CTAs, hashtags in body, or emojis
- **One Minor Error**: Deliberate spelling mistake for authenticity

### Golden Threads Content

**Data Analysis Value**
- Theme: "Data needs analysis to become an asset"
- Use for: data, information, insights, decision-making topics

**Community Asset Management**
- Theme: "Community is critical to asset management"  
- Use for: teams, collaboration, knowledge sharing, organizational topics

## Discord Modal Limitations

### Technical Constraints
- **5 Components Max**: Each Discord modal limited to 5 input fields
- **Text Input Types**: Only `Short` and `Paragraph` styles available
- **No Checkboxes**: Must use text input for Golden Threads selection
- **Character Limits**: Must enforce limits that make sense for Discord

### Workarounds Implemented
- **2-Page Form**: Split 11 fields across 2 modals with continue button
- **Combined Fields**: Golden Threads + Spelling Error in single text input
- **Smart Parsing**: Flexible parsing of user input for thread selection
- **Clear Instructions**: Detailed placeholders and help text

## Verification Checklist

- ✅ All 11 HTML fields mapped to Discord
- ✅ Field descriptions preserved and adapted
- ✅ Character limits appropriate for Discord
- ✅ Golden Threads functionality maintained
- ✅ Spelling error specification preserved
- ✅ Australian English rules intact
- ✅ Content structure requirements maintained
- ✅ Professional tone and formatting preserved

## Testing the Mapping

Use the test file to verify field mapping:
```bash
npm test
```

This will:
1. Generate a LinkedIn prompt with all fields
2. Show character counts and validation
3. Test webhook connectivity
4. Verify content generation with sample data

The sample data in `test/bot-test.js` includes all mapped fields to ensure comprehensive testing.