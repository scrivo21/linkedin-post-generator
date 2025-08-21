require('dotenv').config();
const { 
    Client, 
    GatewayIntentBits, 
    ModalBuilder, 
    TextInputBuilder, 
    TextInputStyle, 
    ActionRowBuilder, 
    ButtonBuilder, 
    ButtonStyle, 
    SlashCommandBuilder, 
    EmbedBuilder 
} = require('discord.js');
const axios = require('axios');

// Initialize Discord client
const client = new Client({ 
    intents: [
        GatewayIntentBits.Guilds, 
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ] 
});

// LinkedIn slash command definition
const linkedinCommand = new SlashCommandBuilder()
    .setName('linkedin')
    .setDescription('Create a LinkedIn post with Australian English formatting');

// LinkedIn-specific constants
const LINKEDIN_CHAR_LIMIT = 3000;
const HOOK_REHOOK_LIMIT = 200;
const LINKEDIN_BLUE = 0x0077B5;

// Golden Threads options
const GOLDEN_THREADS = {
    'data-analysis': 'Data Analysis Value: Data needs analysis to become an asset',
    'community-asset': 'Community Asset Management: Community is critical to asset management'
};

// Event handler for bot ready
client.once('ready', async () => {
    console.log(`✅ LinkedIn Discord Bot logged in as ${client.user.tag}`);
    
    try {
        // Register slash command
        await client.application.commands.create(linkedinCommand);
        console.log('✅ LinkedIn slash command registered');
        
        // Send welcome message to main channel
        const channel = client.channels.cache.get(process.env.DISCORD_CHANNEL_ID);
        if (channel) {
            const welcomeEmbed = new EmbedBuilder()
                .setTitle('💼 LinkedIn Post Generator')
                .setDescription('Professional LinkedIn content creation with Australian English formatting\n\n**📋 2-Page Form Process (10 total fields)**\n*Due to Discord limits, forms are split into 2 pages with 5 fields each*')
                .setColor(LINKEDIN_BLUE)
                .addFields([
                    {
                        name: '📋 Page 1 - Core Content',
                        value: '• Topic/Industry & Target Audience\n• Specific Situation/Challenge\n• Key Insight/Lesson\n• Your Experience/Background',
                        inline: true
                    },
                    {
                        name: '📝 Page 2 - Story Details',
                        value: '• Credibility Signpost\n• Personal Anecdote\n• Timeframe/Context\n• Golden Threads & Options',
                        inline: true
                    },
                    {
                        name: '🇦🇺 Australian English Features',
                        value: '• Hook + rehook structure (200 char limit)\n• Mate-to-mate conversational tone\n• Proper Australian spelling\n• One deliberate minor error\n• No CTAs, hashtags, or emojis',
                        inline: false
                    },
                    {
                        name: '🧵 Golden Threads Available',
                        value: '• **Data Analysis Value**: "Data needs analysis to become an asset"\n• **Community Asset Management**: "Community is critical to asset management"',
                        inline: false
                    }
                ])
                .setFooter({
                    text: 'Use /linkedin to start • Form preserves all original HTML functionality'
                })
                .setTimestamp();

            const welcomeButton = new ActionRowBuilder()
                .addComponents(
                    new ButtonBuilder()
                        .setCustomId('create_linkedin_post')
                        .setLabel('📝 Create LinkedIn Post')
                        .setStyle(ButtonStyle.Primary)
                );

            await channel.send({
                embeds: [welcomeEmbed],
                components: [welcomeButton]
            });
            
            console.log('✅ Welcome message sent to main channel');
        }
    } catch (error) {
        console.error('❌ Setup error:', error);
    }
});

// Main interaction handler
client.on('interactionCreate', async interaction => {
    try {
        if (interaction.isChatInputCommand()) {
            if (interaction.commandName === 'linkedin') {
                await showLinkedInModal(interaction);
            }
        }
        
        if (interaction.isButton()) {
            if (interaction.customId === 'create_linkedin_post') {
                await showLinkedInModal(interaction);
            }
            
            if (interaction.customId === 'continue_linkedin_form') {
                console.log('🔄 Continue button clicked by:', interaction.user.username);
                console.log('🔍 Checking stored form data for user:', interaction.user.id);
                console.log('📦 Available form data:', Object.keys(global.linkedinFormData || {}));
                await showLinkedInModalContinue(interaction);
            }
            
            // Handle approval buttons
            if (interaction.customId.startsWith('approve_') || 
                interaction.customId.startsWith('reject_') || 
                interaction.customId.startsWith('edit_')) {
                await handleApprovalAction(interaction);
            }
        }
        
        if (interaction.isModalSubmit()) {
            if (interaction.customId === 'linkedin_post_modal') {
                await handleLinkedInSubmission(interaction);
            }
            
            if (interaction.customId === 'linkedin_post_modal_page2') {
                await handleLinkedInSubmissionComplete(interaction);
            }
        }
        
    } catch (error) {
        console.error('❌ Interaction error:', error);
        if (!interaction.replied && !interaction.deferred) {
            await interaction.reply({ 
                content: '❌ An error occurred processing your request. Please try again.', 
                ephemeral: true 
            });
        }
    }
});

