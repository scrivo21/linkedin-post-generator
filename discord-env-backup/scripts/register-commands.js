require('dotenv').config();
const { REST, Routes, SlashCommandBuilder } = require('discord.js');

// LinkedIn slash command
const linkedinCommand = new SlashCommandBuilder()
    .setName('linkedin')
    .setDescription('Create a LinkedIn post with Australian English formatting and Golden Threads integration');

const commands = [
    linkedinCommand.toJSON()
];

const rest = new REST({ version: '10' }).setToken(process.env.DISCORD_BOT_TOKEN);

async function registerCommands() {
    try {
        console.log('🔄 Started refreshing application (/) commands.');

        // Get client ID from bot token
        const clientId = process.env.CLIENT_ID || getClientIdFromToken(process.env.DISCORD_BOT_TOKEN);
        
        if (!clientId) {
            throw new Error('Cannot determine client ID. Set CLIENT_ID in .env or ensure DISCORD_BOT_TOKEN is valid.');
        }

        console.log(`📱 Using client ID: ${clientId}`);

        if (process.env.DISCORD_GUILD_ID) {
            // Register commands for specific guild (faster for development)
            console.log(`🏠 Registering commands for guild: ${process.env.DISCORD_GUILD_ID}`);
            await rest.put(
                Routes.applicationGuildCommands(clientId, process.env.DISCORD_GUILD_ID),
                { body: commands },
            );
            console.log('✅ Successfully registered guild-specific application commands.');
        } else {
            // Register commands globally (takes up to 1 hour to update)
            console.log('🌐 Registering commands globally (may take up to 1 hour to update)');
            await rest.put(
                Routes.applicationCommands(clientId),
                { body: commands },
            );
            console.log('✅ Successfully registered global application commands.');
        }

    } catch (error) {
        console.error('❌ Error registering commands:', error);
        console.log('\n💡 Troubleshooting:');
        console.log('1. Make sure DISCORD_BOT_TOKEN is set in .env file');
        console.log('2. Verify bot token is valid (should be ~60+ characters)');
        console.log('3. Check bot has "applications.commands" scope in Discord');
        console.log('4. Optionally set CLIENT_ID directly in .env file\n');
    }
}

// Extract client ID from bot token
function getClientIdFromToken(token) {
    if (!token || typeof token !== 'string') {
        return null;
    }
    
    try {
        // Discord bot tokens are base64 encoded with client ID as first part
        const tokenParts = token.split('.');
        if (tokenParts.length < 1) {
            return null;
        }
        
        // Decode the first part of the token to get client ID
        const clientId = Buffer.from(tokenParts[0], 'base64').toString('ascii');
        
        // Validate it's a valid snowflake (Discord ID)
        if (!/^\d{17,19}$/.test(clientId)) {
            return null;
        }
        
        return clientId;
    } catch (error) {
        console.error('Error extracting client ID from token:', error.message);
        return null;
    }
}

// Auto-run if called directly
if (require.main === module) {
    registerCommands();
}

module.exports = { registerCommands };