import express from 'express';
import { Client, TextChannel, GatewayIntentBits } from 'discord.js';
import { Brook } from './brook';

const app = express();
app.use(express.json());

let brookInstance: Brook | null = null;
let discordClient: Client | null = null;

// Initialize Discord client and Brook instance
async function initializeBot(token: string, transportChannelId: string) {
    discordClient = new Client({
        intents: [
            GatewayIntentBits.Guilds,
            GatewayIntentBits.GuildMessages,
            GatewayIntentBits.MessageContent,
        ],
    });

    await discordClient.login(token);
    
    const transportChannel = await discordClient.channels.fetch(transportChannelId) as TextChannel;
    brookInstance = new Brook(transportChannel, discordClient);
    
    console.log('Brook server initialized and ready!');
}

// Add health check endpoint
app.get('/health', (req, res) => {
    res.json({ 
        success: true, 
        status: 'running',
        initialized: brookInstance !== null 
    });
});

// Initialize endpoint
app.post('/init', async (req, res) => {
    const { token, transportChannelId } = req.body;
    await initializeBot(token, transportChannelId);
    res.json({ success: true, message: 'Brook server initialized' });
});

// Request payment endpoint
app.post('/request-payment', async (req, res) => {
    console.log('Received payment request:', req.body);
    if (!brookInstance || !discordClient) {
        return res.status(400).json({ success: false, error: 'Brook not initialized' });
    }

    const { userId, amount, requestChannelId, description } = req.body;
    
    // Validate required fields
    if (!userId || userId === 'null' || userId === null) {
        return res.status(400).json({ success: false, error: 'Invalid or missing user ID' });
    }
    
    if (!amount || amount <= 0) {
        return res.status(400).json({ success: false, error: 'Invalid amount' });
    }
    
    if (!requestChannelId) {
        return res.status(400).json({ success: false, error: 'Missing request channel ID' });
    }
    
    console.log(`Processing payment request: userId=${userId}, amount=${amount}, channelId=${requestChannelId}`);
    
    const user = await discordClient.users.fetch(userId);
    const requestChannel = await discordClient.channels.fetch(requestChannelId);
    
    if (!requestChannel) {
        return res.status(400).json({ success: false, error: 'Request channel not found' });
    }
    
    const result = await brookInstance.requestPayment(user, amount, requestChannel, description);
    res.json({ success: true, data: result });
    
});

// Pay endpoint
app.post('/pay', async (req, res) => {
    if (!brookInstance) {
        return res.status(400).json({ success: false, error: 'Brook not initialized' });
    }

    const { target, amount } = req.body;
    const result = await brookInstance.pay(target, amount);
    res.json({ success: true, data: result });
});

// Balance endpoint
app.get('/balance/:target', async (req, res) => {
    if (!brookInstance) {
        return res.status(400).json({ success: false, error: 'Brook not initialized' });
    }

    const { target } = req.params;
    const balance = await brookInstance.balance(target);
    res.json({ success: true, data: balance });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Brook server running on port ${PORT}`);
    console.log('Server is ready to accept connections');
});