// Create LinkedIn modal form with all fields from original HTML
async function showLinkedInModal(interaction) {
    const modal = new ModalBuilder()
        .setCustomId('linkedin_post_modal')
        .setTitle('LinkedIn Post Generator - Page 1 of 2');

    // Industry/Topic field
    const industryInput = new TextInputBuilder()
        .setCustomId('industry')
        .setLabel('1. Topic/Industry')
        .setStyle(TextInputStyle.Short)
        .setPlaceholder('e.g., Asset Management, Digital Marketing, Data Analysis')
        .setRequired(true)
        .setMaxLength(100);

    // Target Audience field
    const audienceInput = new TextInputBuilder()
        .setCustomId('audience')
        .setLabel('2. Target Audience')
        .setStyle(TextInputStyle.Short)
        .setPlaceholder('e.g., asset managers, startup founders, data professionals')
        .setRequired(true)
        .setMaxLength(100);

    // Situation/Challenge field
    const situationInput = new TextInputBuilder()
        .setCustomId('situation')
        .setLabel('3. Specific Situation/Challenge')
        .setStyle(TextInputStyle.Paragraph)
        .setPlaceholder('Describe the specific scenario or challenge you want to address...')
        .setRequired(true)
        .setMaxLength(500);

    // Key Insight field
    const insightInput = new TextInputBuilder()
        .setCustomId('key_insight')
        .setLabel('4. Key Insight/Lesson')
        .setStyle(TextInputStyle.Paragraph)
        .setPlaceholder('What\'s your main point or takeaway?')
        .setRequired(true)
        .setMaxLength(400);

    // Experience/Background field  
    const experienceInput = new TextInputBuilder()
        .setCustomId('experience')
        .setLabel('5. Your Experience/Background')
        .setStyle(TextInputStyle.Paragraph)
        .setPlaceholder('Your relevant experience, qualifications, or credentials that give you authority on this topic...')
        .setRequired(true)
        .setMaxLength(1000);

    // Add components to action rows (Discord limits to 5 components per modal)
    modal.addComponents(
        new ActionRowBuilder().addComponents(industryInput),
        new ActionRowBuilder().addComponents(audienceInput),
        new ActionRowBuilder().addComponents(situationInput),
        new ActionRowBuilder().addComponents(insightInput),
        new ActionRowBuilder().addComponents(experienceInput)
    );

    await interaction.showModal(modal);
}

// Handle LinkedIn form submission
async function handleLinkedInSubmission(interaction) {
    try {
        // Defer reply to avoid timeout
        await interaction.deferReply({ ephemeral: true });

        // Extract form data
        const formData = {
            industry: interaction.fields.getTextInputValue('industry'),
            audience: interaction.fields.getTextInputValue('audience'),
            situation: interaction.fields.getTextInputValue('situation'),
            keyInsight: interaction.fields.getTextInputValue('key_insight'),
            experience: interaction.fields.getTextInputValue('experience'),
            submittedBy: {
                id: interaction.user.id,
                username: interaction.user.username,
                displayName: interaction.user.displayName || interaction.user.username,
                avatar: interaction.user.displayAvatarURL()
            },
            submittedAt: new Date().toISOString(),
            postId: generatePostId(),
            platform: 'linkedin',
            guildId: interaction.guildId,
            channelId: interaction.channelId
        };

        // Show second modal for remaining fields
        await showLinkedInModalPage2(interaction, formData);

    } catch (error) {
        console.error('❌ LinkedIn submission error:', error);
        await interaction.editReply({
            content: '❌ Error processing your LinkedIn post. Please try again.'
        });
    }
}

