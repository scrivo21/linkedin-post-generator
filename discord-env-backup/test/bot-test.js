require('dotenv').config();
const axios = require('axios');

// Test configuration
const TEST_CONFIG = {
    webhookUrl: process.env.LLM_WEBHOOK_URL || process.env.N8N_WEBHOOK_URL,
    method: process.env.LLM_WEBHOOK_METHOD || 'POST',
    token: process.env.N8N_WEBHOOK_TOKEN
};

// Test data matching LinkedIn form structure
const testLinkedInData = {
    industry: 'Asset Management',
    audience: 'asset managers and maintenance professionals',
    situation: 'A major equipment failure that could have been prevented with better data analysis',
    keyInsight: 'Data without analysis is just expensive digital hoarding',
    experience: 'After 15 years in asset management across mining and manufacturing',
    credibilitySignpost: 'Having managed over $500M in critical assets',
    personalAnecdote: 'Last month, I watched a $2M pump fail because we had all the vibration data but no one was actually analyzing the trends. The data was sitting there, screaming that something was wrong, but it might as well have been invisible.',
    timeframe: 'Last month',
    contextualInfo: 'Industry statistics show that 70% of unplanned downtime could be prevented with proper data analysis',
    selectedGoldenThreads: ['data-analysis'],
    spellingError: 'its instead of it\'s',
    submittedBy: {
        id: 'test_user_123',
        username: 'testuser',
        displayName: 'Test User',
        avatar: 'https://example.com/avatar.png'
    },
    submittedAt: new Date().toISOString(),
    postId: `linkedin_test_${Date.now()}`,
    platform: 'linkedin'
};

// Test LinkedIn prompt generation
function testPromptGeneration() {
    console.log('🧪 Testing LinkedIn prompt generation...\n');
    
    const prompt = buildLinkedInPrompt(testLinkedInData);
    console.log('Generated prompt:');
    console.log('─'.repeat(80));
    console.log(prompt);
    console.log('─'.repeat(80));
    console.log(`\n✅ Prompt generated successfully (${prompt.length} characters)\n`);
    
    return prompt;
}

// Test webhook connectivity
async function testWebhookConnectivity() {
    console.log('🔗 Testing webhook connectivity...\n');
    
    if (!TEST_CONFIG.webhookUrl) {
        console.log('❌ No webhook URL configured in environment variables');
        console.log('Set LLM_WEBHOOK_URL or N8N_WEBHOOK_URL in .env file\n');
        return false;
    }
    
    try {
        const testPayload = {
            prompt: 'Test prompt for LinkedIn bot connectivity',
            temperature: 0.7,
            max_tokens: 100,
            timestamp: new Date().toISOString(),
            source: 'linkedin-discord-bot-test',
            test: true
        };
        
        console.log(`🔄 Sending test request to: ${TEST_CONFIG.webhookUrl}`);
        
        const response = await axios({
            method: TEST_CONFIG.method,
            url: TEST_CONFIG.webhookUrl,
            data: testPayload,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': TEST_CONFIG.token ? `Bearer ${TEST_CONFIG.token}` : undefined
            },
            timeout: 10000
        });
        
        console.log(`✅ Webhook connectivity test successful`);
        console.log(`Response status: ${response.status}`);
        console.log(`Response type: ${typeof response.data}`);
        console.log(`Response preview: ${JSON.stringify(response.data).substring(0, 200)}...\n`);
        
        return true;
        
    } catch (error) {
        console.log(`❌ Webhook connectivity test failed`);
        console.log(`Error: ${error.message}`);
        if (error.response) {
            console.log(`Response status: ${error.response.status}`);
            console.log(`Response data: ${JSON.stringify(error.response.data)}`);
        }
        console.log('');
        return false;
    }
}

// Test complete LinkedIn content generation
async function testContentGeneration() {
    console.log('📝 Testing complete LinkedIn content generation...\n');
    
    const prompt = buildLinkedInPrompt(testLinkedInData);
    
    if (!TEST_CONFIG.webhookUrl) {
        console.log('❌ Cannot test content generation - no webhook URL configured\n');
        return;
    }
    
    try {
        const payload = {
            prompt: prompt,
            temperature: 0.7,
            max_tokens: 1500,
            timestamp: new Date().toISOString(),
            source: 'linkedin-discord-bot-test',
            platform: 'linkedin',
            formData: testLinkedInData
        };
        
        console.log('🔄 Generating LinkedIn content...');
        
        const response = await axios({
            method: TEST_CONFIG.method,
            url: TEST_CONFIG.webhookUrl,
            data: payload,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': TEST_CONFIG.token ? `Bearer ${TEST_CONFIG.token}` : undefined
            },
            timeout: 30000
        });
        
        const content = typeof response.data === 'string' ? response.data : response.data.content || response.data.text || JSON.stringify(response.data);
        
        console.log('✅ LinkedIn content generated successfully!\n');
        console.log('Generated LinkedIn Post:');
        console.log('═'.repeat(80));
        console.log(content);
        console.log('═'.repeat(80));
        console.log(`\nContent stats:`);
        console.log(`- Characters: ${content.length}/3000`);
        console.log(`- Lines: ${content.split('\n').length}`);
        console.log(`- Contains "IMAGE PROMPT": ${content.includes('IMAGE PROMPT') ? 'Yes' : 'No'}`);
        console.log(`- Australian spelling check: ${content.includes('realise') || content.includes('colour') || content.includes('analyse') ? 'Likely ✅' : 'Check manually'}`);
        
    } catch (error) {
        console.log('❌ Content generation test failed');
        console.log(`Error: ${error.message}`);
        if (error.response) {
            console.log(`Response status: ${error.response.status}`);
            console.log(`Response data: ${JSON.stringify(error.response.data)}`);
        }
        console.log('');
    }
}

