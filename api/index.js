import { Analytics } from "@vercel/analytics/react"
const { Client, GatewayIntentBits } = require('discord.js');
const { config } = require('dotenv');

config(); // Load environment variables from .env file

const client = new Client({
    intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent],
});

client.once('ready', () => {
    console.log(`Logged in as ${client.user.tag}`);
});

client.on('messageCreate', (message) => {
    if (message.content === '!ping') {
        message.channel.send('Pong!');
    }
});

// Vercel serverless function
module.exports = (req, res) => {
    if (req.method === 'POST') {
        // Handle incoming requests (e.g., from Discord)
        res.status(200).send('Bot is running');
    } else {
        res.status(405).send('Method Not Allowed');
    }
};

client.login(process.env.DISCORD_BOT_TOKEN);