// Second modal for remaining LinkedIn fields
async function showLinkedInModalPage2(interaction, existingData) {
    // Store existing data temporarily (in production, use proper storage)
    global.linkedinFormData = global.linkedinFormData || {};
    global.linkedinFormData[interaction.user.id] = existingData;

    // Send a follow-up message with button to continue
    const continueButton = new ActionRowBuilder()
        .addComponents(
            new ButtonBuilder()
                .setCustomId('continue_linkedin_form')
                .setLabel('📝 Continue to Page 2 of 2')
                .setStyle(ButtonStyle.Primary)
        );

    await interaction.editReply({
        content: '✅ **Page 1 of 2 completed!** \n\n📋 **You\'ve filled:** Topic, Audience, Situation, Key Insight, Experience\n📝 **Still needed:** Credibility Signpost, Personal Anecdote, Timeframe, Context, Golden Threads\n\n👇 Click the button below to complete your LinkedIn post:',
        components: [continueButton]
    });
}

// Show the second modal when user clicks continue button
async function showLinkedInModalContinue(interaction) {
    try {
        console.log('📝 Building second modal for user:', interaction.user.username);
        
        const modal = new ModalBuilder()
            .setCustomId('linkedin_post_modal_page2')
            .setTitle('LinkedIn Post Generator - Page 2 of 2');

        // Credibility Signpost
        const credibilityInput = new TextInputBuilder()
            .setCustomId('credibility_signpost')
            .setLabel('6. Credibility Signpost')
            .setStyle(TextInputStyle.Short)
            .setPlaceholder('e.g., "After 12 years in recruitment..." or "Having closed over 200 deals..."')
            .setRequired(true)
            .setMaxLength(150);

        // Personal Anecdote
        const anecdoteInput = new TextInputBuilder()
            .setCustomId('personal_anecdote')
            .setLabel('7. Personal Anecdote')
            .setStyle(TextInputStyle.Paragraph)
            .setPlaceholder('Share a brief personal story or example that illustrates your point...')
            .setRequired(true)
            .setMaxLength(800);

        // Timeframe
        const timeframeInput = new TextInputBuilder()
            .setCustomId('timeframe')
            .setLabel('8. Timeframe/Context')
            .setStyle(TextInputStyle.Short)
            .setPlaceholder('e.g., Last quarter, During the pandemic, 3 months ago')
            .setRequired(true)
            .setMaxLength(100);

        // Contextual Information
        const contextInput = new TextInputBuilder()
            .setCustomId('contextual_info')
            .setLabel('9. Context Info (Optional)')
            .setStyle(TextInputStyle.Paragraph)
            .setPlaceholder('Industry trends, statistics, background info, market conditions...')
            .setRequired(false)
            .setMaxLength(600);

        // Golden Threads & Spelling Error
        const optionsInput = new TextInputBuilder()
            .setCustomId('post_options')
            .setLabel('10. Golden Threads & Options (Optional)')
            .setStyle(TextInputStyle.Paragraph)
            .setPlaceholder('data-analysis, community-asset | its instead of it\'s')
            .setRequired(false)
            .setMaxLength(300);

        modal.addComponents(
            new ActionRowBuilder().addComponents(credibilityInput),
            new ActionRowBuilder().addComponents(anecdoteInput),
            new ActionRowBuilder().addComponents(timeframeInput),
            new ActionRowBuilder().addComponents(contextInput),
            new ActionRowBuilder().addComponents(optionsInput)
        );

        console.log('✅ Second modal built successfully, showing to user');
        await interaction.showModal(modal);
        
    } catch (error) {
        console.error('❌ Error in showLinkedInModalContinue:', error);
        
        if (!interaction.replied && !interaction.deferred) {
            await interaction.reply({
                content: '❌ Error showing second form page. Please try using `/linkedin` command again.',
                ephemeral: true
            });
        } else {
            await interaction.followUp({
                content: '❌ Error showing second form page. Please try using `/linkedin` command again.',
                ephemeral: true
            });
        }
    }
}

