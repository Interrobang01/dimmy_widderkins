import { Client, GatewayIntentBits } from "discord.js";
import { readFileSync } from "fs";
import { deployCommands } from "./deploy-commands";
import { commands } from "./ts-commands";

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.DirectMessages,
    GatewayIntentBits.MessageContent
  ],
});

client.once("ready", async () => {
  console.log("Discord bot is ready! 🤖");
  
  // Deploy commands for all existing guilds
  console.log("Deploying commands to existing guilds...");
  for (const guild of client.guilds.cache.values()) {
    await deployCommands({ guildId: guild.id });
  }
  console.log("Commands deployed to all guilds!");
});

client.on("guildCreate", async (guild) => {
  await deployCommands({ guildId: guild.id });
});

client.on("interactionCreate", async (interaction) => {
  if (!interaction.isCommand()) {
    return;
  }
  
  const { commandName } = interaction;
  
  try {
    if (commands[commandName as keyof typeof commands]) {
      await commands[commandName as keyof typeof commands].execute(interaction);
    } else {
      console.log(`Unknown command: ${commandName}`);
    }
  } catch (error) {
    console.error(`Error executing command ${commandName}:`, error);
    
    const errorMessage = "There was an error executing this command!";
    if (interaction.replied || interaction.deferred) {
      await interaction.followUp({ content: errorMessage, ephemeral: true });
    } else {
      await interaction.reply({ content: errorMessage, ephemeral: true });
    }
  }
});

client.login(readFileSync('/home/interrobang/VALUABLE/dimmy_widderkins_token.txt', 'utf-8').trim());