// Build LinkedIn prompt (duplicated from bot.js for testing)
function buildLinkedInPrompt(data) {
    const goldenThreadsText = data.selectedGoldenThreads && data.selectedGoldenThreads.length > 0 
        ? data.selectedGoldenThreads.map(thread => {
            if (thread === 'data' || thread === 'data-analysis') return 'Data Analysis Value: Data needs analysis to become an asset';
            if (thread === 'community' || thread === 'community-asset') return 'Community Asset Management: Community is critical to asset management';
            return thread;
        }).join(', ')
        : 'None selected - choose themes that naturally fit';

    return `# LinkedIn Post Prompt - Australian English Professional Content

You are a skilled LinkedIn content creator writing in Australian English. Create a conversational LinkedIn post following these specific requirements:

## STRUCTURE REQUIREMENTS:

- Hook (Line 1): One compelling line that grabs attention
- Rehook (Lines 2-3): Two lines that build intrigue and draw the reader in
- CRITICAL: The first 3 lines must form one continuous paragraph (no line breaks/returns) and be 200 characters or less total
- Main Content: Develop the topic with personal insights and experiences

## WRITING STYLE:

- Use Australian English (e.g., 'realise' not 'realize', 'colour' not 'color')
- Maintain a conversational tone - write as if talking to a mate
- Include one minor spelling error naturally${data.spellingError ? ` (specifically: ${data.spellingError})` : ' (e.g., \'it\'s\' instead of \'its\', or a missing letter)'}
- Use contractions where natural (I'm, you're, we've, etc.)

## YOUR SPECIFIC DETAILS:

- Topic/Industry: ${data.industry}
- Target Audience: ${data.audience}
- Specific Situation/Challenge: ${data.situation}
- Key Insight/Lesson: ${data.keyInsight}
- Your Experience/Background: ${data.experience}
- Credibility Signpost: ${data.credibilitySignpost}
- Personal Anecdote: ${data.personalAnecdote}
- Timeframe/Context: ${data.timeframe}

## CONTEXTUAL INFORMATION:

${data.contextualInfo || 'No additional context provided'}

## GOLDEN THREADS:

Selected themes to weave into content: ${goldenThreadsText}

## CONTENT STRUCTURE:

1. Opening Hook + Rehook (First 3 lines as one continuous paragraph - MAX 200 characters total)
2. Context Setting (Where you establish your credibility using: "${data.credibilitySignpost}")
3. Main Story/Insight (Your key point with supporting details from: "${data.personalAnecdote}")
4. Broader Implications (Why this matters to your audience: ${data.audience})
5. Closing Thought (End with reflection, no call to action)

## WHAT NOT TO INCLUDE:

- No call to action at the end of the post
- No "What are your thoughts?" or "Let me know in the comments"
- No direct asks for engagement
- No hashtags anywhere in the post
- No emojis anywhere in the post
- No overly promotional language

## REMEMBER:

Your expertise should come through naturally in your storytelling, not through explicit claims. Show, don't tell.

## IMAGE PROMPT REQUIREMENT:

After creating the LinkedIn post, provide a separate image generation prompt that visually represents the content and themes of your post. The image prompt should:

- Be 1000x1000 pixels, high DPI
- Use a colour palette of deep blues and vibrant greens
- Be realistic in nature (not abstract or cartoon-like)
- Visually represent the key themes, industry, or concepts from your post
- Include relevant professional or industry-specific elements
- Be suitable for LinkedIn's professional audience

Format the image prompt as: "IMAGE PROMPT: [your detailed prompt here]"

Now create the LinkedIn post based on the above requirements and details, followed by the image prompt.`;
}

// Run all tests
async function runAllTests() {
    console.log('🚀 LinkedIn Discord Bot Test Suite\n');
    console.log('Testing configuration:');
    console.log(`- Webhook URL: ${TEST_CONFIG.webhookUrl || 'Not configured'}`);
    console.log(`- Method: ${TEST_CONFIG.method}`);
    console.log(`- Has Token: ${TEST_CONFIG.token ? 'Yes' : 'No'}\n`);
    console.log('─'.repeat(80));
    
    // Test 1: Prompt generation
    testPromptGeneration();
    
    // Test 2: Webhook connectivity
    const webhookOk = await testWebhookConnectivity();
    
    // Test 3: Complete content generation (only if webhook is working)
    if (webhookOk) {
        await testContentGeneration();
    }
    
    console.log('🎯 Test suite completed!\n');
    console.log('Next steps:');
    console.log('1. Configure .env file with Discord bot token');
    console.log('2. Set up Discord channels for bot and approvals');
    console.log('3. Run: npm run dev');
    console.log('4. Test /linkedin command in Discord\n');
}

// Run tests if called directly
if (require.main === module) {
    runAllTests().catch(console.error);
}

module.exports = {
    testPromptGeneration,
    testWebhookConnectivity,
    testContentGeneration,
    buildLinkedInPrompt
};