// Handle complete LinkedIn submission (page 2)
async function handleLinkedInSubmissionComplete(interaction) {
    try {
        await interaction.deferReply({ ephemeral: true });

        // Get stored data from first modal
        const existingData = global.linkedinFormData?.[interaction.user.id];
        if (!existingData) {
            await interaction.editReply({
                content: '❌ Session expired. Please start over with /linkedin command.'
            });
            return;
        }

        // Extract page 2 form data
        const credibilitySignpost = interaction.fields.getTextInputValue('credibility_signpost');
        const personalAnecdote = interaction.fields.getTextInputValue('personal_anecdote');
        const timeframe = interaction.fields.getTextInputValue('timeframe');
        const contextualInfo = interaction.fields.getTextInputValue('contextual_info') || '';
        const postOptions = interaction.fields.getTextInputValue('post_options') || '';

        // Parse options (Golden Threads and spelling error)
        const [goldenThreadsStr = '', spellingError = ''] = postOptions.split('|').map(s => s.trim());
        
        // Parse Golden Threads - handle both comma-separated and individual values
        let selectedThreads = [];
        if (goldenThreadsStr) {
            selectedThreads = goldenThreadsStr
                .toLowerCase()
                .split(/[,\s]+/)
                .map(s => s.trim())
                .filter(s => s.includes('data') || s.includes('community'))
                .map(thread => {
                    if (thread.includes('data')) return 'data-analysis';
                    if (thread.includes('community')) return 'community-asset';
                    return thread;
                })
                .filter(Boolean);
        }
        
        // Complete form data
        const completeFormData = {
            ...existingData,
            credibilitySignpost,
            personalAnecdote,
            timeframe,
            contextualInfo,
            selectedGoldenThreads: selectedThreads,
            spellingError: spellingError || null,
            completedAt: new Date().toISOString()
        };

        // Clean up temporary storage
        delete global.linkedinFormData[interaction.user.id];

        // Generate LinkedIn content
        const generatedContent = await generateLinkedInContent(completeFormData);
        
        if (generatedContent) {
            // Show preview and send for approval
            await showLinkedInPreview(interaction, completeFormData, generatedContent);
            await sendForApproval(completeFormData, generatedContent);
        } else {
            await interaction.editReply({
                content: '❌ Failed to generate LinkedIn content. Please try again or contact support.'
            });
        }

    } catch (error) {
        console.error('❌ Complete submission error:', error);
        await interaction.editReply({
            content: '❌ Error processing your LinkedIn post. Please try again.'
        });
    }
}

// Generate LinkedIn content using LLM webhook
async function generateLinkedInContent(formData) {
    try {
        const prompt = buildLinkedInPrompt(formData);
        
        const webhookUrl = process.env.LLM_WEBHOOK_URL || process.env.N8N_WEBHOOK_URL;
        const method = process.env.LLM_WEBHOOK_METHOD || 'POST';
        
        if (!webhookUrl) {
            console.error('❌ No webhook URL configured');
            return null;
        }

        const payload = {
            prompt: prompt,
            temperature: 0.7,
            max_tokens: 1500,
            timestamp: new Date().toISOString(),
            source: 'linkedin-discord-bot',
            platform: 'linkedin',
            formData: formData
        };

        console.log('🔄 Sending request to LLM webhook:', webhookUrl);
        
        const response = await axios({
            method: method,
            url: webhookUrl,
            data: payload,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': process.env.N8N_WEBHOOK_TOKEN ? `Bearer ${process.env.N8N_WEBHOOK_TOKEN}` : undefined
            },
            timeout: 30000
        });

        if (response.status === 200) {
            // Handle both direct text response and JSON response
            const content = typeof response.data === 'string' ? response.data : response.data.content || response.data.text || JSON.stringify(response.data);
            console.log('✅ Content generated successfully');
            return content;
        } else {
            console.error('❌ Webhook returned non-200 status:', response.status);
            return null;
        }

    } catch (error) {
        console.error('❌ Content generation error:', error.message);
        if (error.response) {
            console.error('Response status:', error.response.status);
            console.error('Response data:', error.response.data);
        }
        return null;
    }
}

// Build comprehensive LinkedIn prompt (adapted from HTML version)
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

// Show LinkedIn preview
async function showLinkedInPreview(interaction, formData, generatedContent) {
    const previewEmbed = new EmbedBuilder()
        .setTitle('💼 LinkedIn Post Preview')
        .setDescription(generatedContent.length > 4096 ? generatedContent.substring(0, 4093) + '...' : generatedContent)
        .setColor(LINKEDIN_BLUE)
        .setAuthor({
            name: formData.submittedBy.displayName,
            iconURL: formData.submittedBy.avatar
        })
        .addFields([
            {
                name: '📊 Post Stats',
                value: `Characters: ${generatedContent.length}/${LINKEDIN_CHAR_LIMIT}\nTarget: ${formData.audience}\nIndustry: ${formData.industry}`,
                inline: true
            },
            {
                name: '🧵 Golden Threads',
                value: formData.selectedGoldenThreads.length > 0 ? formData.selectedGoldenThreads.join(', ') : 'None selected',
                inline: true
            },
            {
                name: '📝 Post ID',
                value: formData.postId,
                inline: true
            }
        ])
        .setFooter({
            text: 'Post sent for approval • Australian English formatting applied'
        })
        .setTimestamp();

    const actionRow = new ActionRowBuilder()
        .addComponents(
            new ButtonBuilder()
                .setCustomId('create_linkedin_post')
                .setLabel('➕ Create Another Post')
                .setStyle(ButtonStyle.Success)
        );

    await interaction.editReply({
        content: '✅ **LinkedIn post generated successfully!**\n\nYour post has been sent to the approval team and will be published once approved.',
        embeds: [previewEmbed],
        components: [actionRow]
    });
}

// Send post for approval
async function sendForApproval(formData, generatedContent) {
    try {
        const approvalChannel = client.channels.cache.get(process.env.DISCORD_APPROVAL_CHANNEL_ID);
        if (!approvalChannel) {
            console.error('❌ Approval channel not found');
            return;
        }

        const approvalEmbed = new EmbedBuilder()
            .setTitle('📱 LinkedIn Post Approval Required')
            .setDescription(`**Platform:** LinkedIn\n**Submitted by:** ${formData.submittedBy.displayName}\n**Target:** ${formData.audience}\n**Industry:** ${formData.industry}`)
            .setColor(0xFFAA00) // Orange for pending approval
            .addFields([
                {
                    name: '📝 Generated Content',
                    value: generatedContent.length > 1024 ? generatedContent.substring(0, 1021) + '...' : generatedContent,
                    inline: false
                },
                {
                    name: '📊 Post Details',
                    value: `**Characters:** ${generatedContent.length}/${LINKEDIN_CHAR_LIMIT}\n**Golden Threads:** ${formData.selectedGoldenThreads.join(', ') || 'None'}\n**Post ID:** ${formData.postId}`,
                    inline: false
                }
            ])
            .setFooter({
                text: 'LinkedIn Post Approval System'
            })
            .setTimestamp();

        const approvalButtons = new ActionRowBuilder()
            .addComponents(
                new ButtonBuilder()
                    .setCustomId(`approve_${formData.postId}`)
                    .setLabel('✅ Approve & Publish')
                    .setStyle(ButtonStyle.Success),
                new ButtonBuilder()
                    .setCustomId(`reject_${formData.postId}`)
                    .setLabel('❌ Reject')
                    .setStyle(ButtonStyle.Danger),
                new ButtonBuilder()
                    .setCustomId(`edit_${formData.postId}`)
                    .setLabel('✏️ Request Changes')
                    .setStyle(ButtonStyle.Secondary)
            );

        await approvalChannel.send({
            embeds: [approvalEmbed],
            components: [approvalButtons]
        });

        console.log(`✅ Approval request sent for post ${formData.postId}`);

    } catch (error) {
        console.error('❌ Error sending approval request:', error);
    }
}

// Generate unique post ID
function generatePostId() {
    return `linkedin_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;
}

// Handle approval actions
async function handleApprovalAction(interaction) {
    const [action, postId] = interaction.customId.split('_', 2);
    
    try {
        // Send approval response to N8N webhook
        const approvalData = {
            postId,
            action,
            timestamp: new Date().toISOString(),
            approvedBy: {
                id: interaction.user.id,
                username: interaction.user.username,
                displayName: interaction.user.displayName || interaction.user.username
            }
        };

        if (process.env.N8N_APPROVAL_WEBHOOK) {
            await axios.post(process.env.N8N_APPROVAL_WEBHOOK, approvalData, {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': process.env.N8N_WEBHOOK_TOKEN ? `Bearer ${process.env.N8N_WEBHOOK_TOKEN}` : undefined
                },
                timeout: 15000
            });
        }

        // Update the approval message
        const actionEmojis = {
            approve: '✅',
            reject: '❌', 
            edit: '✏️'
        };

        const actionTexts = {
            approve: 'APPROVED - Post will be published to LinkedIn',
            reject: 'REJECTED - Post cancelled',
            edit: 'EDIT REQUESTED - Awaiting changes'
        };

        const updatedEmbed = EmbedBuilder.from(interaction.message.embeds[0])
            .addFields({
                name: 'Decision',
                value: `${actionEmojis[action]} **${actionTexts[action]}**\nBy: ${interaction.user.displayName}`,
                inline: false
            })
            .setColor(action === 'approve' ? 0x00FF00 : action === 'reject' ? 0xFF0000 : 0xFFAA00);

        await interaction.update({
            embeds: [updatedEmbed],
            components: [] // Remove buttons after decision
        });

    } catch (error) {
        console.error('❌ Approval action error:', error);
        await interaction.reply({
            content: '❌ Error processing approval action.',
            ephemeral: true
        });
    }
}

// Error handling
client.on('error', error => {
    console.error('❌ Discord client error:', error);
});

process.on('unhandledRejection', error => {
    console.error('❌ Unhandled promise rejection:', error);
});

// Start the bot
client.login(process.env.DISCORD_BOT_TOKEN);